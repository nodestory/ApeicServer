import operator
from predictor import Predictor
from collections import Counter, defaultdict
from termcolor import colored

import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper

class App():
	r = 0.85

	def __init__(self, pkg_name):
		self.crf = 0

		self.ocrs = 0
		self.avg_duration = 0
		self.crfd = 0

		self.hod = defaultdict(int)
		self.dow = defaultdict(int)

		self.pred_co_ocrs = defaultdict(int)
		self.seq = defaultdict(int)
		

	def update_crf(self, is_present):
		self.crf = (1 if is_present else 0) + App.r*self.crf

	def update_crfd(self, duration):
		avg_duration = (self.avg_duration*self.ocrs + duration)/(self.ocrs + 1)
		self.avg_duration = avg_duration
		if duration == 0:
			dw = 0
		elif 0.0*avg_duration < duration <= 0.5*avg_duration:
			dw = 0.8
		elif 0.5*avg_duration < duration <= 0.5*avg_duration:
			dw = 1.0
		else:
			dw = 1.2

		self.crfd = dw + App.r*self.crfd
		self.ocrs += 1

	def update_hod(self, hour):
		self.hod[hour] += 1.0

	def update_dow(self, day):
		self.dow[day] += 1.0

	def add_predecessor(self, predecessor):
		self.pred_co_ocrs[predecessor] += 1.0

	def normalize(self, used_apps):
		denominator = sum(self.hod.values())
		for hour in self.hod:
			self.hod[hour] /= denominator

		denominator = sum(self.dow.values())
		for day in self.dow:
			self.dow[dat] /= denominator

		for predecessor in self.pred_co_ocrs:
			self.seq[predecessor] = self.pred_co_ocrs[predecessor]/used_apps[predecessor].ocrs


class APPRushPredictor(Predictor):
	r = 0.5

	def __init__(self):
		self.used_apps = {}

	def train(self, training_data):
		last_log = training_data[0]
		start = last_log['datetime']
		index = 0
		# for log in training_data[1:]:
		for i in xrange(1, len(training_data)):
			if training_data[i]['application'] != last_log['application'] or training_data[i]['id'] == training_data[-1]['id']:
				duration = (training_data[i]['datetime'] - start).seconds

				for pkg_name in self.used_apps:
					app = self.used_apps.setdefault(pkg_name, App(pkg_name))
					app.update_crf(pkg_name == last_log['application'])
					app.update_crfd(duration if pkg_name == last_log['application'] else 0)

				app = self.used_apps.setdefault(last_log['application'], App(last_log['application']))
				app.update_hod(last_log['datetime'].hour)
				app.update_hod(last_log['datetime'].isoweekday())
				if index > 0:
					app.add_predecessor(training_data[index-1]['application'])
				
				last_log = training_data[i]
				start = training_data[i]['datetime']
				index = i

		for pkg_name in self.used_apps:
			app = self.used_apps.setdefault(pkg_name, App(pkg_name))
			app.normalize(self.used_apps)


	wc = 0.6
	def predict(self, last_log, log, k=4):
		hour = log['datetime'].hour
		day = log['datetime'].isoweekday()
		last_app = last_log['application']

		ranking = defaultdict(int)
		for pkg_name in self.used_apps:
			app = self.used_apps.setdefault(pkg_name, App(pkg_name))
			ranking[pkg_name] = 0.6*app.crf + 0.6*app.crfd + 0.61*app.hod[hour] + 0.33*app.dow[day] + 0.87*app.seq[last_app]
			# ranking[pkg_name] = app.seq[last_app]
			# ranking[pkg_name] = wc*app.crfd + wh*app.hod[hour] + wd*app.dow[day] + ws*app.seq[last_app]
			
		results = sorted(ranking.iteritems(), key=operator.itemgetter(1), reverse=True)
		candidates = map(lambda x: x[0], results[:k])
		return candidates

def main():
	db_helper = ApeicDBHelper()
	users = db_helper.get_users()
	
	accuracies = []
	for user in users:
		if user == '11d1ef9f845ec10e':
			continue

		print colored(user, attrs=['blink'])

		logs = db_helper.get_logs(user)

		predictor = APPRushPredictor()
		training_logs, testing_logs = predictor.split(logs, 0.8)
		predictor.train(training_logs)


		hits = 0.0
		misses = 0.0
		last_log = testing_logs[0]
		for log in testing_logs[1:]:
			if log['application'] != last_log['application'] or log['id'] == testing_logs[-1]['id']:
				candidates = predictor.predict(last_log, log, 8)

				if log['application'] in candidates:
					hits += 1
				else:
					misses += 1

				last_log = log

		acc = hits/(hits + misses)
		accuracies.append(acc)
		print acc
	print sum(accuracies)/len(accuracies)
		

if __name__ == '__main__':
	main()