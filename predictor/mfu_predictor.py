from collections import defaultdict, Counter, OrderedDict
from termcolor import colored
from predictor.predictor import Predictor, split

class MFUPredictor(Predictor):

	def train(self, data):
		self.app_counter = Counter(map(lambda x: x['application'], data))

	def predict(self, data, k=4):
		return map(lambda x: x[0], self.app_counter.most_common(k))

from apeic.apeic_db_manager import ApeicDBHelper
def main():
	predictor = MFUPredictor()

	db_helper = ApeicDBHelper()
	users = db_helper.get_users()
	for user in users:
		logs = db_helper.get_logs(user)
		
		sessions = db_helper.get_sessions(user)
		training_logs, testing_logs = split(sessions, aggregated=True)
		predictor.train(training_logs)
		launches = map(lambda x: x['application'], testing_logs)
		predictions = map(lambda x: predictor.predict(x), testing_logs)
		hr, mrr = predictor.test(launches, predictions)
		print hr, mrr

if __name__ == '__main__':
	main()