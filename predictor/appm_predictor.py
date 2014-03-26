from predictor import Predictor
from collections import Counter, defaultdict

class APPMPredictor(Predictor):

	def train(self, training_data):
		# used_apps = set(map(lambda x: x['application'], training_data))
		used_apps = defaultdict(int)

		for i in xrange(2, len(training_data)):
			training_data[i-1]['application']
			training_data[i-2]['application']
			used_apps[training_data[i]['application']]
		return

	def predict(self, n, k=4):
		return map(lambda x: x[0], self.used_apps.most_common(k))