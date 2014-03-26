import itertools
import logging
import math
import operator
from collections import defaultdict, Counter, OrderedDict
from termcolor import colored
from apeic_db_manager import ApeicDBHelper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class App():
	def __init__(self, pkg_name):
		self.name = pkg_name
		self.ocrs = 0
		self.pred_co_ocrs = defaultdict(int)
		self.pred_influence = defaultdict(lambda: -1)
		self.repeatedness = 0

	def add_occurrence(self):
		self.ocrs += 1

	def add_predecessor_cooccurrence(self, predecessor):
		self.pred_co_ocrs[predecessor] += 1

def split(sessions, ratio=0.8):
	split_index = int(len(sessions)*ratio)
	return sessions[:split_index], sessions[split_index:]

def train_by_ic(sessions):
	installed_apps = {}
	N = len(sessions)

	for session in sessions:
		for x in session:
			app = installed_apps.setdefault(x['application'], App(x['application']))
			app.add_occurrence()

		# print '\n'.join([x['application'] for x in session])
		if len(session) > 1:
			app_pkg_names = [x['application'] for x in session]
			for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
				indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]
				indices.append(len(session))
				for i in xrange(len(indices) - 1):
					for j in xrange(indices[i] + 1, indices[i+1]):
						successor = session[j]['application']
						# print colored('%s -> %s' % (predecessor, successor), 'cyan')
						app = installed_apps.setdefault(successor, App(successor))
						app.add_predecessor_cooccurrence(predecessor)
		# print 

	for pkg_name in installed_apps:
		successor = installed_apps[pkg_name]
		# print colored(successor.name, 'yellow')
		for p in successor.pred_co_ocrs:
			predecessor = installed_apps[p]
			successor.pred_influence[p] = compute_relatedness(
				successor.pred_co_ocrs[p], predecessor.ocrs, successor.ocrs, len(sessions), 5)
			# print colored(p, 'cyan'), '%d/(%d*%d) = %f' % \
			# 	(successor.pred_co_ocrs[p], predecessor.ocrs, successor.ocrs, successor.pred_influence[p])

	# TODO: check if the computation is correct
	"""
	for p in installed_apps:
		print installed_apps[p].name
		ranking = [(s, installed_apps[s].pred_influence[p]) \
			for s in installed_apps]
		ranking = sorted(ranking, key=operator.itemgetter(1), reverse=True)
		ranking = filter(lambda x: x[1] != -1, ranking)
		for successor, intensity in ranking:
			print ("%2.4f" % intensity).rjust(7), successor
		print 
	"""

	results = defaultdict(list)
	for session in sessions:
		apps = [x['application'] for x in session]
		counts = Counter(apps)
		for app in counts:
			results[app].append(counts[app])

	for app in results:
	    installed_apps[app].repeatedness = sum(results[app])/float(len(results[app]))

	return installed_apps

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
	elif typ == 4:
		return math.log(N/p_ocrs)*math.log(co_prob/(p_prob*s_prob))/(-math.log(co_prob))
	else:
		return co_prob/float(p_prob)


def test(sessions, installed_apps):
	count = 0
	base = 0.0
	for session in sessions:
		results = defaultdict(int)
		used = []
		for i in xrange(1, len(session)):
			if len(session) == 1:
				continue
			for app in installed_apps:
				results[app] = installed_apps[app].pred_influence[session[i-1]['application']]
				# if app in used:
				# 	results[app] = 1 + installed_apps[app].pred_influence[session[i-1]['application']]
				# else:
				# 	results[app] = installed_apps[app].pred_influence[session[i-1]['application']]
			predicted_apps = sorted(results.iteritems(), key=operator.itemgetter(1), reverse=True)
			# print predicted_apps[0], session[i]['application']
			# print predicted_apps[:4]
			if session[i]['application'] in [x[0] for x in predicted_apps[:4]]:
				count += 1
			base += 1
			used.append(session[i]['application'])
	print count/base, base



def main():
	users = ['5f83a438d9145bb2', \
       		 '7fab9970aff53ef4', \
         	 '11d1ef9f845ec10e', \
         	 '475f258ecc566658', \
         	 '15002028b1f352fe']
         	 # 'da832e9ef7b778f9', \
	         # 'ff3be9536122e83f']

	for user in users:
		print colored(user, attrs=['blink']),

		db_helper = ApeicDBHelper()
		sessions = db_helper.get_sessions(user)
		training_sessions, testing_sessions = split(sessions, 0.8)

		
		installed_apps = train_by_ic(training_sessions)
		test(testing_sessions, installed_apps)

		# installed_apps = train_by_ic([list(itertools.chain(*training_sessions))])
		# test([list(itertools.chain(*testing_sessions))], installed_apps)
		# break

if __name__ == '__main__':
	main()