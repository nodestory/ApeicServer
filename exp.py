import itertools
import operator
from collections import Counter
from termcolor import colored
from apeic.apeic_db_manager import ApeicDBHelper
from predictor.preprocessor import Preprocessor
from predictor.mfu_predictor import MFUPredictor
from sklearn.naive_bayes import MultinomialNB, BernoulliNB 
from sklearn.naive_bayes import GaussianNB

from sklearn import tree


def split(sessions, ratio=0.8):
	split_index = int(len(sessions)*ratio)
	return sessions[:split_index], sessions[split_index:]


import sys
if __name__ == '__main__':
	db_helper = ApeicDBHelper()
	users = db_helper.get_users()
	for user in users:
		print colored(user, attrs=['blink']),

		sessions = db_helper.get_sessions(user)
		sessions = map(lambda x: x[:1], sessions)
		if len(sessions) == 0:
			print
			continue

		preprocessor = Preprocessor()
		logs = preprocessor.aggregate_sessions(sessions)
		used_apps = Counter(map(lambda x: x['application'], logs))
		X, y = preprocessor.to_sklearn(logs)
		
		training_X, tesiting_X = split(X, 0.8)
		training_y, tesiting_y = split(y, 0.8)

		# nb = GaussianNB()
		nb = MultinomialNB()
		# nb = BernoulliNB()
		predictor = nb.fit(training_X, training_y)

		# clf = tree.DecisionTreeClassifier()
		# predictor = clf.fit(training_X, training_y)

		count = 0
		for i in xrange(len(tesiting_X)):
			ranking = sorted(zip(predictor.classes_, predictor.predict_proba(tesiting_X[i])[0]), \
				key=operator.itemgetter(1), reverse=True)
			candidates = map(lambda x: x[0], filter(lambda x: x[1] > 0.2, ranking))
			for c in candidates:
				del used_apps[c]
			# if tesiting_y[i] in candidates + used_apps.most_common(4 - len(candidates)):
			if tesiting_y[i] in map(lambda x: x[0], ranking[:4]):
				count += 1
		print count/float(len(tesiting_X))


		# sessions = db_helper.get_sessions(user)
		# training_sessions, testing_sessions = split(sessions, 0.8)
		# predictor = MFUPredictor()
		# predictor.train(list(itertools.chain(*training_sessions)))
		# acc = predictor.test(list(itertools.chain(*testing_sessions)), 4)
		# print acc
		# break