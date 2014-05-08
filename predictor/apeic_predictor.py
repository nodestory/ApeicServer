import datetime
import itertools
import operator
from collections import Counter, OrderedDict, defaultdict
from itertools import chain
from termcolor import colored

# TODO
import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper
from nb_predictor import *

class AppInstance():
	def __init__(self, pkg_name):
		self.pkg_name = pkg_name
		self.ocrs = 0
		self.pred_co_ocrs = defaultdict(int)
		self.pred_influence = defaultdict(int)

		self.crf = 0

class ApeicPredictor():

	def __init__(self):
		self.feature_extractor = FeatureExtractor()
		self.app_instances = {}

	def train(self, sessions):
		# environmental context
		logs = list(chain(*sessions))
		X, y = self.feature_extractor.generate_training_instances(logs)
		nb = MultinomialNB()
		self.nb_predictor = nb.fit(X, y)

		# interactional context
		for session in sessions:
			self.update(session)

	def update(self, session):
		launched_apps = map(lambda x: x['application'], session)
		for name in launched_apps:
			instance = self.app_instances.setdefault(name, AppInstance(name))
			instance.ocrs += 1.0

		for pkg_name in self.app_instances:
			instance = self.app_instances[pkg_name]
			instance.crf = (1 if pkg_name in set(launched_apps) else 0) + 0.5*instance.crf

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
							instance.pred_co_ocrs[predecessor] += self.app_instances.setdefault(predecessor, AppInstance(predecessor)).crf
							instance.pred_co_ocrs[predecessor] += 1.0
							successors.append(successor)
					instance = self.app_instances.setdefault(predecessor, AppInstance(predecessor))
					instance.pred_co_ocrs[predecessor] += self.app_instances.setdefault(predecessor, AppInstance(predecessor)).crf
					instance.pred_co_ocrs[predecessor] += 1.0
			# """

			"""
			for p in list(OrderedDict.fromkeys(launched_apps))[:-1]:
				for s in list(OrderedDict.fromkeys(launched_apps))[1:]:
					instance = self.app_instances.setdefault(s, AppInstance(s))
					instance.pred_co_ocrs[p] += 1.0
			"""

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

	def predict(self, session, last_app, terminator, k=4):
		env_context = session[-1]
		instance = self.feature_extractor.transform(last_app, env_context)
		result = dict(zip(self.nb_predictor.classes_, self.nb_predictor.predict_proba(instance)[0]), \
						key=operator.itemgetter(1), reverse=True)

		ranking = defaultdict(int)
		test = {}
		for pkg_name in self.app_instances:
			ranking[pkg_name] = result[pkg_name] if pkg_name in result else 0
			test[pkg_name] = self.app_instances.setdefault(pkg_name, AppInstance(pkg_name)).crf

		nb_candidates = sorted(ranking, key=ranking.get, reverse=True)

		int_context = map(lambda x: x['application'], session[:-1])
		for app in int_context:
			for pkg_name in self.app_instances:
				instance = self.app_instances.setdefault(pkg_name, AppInstance(pkg_name))
				ranking[pkg_name] += self.app_instances[pkg_name].pred_influence[app]	

		apeic_candidates = sorted(ranking, key=ranking.get, reverse=True)
		if len(int_context) == 0:
			apeic_candidates = [terminator] + filter(lambda x: x!= terminator, apeic_candidates)
		else:
			if int_context[-1] in apeic_candidates:
				apeic_candidates.remove(int_context[-1])
		return apeic_candidates[:k], nb_candidates[:k]

def split(sessions, ratio=0.8):
	# print (sessions[-1][-1]['datetime'] - sessions[0][0]['datetime']).days
	start_date = sessions[0][0]['datetime']
	midnight = datetime.time(0)
	start_date = datetime.datetime.combine(start_date.date(), midnight)
	end_date = start_date + datetime.timedelta(days=7)

	split_index = int(len(sessions)*ratio)
	for i in xrange(len(sessions)):
		if (sessions[i][0]['datetime'] - end_date).days > 0:
			split_index = i
			break

	test_sessions = sessions[split_index:]
	start_date = test_sessions[0][0]['datetime']
	midnight = datetime.time(0)
	start_date = datetime.datetime.combine(start_date.date(), midnight)
	end_date = start_date + datetime.timedelta(days=7)
	tt = -1
	for i in xrange(len(test_sessions)):
		if (test_sessions[i][0]['datetime'] - end_date).days > 0:
			tt = i
			break
	if tt != -1:
		test_sessions = test_sessions[:tt]

	# print split_index, len(sessions) - split_index
	return sessions[:split_index], sessions[split_index:]
	return sessions[:split_index], test_sessions

def test(k=4, ignore_initiator=True):
	db_helper = ApeicDBHelper()
	users = filter(lambda x: x != '11d1ef9f845ec10e', db_helper.get_users())

	total_hits = 0.0
	total_misses = 0.0
	m = 0.0
	
	nb_total_hits = 0.0
	nb_total_misses = 0.0
	nb_m = 0.0

	mfu_total_hits = 0.0
	mfu_total_misses = 0.0
	mfu_m = 0.0
	for user in users[:1]:
		# print colored(user, attrs=['blink'])

		sessions = db_helper.get_sessions(user)
		training_sessions, testing_sessions = split(sessions, 0.8)

		used_apps = []
		for session in training_sessions:
			used_apps += map(lambda x: x['application'], session)
			counter = Counter(used_apps)
		mfu_candidates = map(lambda x: x[0], counter.most_common(k))

		predictor = ApeicPredictor()
		predictor.train(training_sessions)

		hits = 0.0
		misses = 0.0
		initial_misses = 0.0
		unseen_misses = 0.0

		starter = ''
		terminator = ''
		last_app = ''
		for session in testing_sessions:
			# if len(session) > 1:
				# print '==='
				# print '\n'.join(map(lambda x: x['application'], session))

			for i in xrange(len(session)):
				if ignore_initiator and i == 0:
					continue

				apeic_candidates, nb_candidates = predictor.predict(session[:i+1], last_app, terminator, k)
				assert len(apeic_candidates) <= k and len(nb_candidates) <= k

				if session[i]['application'] in apeic_candidates:
					total_hits += 1.0
					hits += 1.0
					m += 1.0/(apeic_candidates.index(session[i]['application']) + 1)
				else:
					total_misses += 1.0
					# print i, session[i]['application']
					# print '\t', apeic_candidates
					misses += 1.0
					if i == 0:
						initial_misses += 1.0
					if session[i]['application'] not in counter.keys() and i > 0:
						unseen_misses += 1.0

				if session[i]['application'] in nb_candidates:
					nb_total_hits += 1.0
					nb_m += 1.0/(nb_candidates.index(session[i]['application']) + 1)
				else:
					nb_total_misses += 1.0

				if session[i]['application'] in mfu_candidates:
					mfu_total_hits += 1.0
					mfu_m += 1.0/(mfu_candidates.index(session[i]['application']) + 1)
				else:
					mfu_total_misses += 1.0

				last_app = session[i]['application'] 
			starter = session[0]['application']
			terminator = session[-1]['application']

			predictor.update(session)

		if hits + misses == 0:
			continue
		acc = (hits)/(hits + misses)
		# print acc, hits, misses, initial_misses, unseen_misses

	print k
	print colored('APEIC', 'cyan'), \
			(total_hits)/(total_hits + total_misses), m/(total_hits + total_misses)
	print colored('NB   ', 'cyan'), \
			(nb_total_hits)/(nb_total_hits + nb_total_misses), nb_m/(nb_total_hits + nb_total_misses)
	print colored('MFU  ', 'cyan'), \
			(mfu_total_hits)/(mfu_total_hits + mfu_total_misses), mfu_m/(mfu_total_hits + mfu_total_misses)

if __name__ == '__main__':
	for k in xrange(1, 9):
		test(k, True)
