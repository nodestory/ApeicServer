import itertools
import operator
from collections import Counter, OrderedDict, defaultdict
from termcolor import colored
from predictor import Predictor
from preprocessor import Preprocessor

import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper

#TODO: rename class
class App():
	def __init__(self, pkg_name):
		self.name = pkg_name
		self.ocrs = 0
		self.pred_co_ocrs = defaultdict(int)
		self.pred_influence = defaultdict(int)
		self.repeatedness = 0

class ApeicPredictor(Predictor):

	def __init__(self):
		self.triggers = defaultdict(int)
		self.used_apps = {}

	def update(self, session):
		self.triggers[session[0]['application']] += 1

		for x in session:
			app = self.used_apps.setdefault(x['application'], App(x['application']))
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
							app = self.used_apps.setdefault(successor, App(successor))
							app.pred_co_ocrs[predecessor] += 1.0
							successors.append(successor)

		for pkg_name in self.used_apps:
			successor = self.used_apps[pkg_name]
			for p in successor.pred_co_ocrs:
				predecessor = self.used_apps[p]
				# TODO: perform experiments with differnect measures
				successor.pred_influence[p] = successor.pred_co_ocrs[p]/predecessor.ocrs

	def predict(self, session, k=4):
		if len(session) == 0:
			results = sorted(self.triggers.iteritems(), key=operator.itemgetter(1), reverse=True)
			candidates = map(lambda x: x[0], results)
			return candidates

		ranking = defaultdict(int)
		for pkg_name in self.used_apps:
			ranking[pkg_name] = self.used_apps[pkg_name].pred_influence[session[-1]['application']]
			# TODO: take recency into consideration
			# if pkg_name in map(lambda x: x['application'], session[-4:-1]):
			# 	ranking[pkg_name] += 1
			# if pkg_name in map(lambda x: x['application'], session[:-4]):
			# 	ranking[pkg_name] -= 1
		
		predicted_apps = sorted(ranking.iteritems(), key=operator.itemgetter(1), reverse=True)
		candidates = [x[0] for x in predicted_apps[:4]]
		return candidates

def split(sessions, ratio=0.8):
	split_index = int(len(sessions)*ratio)
	return sessions[:split_index], sessions[split_index:]

def main():
	db_helper = ApeicDBHelper()
	users = db_helper.get_users()
	
	accuracies = []
	for user in users:
		sessions = db_helper.get_sessions(user)
		if len(sessions) < 15:
			continue
		
		print colored(user, attrs=['blink'])
		
		training_sessions, testing_sessions = split(sessions, 0.8)
		
		predictor = ApeicPredictor()
		for session in training_sessions:
			predictor.update(session)

		hits = 0.0
		misses = 0.0
		for session in testing_sessions:
			for i in xrange(len(session)):
				candidates = predictor.predict(session[:i], 4)
				if session[i]['application'] in candidates:
					hits += 1.0
				else:
					misses += 1.0
				
			predictor.update(session)

		acc = hits/(hits + misses)
		accuracies.append(acc)
		print acc
	print sum(accuracies)/len(accuracies)


if __name__ == '__main__':
	main()
