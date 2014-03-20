import logging
import math
import operator
from collections import defaultdict, OrderedDict
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

	def add_occurrence(self):
		self.ocrs += 1

	def add_predecessor_cooccurrence(self, predecessor):
		self.pred_co_ocrs[predecessor] += 1

def train_by_ic(sessions):
	installed_apps = {}
	N = len(sessions)

	for session in sessions:
		for x in session:
			app = installed_apps.setdefault(x['application'], App(x['application']))
			app.add_occurrence()

		print '\n'.join([x['application'] for x in session])
		if len(session) > 1:
			app_pkg_names = [x['application'] for x in session]
			for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
				indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]
				indices.append(len(session))
				for i in xrange(len(indices) - 1):
					for j in xrange(indices[i] + 1, indices[i+1]):
						successor = session[j]['application']
						print colored('%s -> %s' % (predecessor, successor), 'cyan')
						app = installed_apps.setdefault(successor, App(successor))
						app.add_predecessor_cooccurrence(predecessor)
		print 

	for pkg_name in installed_apps:
		successor = installed_apps[pkg_name]
		print colored(successor.name, 'yellow')
		for p in successor.pred_co_ocrs:
			predecessor = installed_apps[p]
			successor.pred_influence[p] = compute_relatedness(
				successor.pred_co_ocrs[p], predecessor.ocrs, successor.ocrs, len(sessions), 3)
			# print colored(p, 'cyan'), '%d/(%d*%d) = %f' % \
			# 	(successor.pred_co_ocrs[p], predecessor.ocrs, successor.ocrs, successor.pred_influence[p])

	# TODO: check if the computation is correct
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
	else:
		return math.log(N/p_ocrs)*math.log(co_prob/(p_prob*s_prob))/(-math.log(co_prob))

def main():
	users = ['5f83a438d9145bb2', \
       		 '7fab9970aff53ef4', \
         	 '11d1ef9f845ec10e', \
         	 '475f258ecc566658', \
         	 '15002028b1f352fe', \
	         'ff3be9536122e83f']

	for user in users:
		print colored(user, attrs=['blink'])

		installed_apps = {}

		db_helper = ApeicDBHelper()
		sessions = db_helper.get_sessions(user)

		train_by_ic(sessions)
		break

if __name__ == '__main__':
	main()