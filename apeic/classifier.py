import itertools
import logging
import math
import operator
from collections import defaultdict, Counter, OrderedDict
from termcolor import colored
from apeic_db_manager import ApeicDBHelper
import sys
sys.path.append('/home/linzy/Projects/ApeicServer/predictor')
from mfu_predictor import MFUPredictor
from sklearn.naive_bayes import MultinomialNB
from preprocessor import Preprocessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class App():
	def __init__(self, pkg_name):
		self.name = pkg_name
		self.ocrs = 0
		self.pred_co_ocrs = defaultdict(int)
		self.pred_influence = defaultdict(int)
		self.repeatedness = 0

def split(sessions, ratio=0.8):
	split_index = int(len(sessions)*ratio)
	return sessions[:split_index], sessions[split_index:]

def train_1(sessions):
	installed_apps = {}
	for session in sessions:
		for x in session:
			app = installed_apps.setdefault(x['application'], App(x['application']))
			app.ocrs += 1.0

		if len(session) > 1:
			app_pkg_names = [x['application'] for x in session]
			for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
				successors = []
				indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]
				indices.append(len(session))
				for i in xrange(len(indices) - 1):
					for j in xrange(indices[i] + 1, indices[i+1]):
						successor = session[j]['application']
						if successor not in successors:
							app = installed_apps.setdefault(successor, App(successor))
							app.pred_co_ocrs[predecessor] += 1.0
							successors.append(successor)

	for pkg_name in installed_apps:
		successor = installed_apps[pkg_name]
		for p in successor.pred_co_ocrs:
			predecessor = installed_apps[p]
			successor.pred_influence[p] = compute_relatedness(
				successor.pred_co_ocrs[p], predecessor.ocrs, successor.ocrs, len(sessions), 5)
	return installed_apps

def train_2(sessions):
	installed_apps = {}
	for session in sessions:
		for x in [x['application'] for x in session]:
			app = installed_apps.setdefault(x, App(x))
			app.ocrs += 1

		if len(session) > 1:
			app_pkg_names = [x['application'] for x in session]
			for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
				index = app_pkg_names.index(predecessor)
				for i in xrange(index + 1, len(session)):
					successor = app_pkg_names[i]
					app = installed_apps.setdefault(successor, App(successor))
					app.pred_co_ocrs[predecessor] += 1.0

	for pkg_name in installed_apps:
		successor = installed_apps[pkg_name]
		for p in successor.pred_co_ocrs:
			predecessor = installed_apps[p]
			successor.pred_influence[p] = compute_relatedness(
				successor.pred_co_ocrs[p], predecessor.ocrs, successor.ocrs, len(sessions), 5)

	results = defaultdict(list)
	for session in sessions:
		apps = [x['application'] for x in session]
		counts = Counter(apps)
		for app in counts:
			results[app].append(counts[app])

	return installed_apps


def print_causality(installed_apps):
	for p in installed_apps:
		print installed_apps[p].name
		ranking = [(s, installed_apps[s].pred_influence[p]) \
			for s in installed_apps]
		ranking = sorted(ranking, key=operator.itemgetter(1), reverse=True)
		ranking = filter(lambda x: x[1] != -1, ranking)
		for successor, intensity in ranking:
			print ("%2.4f" % intensity).rjust(7), successor
		print 

def compute_relatedness(co_ocrs, p_ocrs, s_ocrs, N, typ=1):
	N = float(N)
	co_prob = co_ocrs/N
	p_prob = p_ocrs/N
	s_prob = s_ocrs/N
	if typ == 1:
		return co_prob/(p_prob*s_prob)
	elif typ == 2:
		return math.log(co_prob/(p_prob*s_prob))
	elif typ == 3:
		return math.log(co_prob/(p_prob*s_prob))/(-math.log(co_prob))
	elif typ == 4: #idf
		return math.log(N/p_ocrs)*math.log(co_prob/(p_prob*s_prob))/(-math.log(co_prob))
	elif typ == 5:
		return co_ocrs/float(p_ocrs)
	elif typ == 6:
		return math.log(p_ocrs)*co_ocrs/p_ocrs
	else:
		pass

def test(sessions, installed_apps, counter):
	count = 0
	base = 0.0
	error = defaultdict(int)
	for session in sessions:
		if len(session) == 1:
			# if session[0]['application'] in [ u'com.android.systemui', u'com.htc.launcher', u'android', \
			# 	u'com.tul.aviate', u'com.android.settings']:
			# 	continue
			# if session[0]['application'] in [x[0] for x in counter.most_common(4)]:
			# 	count += 1
			# else:
			# 	error[session[0]['application']] += 1
			# base+=1

			continue
					
		used = []
		results = defaultdict(int)
		# used.append(session[0]['application'])
		for i in xrange(1, len(session)):
			if session[i]['application'] in [ u'com.android.systemui', u'com.htc.launcher', u'android', \
				u'com.tul.aviate', u'com.android.settings']:
				continue
			# used.append(session[0]['application'])
			for app in installed_apps:
				results[app] = installed_apps[app].pred_influence[session[i-1]['application']]
				# if app in used[-3:]:
				# 	results[app] += 1
				# else:
				# 	results[app] += installed_apps[app].pred_influence[session[i-1]['application']]
			predicted_apps = sorted(results.iteritems(), key=operator.itemgetter(1), reverse=True)
			# print max(map(lambda x: x[1], predicted_apps))
			# predicted_apps = filter(lambda x: x[1] > 0.1, predicted_apps)
			# print len(predicted_apps)
			# others = []
			# if len(predicted_apps) < 4:
			# 	for c in counter.most_common(100):
			# 		if len(others) == 4-len(predicted_apps):
			# 			break
			# 		if c not in [x[0] for x in predicted_apps[:4]]:
			# 			others.append(c[0])

			# print len(others)
			# if session[i]['application'] in [x[0] for x in predicted_apps[:4]] or session[i]['application'] not in installed_apps:
			# print used
			# print used[-2:]
			if session[i]['application'] in [x[0] for x in predicted_apps[:4]]:
			# if session[i]['application'] in [x[0] for x in counter.most_common(4)]:
				count += 1
			else:
				# print session[i]['application'] in used
				# print sessions.index(session), i
				# print '\n'.join(map(lambda x: x['application'], session))
				error[session[i]['application']] += 1
			base += 1
			used.append(session[i]['application'])



		# for x in session:
		# 	app = installed_apps.setdefault(x['application'], App(x['application']))
		# 	app.ocrs += 1

		# if len(session) > 1:
		# 	app_pkg_names = [x['application'] for x in session]
		# 	for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
		# 		successors = []
		# 		indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]
		# 		indices.append(len(session))
		# 		for i in xrange(len(indices) - 1):
		# 			for j in xrange(indices[i] + 1, indices[i+1]):
		# 				successor = session[j]['application']
		# 				if successor not in successors:
		# 					app = installed_apps.setdefault(successor, App(successor))
		# 					app.pred_co_ocrs[predecessor] += 1
		# 					successors.append(successor)

		# for pkg_name in installed_apps:
		# 	successor = installed_apps[pkg_name]
		# 	for p in successor.pred_co_ocrs:
		# 		predecessor = installed_apps[p]
		# 		successor.pred_influence[p] = compute_relatedness(
		# 			successor.pred_co_ocrs[p], predecessor.ocrs, successor.ocrs, len(sessions), 5)
		# print count/base
	# print error
	print count/base, count, base
	return count/base



def main():
	db_helper = ApeicDBHelper()
	users = db_helper.get_users()
	accs = []
	mfu_accs = []
	for user in users:
		sessions = db_helper.get_sessions(user)
		if len(sessions) < 20:
			continue
		else:
			print colored(user, attrs=['blink']),			
		training_sessions, testing_sessions = split(sessions, 0.84)
		counter = Counter(map(lambda x: x['application'], list(itertools.chain(*training_sessions))))
		# counter = Counter(map(lambda x: x['application'], map(lambda x: x[0], training_sessions)))

		# installed_apps = train(training_sessions)
		installed_apps = train_1(training_sessions)
		# installed_apps = train_2(training_sessions)
		acc = test(testing_sessions, installed_apps, counter)
		accs.append(acc)

		predictor = MFUPredictor()
		predictor.train(list(itertools.chain(*training_sessions)))
		# testing_sessions = filter(lambda x: len(x) > 1, testing_sessions)
		mfu_acc, mrr = predictor.test(list(itertools.chain(*testing_sessions)), 4)
		print mfu_acc
		mfu_accs.append(mfu_acc)


		# installed_apps = train_by_ic([list(itertools.chain(*training_sessions))])
		# test([list(itertools.chain(*testing_sessions))], installed_apps)
		# break
	print sum(accs)/len(accs), sum(mfu_accs)/len(mfu_accs)
if __name__ == '__main__':
	main()