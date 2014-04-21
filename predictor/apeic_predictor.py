import datetime
import itertools
import operator
from collections import Counter, OrderedDict, defaultdict
from itertools import chain
from termcolor import colored
from preprocessor import Preprocessor
from predictor import Predictor
from nb_predictor import *

class AppInstance():
	def __init__(self, pkg_name):
		self.pkg_name = pkg_name
		self.ocrs = 0
		self.pred_co_ocrs = defaultdict(int)
		self.pred_influence = defaultdict(int)

class ApeicPredictor(Predictor):

	def __init__(self):
		self.feature_extractor = FeatureExtractor()
		self.app_instances = {}

	def train(self, sessions):
		# TODO: refactor by using nb_predictor
		logs = list(chain(*sessions))
		X, y = self.feature_extractor.generate_training_instances(logs)
		nb = MultinomialNB()
		self.nb_predictor = nb.fit(X, y)

		for session in sessions:
			self.update(session)

	def update(self, session):					
		launched_apps = map(lambda x: x['application'], session)
		for name in launched_apps:
			instance = self.app_instances.setdefault(name, AppInstance(name))
			instance.ocrs += 1.0

		if len(session) > 1:
			# """
			for predecessor in list(OrderedDict.fromkeys(launched_apps)):
				successors = []
				indices = [i for i, x in enumerate(launched_apps) if x == predecessor]
				indices.append(len(session))
				for i in xrange(len(indices) - 1):
					for j in xrange(indices[i] + 1, indices[i+1]):
						successor = session[j]['application']
						if successor not in successors:
							instance = self.app_instances.setdefault(successor, AppInstance(successor))
							instance.pred_co_ocrs[predecessor] += 1.0
							successors.append(successor)
					instance = self.app_instances.setdefault(predecessor, AppInstance(predecessor))
					instance.pred_co_ocrs[predecessor] += 1.0
			# """

			"""
			for i in xrange(1, len(session)):
				successor = session[i]['application']
				app = self.app_instances.setdefault(successor, AppInstance(successor))
				app.pred_co_ocrs[session[i-1]['application']] += 1.0
			"""

		for pkg_name in self.app_instances:
			successor = self.app_instances[pkg_name]
			for p in successor.pred_co_ocrs:
				predecessor = self.app_instances[p]
				successor.pred_influence[p] = successor.pred_co_ocrs[p]/predecessor.ocrs

	def predict(self, starter, terminator, session, k=4):
		env_context = session[-1]
		instance = self.feature_extractor.transform('', env_context)
		result = dict(zip(self.nb_predictor.classes_, self.nb_predictor.predict_proba(instance)[0]), \
						key=operator.itemgetter(1), reverse=True)

		ranking = defaultdict(int)
		for pkg_name in self.app_instances:
			ranking[pkg_name] = result[pkg_name] if pkg_name in result else 0
		int_context = map(lambda x: x['application'], session[:-1])
		temp = []
		for a in int_context:
			if a not in self.app_instances:
				temp.append(a)
			else:
				for pkg_name in self.app_instances:
					ranking[pkg_name] += self.app_instances[pkg_name].pred_influence[a]

		candidates = sorted(ranking, key=ranking.get, reverse=True)
		if len(int_context) == 0:
			if terminator not in candidates[:k] and terminator != '':
				candidates.insert(0, terminator)
			# if starter not in candidates[:k+1] and starter != '':
			# 	candidates.insert(0, starter)
		else:
			if int_context[-1] in candidates:
				candidates.remove(int_context[-1])
		return candidates[:k]

		"""
		if len(session) == 0:
			results = sorted(ei.iteritems(), key=operator.itemgetter(1), reverse=True)
			candidates = map(lambda x: x[0], results[2:k+2])
			if last not in candidates:
				candidates = map(lambda x: x[0], results[2:k+1]) + [last]
			return candidates

		launched_apps = list(OrderedDict.fromkeys(map(lambda x: x['application'], session[:-1])))
		ranking = defaultdict(int)
		for pkg_name in self.app_instances:
			# ranking[pkg_name] = ei[pkg_name] if pkg_name in ei else 0
			ranking[pkg_name] = self.app_instances[pkg_name].pred_influence[session[-1]['application']]
			# ranking[pkg_name] = self.app_instances[pkg_name].pred_influence[session[-1]['application']] \
			# 						+ ei[pkg_name] if pkg_name in ei.keys() else 0

			# TODO: take recency into consideration
			# if pkg_name in map(lambda x: x['application'], session[-4:-1]):
			# 	ranking[pkg_name] += 1
			# if pkg_name in map(lambda x: x['application'], session[:-4]):
			# 	ranking[pkg_name] -= 1
			# if pkg_name in launched_apps:
				# ranking[pkg_name] += 0.3 - 0.05*(len(launched_apps) - temp.index(pkg_name))
		"""

def split(sessions, ratio=0.8):
	# print (sessions[-1][-1]['datetime'] - sessions[0][0]['datetime']).days
	start_date = sessions[0][0]['datetime']
	midnight = datetime.time(0)
	start_date = datetime.datetime.combine(start_date.date(), midnight)
	end_date = start_date + datetime.timedelta(days=21)

	split_index = int(len(sessions)*ratio)
	# for i in xrange(len(sessions)):
	# 	if (sessions[i][0]['datetime'] - end_date).days > 0:
	# 		split_index = i
	# 		break
	
	# print split_index, len(sessions) - split_index
	return sessions[:split_index], sessions[split_index:]

import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper
def main():
	db_helper = ApeicDBHelper()
	users = db_helper.get_users()

	total_hits = 0.0
	total_misses = 0.0
	accuracies = []
	# users = ['7fab9970aff53ef4']
	for user in users:
		if user == '11d1ef9f845ec10e':
			continue
		print colored(user, attrs=['blink'])

		sessions = db_helper.get_sessions(user)
		training_sessions, testing_sessions = split(sessions, 0.8)
		seen_apps = []
		for s in training_sessions:
			seen_apps.extend(map(lambda x: x['application'], s))
		print len(set(seen_apps)), len(sessions)
		# training_sessions = map(lambda x: [x[0]], training_sessions)
		predictor = ApeicPredictor()
		predictor.train(training_sessions)

		hits = 0.0
		misses = 0.0
		initial_misses = 0.0
		unseen_misses = 0.0

		starter = ''
		terminator = ''
		for session in testing_sessions:
			# print '\n'.join(map(lambda x: x['application'], session))
			for i in xrange(len(session)):
				candidates = predictor.predict(starter, terminator, session[:i+1], 4)
				assert len(candidates) == 4

				# if session[i]['application'] not in candidates:
				# 	print i, session[i]['application']
				# 	print candidates
				# print

				if session[i]['application'] in candidates:
					total_hits += 1.0
					hits += 1.0
				else:
					total_misses += 1.0
					misses += 1.0
					if i == 0:
						initial_misses += 1.0
					if session[i]['application'] not in seen_apps:
						unseen_misses += 1.0
			starter = session[0]['application']
			terminator = session[-1]['application']

			# predictor.update(session)

			# logs = aggregate_sessions(training_sessions + [session])
			# extractor = FeatureExtractor()
			# X, y = extractor.generate_training_instances(logs)
			# nb = MultinomialNB()
			# nb_predictor = nb.fit(X, y)

		if hits + misses == 0:
			continue
		acc = (hits)/(hits + misses)
		print acc, hits, misses, initial_misses, unseen_misses
		# break
	print (total_hits)/(total_hits + total_misses)

if __name__ == '__main__':
	main()
