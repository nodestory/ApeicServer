import itertools
import operator
from collections import Counter
from termcolor import colored
from apeic.apeic_db_manager import ApeicDBHelper
from predictor.preprocessor import Preprocessor
from predictor.mfu_predictor import MFUPredictor
from sklearn.naive_bayes import MultinomialNB, BernoulliNB 
from sklearn.naive_bayes import GaussianNB
from sklearn.feature_extraction import DictVectorizer
from sklearn import tree


def split(sessions, ratio=0.8):
	split_index = int(len(sessions)*ratio)
	return sessions[:split_index], sessions[split_index:]


import sys
if __name__ == '__main__':
	db_helper = ApeicDBHelper()
	users = db_helper.get_users()

	accuracies = []
	for user in users:
		print colored(user, attrs=['blink'])

		sessions = db_helper.get_sessions(user)
		training_sessions, testing_sessions = split(sessions, 0.8)
		preprocessor = Preprocessor([])

		start = 0
		tesiting_sessions = filter(lambda x: len(x) > start, testing_sessions)
		logs = preprocessor.aggregate_sessions(\
			training_sessions + \
			map(lambda x: [x[start]], tesiting_sessions))
		l = len(logs) - len(tesiting_sessions)
		X, y = preprocessor.to_sklearn(logs)
		
		training_X, testing_X = X[:l], X[l:]
		training_y, testing_y = y[:l], y[l:]
		if len(testing_X) == 0:
			continue

		nb = MultinomialNB()
		predictor = nb.fit(training_X, training_y)

		count = 0
		for i in xrange(len(testing_X)):
			ranking = sorted(zip(predictor.classes_, predictor.predict_proba(testing_X[i])[0]), \
				key=operator.itemgetter(1), reverse=True)
			if testing_y[i] in map(lambda x: x[0], ranking[:4]):
				count += 1

		# print count/float(len(testing_X))

		print count/float(len(testing_X))
		accuracies.append(count/float(len(testing_X)))
		# break
		
	print sum(accuracies)/len(accuracies)