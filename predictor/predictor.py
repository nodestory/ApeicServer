import abc
from collections import defaultdict

class Predictor():

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