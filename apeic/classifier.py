from collections import defaultdict, OrderedDict
from termcolor import colored
from apeic_db_manager import ApeicDBHelper

class App():
	def __init__(self, pkg_name):
		self.name = pkg_name
		self.occurrences = 0
		self.predecessor_occurrences = defaultdict(int)
		self.predecessor_influence = defaultdict(float)

	def add_occurrence(self):
		self.occurrences += 1

	def add_predecessor_occurrence(self, predecessor):
		self.predecessor_occurrences[predecessor] += 1


def main():
	users = ['5f83a438d9145bb2', \
         '7fab9970aff53ef4', \
         '11d1ef9f845ec10e', \
         '475f258ecc566658', \
         '15002028b1f352fe', \
         'ff3be9536122e83f']

	for user in users:
		print colored(user, attrs=['blink'])

		installed_apps = {}

		db_helper = ApeicDBHelper()
		sessions = db_helper.get_sessions(user)
		for session in sessions:
			print '==='
			print '\n'.join([x['application'] for x in session])
			print
			for x in session:
				app = installed_apps.setdefault(x['application'], App(x['application']))
				app.add_occurrence()

			if len(session) > 1:
				app_pkg_names = [x['application'] for x in session]
				for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
					indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]
					indices.append(len(session))
					for i in xrange(len(indices) - 1):
						if indices[i] + 1 < indices[i+1]:
							for j in xrange(indices[i] + 1, indices[i+1]):
								successor = session[j]['application']
								# print predecessor, '->', successor
								app = installed_apps.setdefault(successor, App(successor))
								app.add_predecessor_occurrence(predecessor)
				print

		for app_pkg_name in installed_apps:
			print app_pkg_name, installed_apps[app_pkg_name].occurrences
			for p in installed_apps[app_pkg_name].predecessor_occurrences:
				print p, installed_apps[app_pkg_name].predecessor_occurrences[p]
			print 
		break

if __name__ == '__main__':
	main()