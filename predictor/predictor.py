import abc
from collections import defaultdict

IGNORED_LAUNCHES = [u'com.android.systemui', u'com.htc.launcher', u'android', u'com.tul.aviate', u'com.android.settings']

class Predictor():

	def split(self, data, ratio=0.8):
		split_index = int(len(data)*ratio)
		return data[:split_index], data[split_index:]

	@abc.abstractmethod
	def train(self, training_data):
	    return

	@abc.abstractmethod
	def predict(self, data, k=4):
		return

	def test(self, testing_data, k=4):
		N = float(len(testing_data))
		results = filter(lambda x: x['application'] in self.predict(x, k), testing_data)

		hit_rate = len(results)/N
		mrr = sum(map(lambda x: 1/(self.predict(x, k).index(x['application']) + 1), results))/N
		
		return hit_rate, mrr