import datetime
import itertools
import operator
from collections import Counter, OrderedDict, defaultdict
from itertools import chain
from termcolor import colored
from operator import itemgetter

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
		self.hahaha = []
		self.ohohoh = []

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

		for pkg_name in self.app_instances:
			instance = self.app_instances[pkg_name]
			instance.crf = (1 if pkg_name in set(launched_apps) else 0.3) + 0.8*instance.crf

		if len(session) > 1:
			# """
			for predecessor in list(OrderedDict.fromkeys(launched_apps)):
				successors = []
				indices = [i for i, x in enumerate(launched_apps) if x == predecessor] + [len(session)]
				for i in xrange(len(indices) - 1):
					# successors = set(map(lambda j: session[j]['application'], \
					# 					xrange(indices[i] + 1, indices[i+1] + 1 \
					# 						if indices[i+1] != len(session) else indices[i+1])))
					successors = set(map(lambda j: session[j]['application'], \
										xrange(indices[i] + 1, indices[i+1])))
					instance = self.app_instances.setdefault(predecessor, AppInstance(predecessor))
					instance.ocrs += 1.0
					for successor in list(successors):
						instance = self.app_instances.setdefault(successor, AppInstance(successor))
						# instance.pred_co_ocrs[predecessor] += instance.crf
						instance.pred_co_ocrs[predecessor] += 1.0
			# """

			"""
			for name in launched_apps:
				instance = self.app_instances.setdefault(name, AppInstance(name))
				instance.ocrs += 1.0

			for predecessor in list(OrderedDict.fromkeys(launched_apps)):
				successors = []
				indices = [i for i, x in enumerate(launched_apps) if x == predecessor] + [len(session)]
				for i in xrange(len(indices) - 1):
					for j in xrange(indices[i] + 1, indices[i+1]):
						successor = session[j]['application']
						if successor not in successors:		
							instance = self.app_instances.setdefault(successor, AppInstance(successor))
							# instance.pred_co_ocrs[predecessor] += self.app_instances.setdefault(predecessor, AppInstance(predecessor)).crf
							instance.pred_co_ocrs[predecessor] += 1.0
							successors.append(successor)
					instance = self.app_instances.setdefault(predecessor, AppInstance(predecessor))
					instance.pred_co_ocrs[predecessor] += self.app_instances.setdefault(predecessor, AppInstance(predecessor)).crf
					instance.pred_co_ocrs[predecessor] += 1.0
			"""

			"""
			for name in launched_apps:
				instance = self.app_instances.setdefault(name, AppInstance(name))
				instance.ocrs += 1.0

			for i in xrange(1, len(session)):
				successor = session[i]['application']
				app = self.app_instances.setdefault(successor, AppInstance(successor))
				app.pred_co_ocrs[session[i-1]['application']] += 1.0
			"""

		for pkg_name in self.app_instances:
			successor = self.app_instances[pkg_name]
			N = float(sum(map(lambda x: successor.pred_co_ocrs[x], self.app_instances)))
			for p in successor.pred_co_ocrs:
				n = successor.pred_co_ocrs[p]
				predecessor = self.app_instances[p]
				successor.pred_influence[p] = successor.pred_co_ocrs[p]/predecessor.ocrs
				# successor.pred_influence[p] = successor.crf*successor.pred_co_ocrs[p]/predecessor.ocrs

				# if n == 0:
				# 	successor.pred_influence[p] = 0
				# else:
				# 	successor.pred_influence[p] = n/predecessor.ocrs

	def predict(self, session, last_app, terminator, k=4):
		env_context = session[-1]
		instance = self.feature_extractor.transform(last_app, env_context)
		result = dict(zip(self.nb_predictor.classes_, self.nb_predictor.predict_proba(instance)[0]), \
						key=operator.itemgetter(1), reverse=True)

		ranking = defaultdict(int)
		for pkg_name in self.app_instances:
			ranking[pkg_name] = result[pkg_name] if pkg_name in result else 0

		nb_candidates = sorted(ranking, key=ranking.get, reverse=True)

		int_context = map(lambda x: x['application'], session[:-1])
		for app in set(int_context):
			for pkg_name in self.app_instances:
				instance = self.app_instances.setdefault(pkg_name, AppInstance(pkg_name))
				ranking[pkg_name] += self.app_instances[pkg_name].pred_influence[app]/len(int_context)
				# ranking[pkg_name] += self.app_instances[pkg_name].pred_influence[app]
				# ranking[pkg_name] = self.app_instances[pkg_name].pred_influence[app]
			
		# print '\n'.join(int_context)
		N = float(len(int_context))
		for app in set(int_context[:-1]):
			n = int_context.count(app)
			l_index = (x for x in reversed([y for y in enumerate(int_context)]) if x[1] == app).next()[0]
			# lamb = N/n + 0.5
			lamb = (N - l_index)/n
			x = int(N - l_index)
			prob = (lamb**x)*math.exp(-lamb)/math.factorial(x)
			# print lamb, x, app, prob
			ranking[app] += prob
			# ranking[app] += 1
		# print


		# for pkg_name in self.app_instances:
		# 	instance = self.app_instances[pkg_name]
		# 	instance.crf = (1 if pkg_name in set(launched_apps) else 0.3) + 0.8*instance.crf

		# for pkg_name in self.app_instances:
		# 	instance = self.app_instances.setdefault(pkg_name, AppInstance(pkg_name))
		# 	ranking[pkg_name] *= instance.crf


		apeic_candidates = sorted(ranking, key=ranking.get, reverse=True)
		if len(int_context) == 0:
			apeic_candidates = [terminator] + filter(lambda x: x!= terminator, apeic_candidates)
		else:
			if int_context[-1] in apeic_candidates:
				apeic_candidates.remove(int_context[-1])

		# self.logs += session
		# X, y = self.feature_extractor.generate_training_instances(self.logs)
		# nb = MultinomialNB()
		# self.nb_predictor = nb.fit(X, y)

		return apeic_candidates[:k], nb_candidates[:k]

def split(sessions, passed_days=7, ratio=0.8):
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
	end_date = start_date + datetime.timedelta(days=6)
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
	initial_misses = 0.0
	
	nb_total_hits = 0.0
	nb_total_misses = 0.0
	nb_m = 0.0

	mfu_total_hits = 0.0
	mfu_total_misses = 0.0
	mfu_m = 0.0
	for user in users:
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
		# initial_misses = 0.0
		unseen_misses = 0.0

		starter = ''
		terminator = ''
		last_app = ''
		last_date = ''

		# ss = 1
		for session in testing_sessions:
			"""
			if last_date != session[0]['datetime'].day and last_date != '':
				if hits + misses > 0:
					print ss, hits/(hits + misses)
				else:
					pass
					print 'zero'
				# hits = 0.0
				# misses = 0.0
				ss += 1
				# if ss == 7:
				# 	sys.exit()
			"""
			
			# print '==='
			# if len(session) > 0:
			# 	print '\n'.join(map(lambda x: x['application'], session))
			# 	print

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
					if session[i]['application'] not in counter.keys() and i == 0:
						# print session[i]['application']
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
			last_date = session[0]['datetime'].day

			predictor.update(session)

		if hits + misses == 0:
			continue
		acc = (hits)/(hits + misses)
		# print unseen_misses
		print acc, hits, misses, initial_misses, unseen_misses

	print k
	print colored('APEIC', 'cyan'), \
			(total_hits)/(total_hits + total_misses), m/(total_hits + total_misses), initial_misses, total_hits, total_misses
	print colored('NB   ', 'cyan'), \
			(nb_total_hits)/(nb_total_hits + nb_total_misses), nb_m/(nb_total_hits + nb_total_misses)
	print colored('MFU  ', 'cyan'), \
			(mfu_total_hits)/(mfu_total_hits + mfu_total_misses), mfu_m/(mfu_total_hits + mfu_total_misses)

if __name__ == '__main__':
	# for k in xrange(1, 9):
	# 	test(k, True)
	test(4, True)
