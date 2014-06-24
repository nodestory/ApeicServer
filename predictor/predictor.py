import abc
from collections import defaultdict

class Predictor():

	@abc.abstractmethod
	def train(self, data):
	    return

	@abc.abstractmethod
	def predict(self, data, k=4):
		return

	def test(self, launches, predictions, k=4):
		N = float(len(predictions))
		hr = len(filter(lambda i: launches[i] in predictions[i], xrange(len(predictions))))/N
		mrr = sum(map(lambda x, y: 1.0/(y.index(x) + 1) if x in y else 0, launches, predictions))/N
		return hr, mrr

import datetime
import math
from itertools import chain
def split(sessions, aggregated=False):
	start_date = sessions[0][0]['datetime']
	end_date = sessions[-1][-1]['datetime']
	passed_weeks = int(math.ceil((end_date - start_date).days/7.0))
	training_weeks = int(math.floor(passed_weeks*0.8))
	split_date = start_date + datetime.timedelta(days=training_weeks*7)

	split_index = len(sessions)
	for i in xrange(len(sessions)):
		if (sessions[i][0]['datetime'] - split_date).days > 0:
			split_index = i
			break

	training_sessions = sessions[:split_index]
	testing_sessions = sessions[split_index:]
	if aggregated:
		return list(chain(*training_sessions)), list(chain(*testing_sessions))
	else:
		return training_sessions, testing_sessions