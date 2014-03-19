import datetime
import operator
from collections import defaultdict
from termcolor import colored
from apeic_db_manager import ApeicDBHelper as DB

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
	apps = DB.select('%s_installed_apps' % user, 
		select_items=('application', 'start_date'))

	history = defaultdict(list)
	map(lambda x: history[x[1].date()].append(x[0]), apps)
	history = sorted(history.iteritems(), key=operator.itemgetter(0))
	return history

def get_uninstallation_history(user):
	apps = DB.select('%s_installed_apps' % user, 
		select_items=('application', 'end_date'), 
		where_items={'end_date IS NOT': None})
	
	history = defaultdict(list)
	map(lambda x: history[x[1].date()].append(x[0]), apps)
	history = sorted(history.iteritems(), key=operator.itemgetter(0))
	return history

def main():
	users = ['5f83a438d9145bb2', \
         '7fab9970aff53ef4', \
         '11d1ef9f845ec10e', \
         '475f258ecc566658', \
         '15002028b1f352fe', \
         'ff3be9536122e83f']

	for user in users:
		print colored(user, attrs=['blink'])

		print_app_events(user)
		
		print 

if __name__ == '__main__':
	main()