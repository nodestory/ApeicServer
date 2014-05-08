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

import datetime
from itertools import chain
def split(sessions, ratio=0.8):
	# print (sessions[-1][-1]['datetime'] - sessions[0][0]['datetime']).days
	start_date = sessions[0][0]['datetime']
	midnight = datetime.time(0)
	start_date = datetime.datetime.combine(start_date.date(), midnight)
	end_date = start_date + datetime.timedelta(days=7)

	split_index = int(len(sessions)*ratio)
	for i in xrange(len(sessions)):
		if (sessions[i][0]['datetime'] - end_date).days > 0:
			split_index = i
			break

	test_sessions = sessions[split_index:]
	start_date = test_sessions[0][0]['datetime']
	midnight = datetime.time(0)
	start_date = datetime.datetime.combine(start_date.date(), midnight)
	end_date = start_date + datetime.timedelta(days=7)
	tt = -1
	for i in xrange(len(test_sessions)):
		if (test_sessions[i][0]['datetime'] - end_date).days > 0:
			tt = i
			break
	if tt != -1:
		test_sessions = test_sessions[:tt]

	# print split_index, len(sessions) - split_index
	return sessions[:split_index], sessions[split_index:]
	return sessions[:split_index], test_sessions


def main():
	hits = 0.0
	misses = 0.0
	m = 0.0

	db_helper = ApeicDBHelper()
	users = db_helper.get_users()
	for user in users:
		logs = db_helper.get_logs(user)
		if user == '11d1ef9f845ec10e':
			continue
		# preprocessor = Preprocessor(logs)
		# training_logs, testing_logs = preprocessor.split(logs, 0.8)
		sessions = db_helper.get_sessions(user)
		training_sessions, testing_sessions = split(sessions)
		training_logs = list(chain(*training_sessions))
		testing_logs = list(chain(*testing_sessions))
		predictor = MFUPredictor()
		predictor.train(training_logs)

		candidates = predictor.predict(None, 1)
		print candidates
		for log in testing_logs:
			if log['application'] in candidates:
				hits += 1.0
				m += 1.0/(candidates.index(log['application']) + 1)
			else:
				misses += 1.0
	
	print (hits)/(hits + misses), m/(hits + misses)

if __name__ == '__main__':
	main()