from predictor import Predictor
from collections import Counter, defaultdict

class App():
	def __init__(self, pkg_name):
		self.crf = 0
		self.hods = []
		self.dows = []

		self.name = pkg_name
		self.ocrs = 0
		self.pred_co_ocrs = defaultdict(int)
		self.pred_influence = defaultdict(lambda: -1)
		self.repeatedness = 0

	def add_occurrence(self):
		self.ocrs += 1

	def add_predecessor_cooccurrence(self, predecessor):
		self.pred_co_ocrs[predecessor] += 1

class APPRushPredictor(Predictor):

	def fomat(self, logs):
		used_apps = {}

		# for app_name in set(map(lambda x: x['application'], logs)):
		for log in logs:
			app = installed_apps.setdefault(x['application'], App(x['application']))
			used_apps[app_name] = App(app_name)
			app_logs = filter(lambda x: x['application'] == app_name, logs)
			for 
			self.crf = (1 if is_launched else 0) + App.r*self.crf

	def train(self, training_data):
		self.used_apps = Counter(map(lambda x: x['application'], training_data))
		return

	def predict(self, n, k=4):
		return map(lambda x: x[0], self.used_apps.most_common(k))