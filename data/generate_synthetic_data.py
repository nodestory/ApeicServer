# TODO
import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper

from collections import Counter, defaultdict


class RealDataAnalyzer():

	def __init__(self):
		pass

	def get_segment_len_distr(self):
		distr = defaultdict(list)

		db = ApeicDBHelper()
		for user in db.get_users()[1:]:
			sessions = db.get_sessions(user)
			for session in sessions:
				int_context = map(lambda x: x['application'], session)
				session_length = len(int_context)
				initiator = max(set(int_context), key=int_context.count)
				indices = [i for i, x in enumerate(int_context) if x == initiator] + [session_length]
				if len(indices) == 2:
					distr[session_length].append(session_length)
				else:
					for i in xrange(1, len(indices)):
						distr[session_length].append(indices[i] - indices[i-1])	

		distr = dict(map(lambda x: (x, Counter(distr[x])), distr))
		print distr
		print distr[5].keys(), distr[5].values()
		


class SyntheticDataGenerator():

	def __init__(self):
		pass


def main():
	analyzer = RealDataAnalyzer()
	analyzer.get_segment_len_distr()

if __name__ == '__main__':
	main()