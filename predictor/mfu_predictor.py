from predictor import Predictor
from collections import Counter, defaultdict

class MFUPredictor(Predictor):

	def train(self, training_data):
		self.used_apps = Counter(map(lambda x: x['application'], training_data))
		return

	def predict(self, data, k=4):
		return map(lambda x: x[0], self.used_apps.most_common(k))