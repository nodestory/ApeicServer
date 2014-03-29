import datetime
import operator
from collections import Counter, OrderedDict, defaultdict
from termcolor import colored
from apeic_db_manager import ApeicDBHelper

def print_app_events(user):
	print colored('Installation', 'magenta', attrs=['underline'])
	history = get_installation_history(user)
	if len(history) > 1:
		for date, apps in history[1:]:
			print colored(date, 'cyan')
			print '\t', '\n\t'.join(apps)
	else:
		print colored('NULL', 'cyan')
		
	print colored('Unnstallation', 'magenta', attrs=['underline'])
	history = get_uninstallation_history(user)
	if len(history) > 1:
		for date, apps in history[1:]:
			print colored(date, 'cyan')
			print '\t', '\n\t'.join(apps)
	else:
		print colored('NULL', 'cyan')

def get_installation_history(user):
	apps = ApeicDBHelper.select('%s_installed_apps' % user, 
		select_items=('application', 'start_date'))

	history = defaultdict(list)
	map(lambda x: history[x[1].date()].append(x[0]), apps)
	history = sorted(history.iteritems(), key=operator.itemgetter(0))
	return history

def get_uninstallation_history(user):
	apps = ApeicDBHelper.select('%s_installed_apps' % user, 
		select_items=('application', 'end_date'), 
		where_items={'end_date IS NOT': None})
	
	history = defaultdict(list)
	map(lambda x: history[x[1].date()].append(x[0]), apps)
	history = sorted(history.iteritems(), key=operator.itemgetter(0))
	return history

def print_app_repeatability(user):
	results = compute_repeatability(user)
	for app, repeatability in results:
		print app, repeatability

def compute_repeatability(user):
	db_helper = ApeicDBHelper()
	sessions = db_helper.get_sessions(user)

	results = defaultdict(list)
	for session in sessions:
		apps = [x['application'] for x in session]
		counts = Counter(apps)
		for app in counts:
			results[app].append(counts[app])

	for app in results:
	    results[app] = sum(results[app])/float(len(results[app]))

	return sorted(results.iteritems(), key=operator.itemgetter(1), reverse=True)

def main():
	db_helper = ApeicDBHelper()
	users = db_helper.get_users()
	print len(users)

	for user in users:
		print colored(user, attrs=['blink'])
		print_app_events(user)
		# print_app_repeatability(user)
		print
		# break

if __name__ == '__main__':
	main()