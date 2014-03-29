from collections import Counter, defaultdict
import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper
from predictor import Predictor
from preprocessor import Preprocessor

import itertools
import logging
import math
import operator
from collections import defaultdict, Counter, OrderedDict
from termcolor import colored


class MFUPredictor(Predictor):

	def train(self, training_data):
		self.used_apps = Counter(map(lambda x: x['application'], training_data))
		return

	def predict(self, data, k=4):
		return map(lambda x: x[0], self.used_apps.most_common(k))

def main():
	db_helper = ApeicDBHelper()
	preprocessor = Preprocessor()
	users = db_helper.get_users()

	results = []
	for user in users:
		logs = db_helper.get_logs(user)
		if len(logs) < 20:
			continue
		training_logs, testing_logs = preprocessor.split(logs, 0.8)
		predictor = MFUPredictor()
		predictor.train(training_logs)

		hit_rate, mrr = predictor.test(testing_logs, 4)
		print hit_rate
		results.append((hit_rate, mrr))
	avg_hit_rate = sum(map(lambda x: x[0], results))/len(results)
	avg_mrr = sum(map(lambda x: x[1], results))/len(results)
	print avg_hit_rate, avg_mrr

if __name__ == '__main__':
	main()