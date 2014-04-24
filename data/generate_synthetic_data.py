# TODO
import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper

from collections import Counter, defaultdict
from itertools import groupby
from operator import itemgetter

class AppDistr(object):

    def __init__(self, ocrs, day_distr, hr_distr, act_distr):
        self.ocrs = ocrs
        self.day_distr = day_distr
        self.hr_distr = hr_distr
        self.act_distr = act_distr

    def get_ei_score(self, env_context):
    	pass

class RealDataAnalyzer():

	def __init__(self):
		pass

	def get_segment_len_distrs(self):
		distr = defaultdict(list)

		db = ApeicDBHelper()
		for user in db.get_users():
			sessions = db.get_sessions(user)
			for session in sessions:
				int_context = map(lambda x: x['application'], session)
				session_len = len(int_context)
				initiator = max(set(int_context), key=int_context.count)
				indices = [i for i, x in enumerate(int_context) if x == initiator] + [session_len]
				if len(indices) == 2:
					distr[session_len].append(session_len)
				else:
					for i in xrange(1, len(indices)):
						distr[session_len].append(indices[i] - indices[i-1])	

		distr = dict(map(lambda x: (x, Counter(distr[x])), distr))
		return distr

	def get_app_usage_distrs(self):
		app_usage_distrs = {}

		db = ApeicDBHelper()
		for user in db.get_users():
			print user
			# TODO: check get logs
			logs = db.get_logs(user)
			logs = map(lambda x: self._format(x), logs)
			user_traces = sorted(logs, key=itemgetter(-1))
			for app, traces in groupby(user_traces, lambda x: x[-1]):
				cluster = list(traces)
				# TODO: range(3) make it static
				count = app_usage_distrs.keys().count(app)
				app_usage_distrs['%s_%d' % (app, count + 1)] = tuple(map(lambda i: self._get_feature_distr(i, cluster), range(3)))

		return app_usage_distrs
        
	def _format(self, log):
	    day = log['datetime'].isoweekday()
	    hour = log['datetime'].hour
	    act = 'STATIC' if log['activity'] in ['STILL', 'TILTING'] else log['activity']
	    app = log['application']
	    return day, hour, act, app

	def _get_feature_distr(self, feature_index, cluster):
		distr = defaultdict(lambda: 1e-8)
		for k, v in groupby(cluster, lambda x: x[feature_index]):
			distr[str(k)] += sum(1 for _ in v)
		n = float(sum(distr.values()))
		for att in distr:
		    distr[att] /= n
		return distr



class SyntheticDataGenerator():

	def __init__(self):
		analyzer = RealDataAnalyzer()
		self.segment_len_distrs = analyzer.get_segment_len_distrs()
		self.app_usage_distrs = analyzer.get_app_usage_distrs()

	def generate_sessions(self, session_num=500, session_len=5):
		env_contexts = self._generate_env_contexts()
		for env_context in env_contexts:
			pass

	def _generate_env_contexts(self):
		# TODO: refactor
        os.system('benerator.sh test.xml')
        with open('app_usage_logs.flat', 'r') as f:
            lines = f.readlines()
            env_contexts = map(lambda x: x.strip().split(), lines)
        return env_contexts

    def _develop_int_context(self, env_context):
    	pass

    def _generate_segment(self, initiator):
    	pass

	def _get_segment_len_distr(self, session_len):
		return self.segment_len_distrs[session_len]




def main():
	analyzer = RealDataAnalyzer()
	analyzer.get_app_usage_distrs()

if __name__ == '__main__':
	main()