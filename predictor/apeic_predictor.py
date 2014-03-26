from predictor import Predictor
from collections import Counter, defaultdict

class App():
	def __init__(self, pkg_name):
		self.name = pkg_name
		self.ocrs = 0
		self.pred_co_ocrs = defaultdict(int)
		self.pred_influence = defaultdict(lambda: -1)
		self.ocrs_in_sessions = []
		self.repeatability = 0

	def add_predecessor_cooccurrence(self, predecessor):
		self.pred_co_ocrs[predecessor] += 1

class ApeicPredictor(Predictor):

	def train(self, sessions):
		used_apps = {}

		for session in sessions:
			counter = Counter([x['application'] for x in session])
			for pkg_name in counter:
				used_apps[pkg_name].ocrs_in_sessions.append(counter[used_apps])

			for x in session:
				app = used_apps.setdefault(x['application'], App(x['application']))
				app.ocrs += 1

			if len(session) > 1:
				app_pkg_names = [x['application'] for x in session]
				for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
					indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]
					indices.append(len(session))
					for i in xrange(len(indices) - 1):
						for j in xrange(indices[i] + 1, indices[i+1]):
							successor = session[j]['application']
							# print colored('%s -> %s' % (predecessor, successor), 'cyan')
							app = used_apps.setdefault(successor, App(successor))
							app.pred_co_ocrs[predecessor] += 1
			# print 

		for pkg_name in used_apps:
			successor = used_apps[pkg_name]
			for p in successor.pred_co_ocrs:
				predecessor = used_apps[p]
				successor.pred_influence[p] = compute_relatedness(
					successor.pred_co_ocrs[p], predecessor.ocrs, successor.ocrs, len(sessions), 5)

			ocrs_in_sessions = used_apps[pkg_name].ocrs_in_sessions
			used_apps[pkg_name] = sum(ocrs_in_sessions)/float(ocrs_in_sessions)

		self.used_apps = used_apps

	def predict(self, data, k=4):
		return map(lambda x: x[0], self.used_apps.most_common(k))