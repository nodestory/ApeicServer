import operator
from collections import Counter, defaultdict
from mosql.build import select, update, join, insert, delete
from termcolor import colored
from apeic_db_manager import ApeicDBConnManager as DB
from apeic_db_helper import get_logs, get_sessions, get_installed_apps_history

def compute_repeatability(sessions):
    repeatability = defaultdict(list)
    for session in sessions:
        counts = Counter([x[-1] for x in session])
        for app in counts:
            repeatability[app].append(counts[app])
    
    for app in repeatability:
        repeatability[app] = sum(repeatability[app])/float(len(repeatability[app]))

    return sorted(repeatability.iteritems(), key=operator.itemgetter(1), reverse=True)

def compute_idf(sessions):
    df = defaultdict(int)
    for session in sessions:
        apps = set([x[-1] for x in session])
        for app in apps:
            df[app] += 1

    N = float(len(sessions))
    print N
    idf = defaultdict(int)
    for app in df:
        print df[app]
        idf[app] = N/df[app]
    # return app_idf
    return sorted(idf.iteritems(), key=operator.itemgetter(1), reverse=True)    

users = ['5f83a438d9145bb2', \
         '7fab9970aff53ef4', \
         '11d1ef9f845ec10e', \
         '475f258ecc566658', \
         '15002028b1f352fe', \
         'ff3be9536122e83f']

for user in users:
    table_name = user + '_app_usage_logs'
    logs = get_logs(table_name, 'ALL')
    # logs = DB.execute(select(table_name))
    sessions = get_sessions(logs)

    print colored(user, 'blue')

    # compute the repeatability of an App in sessions
    """
    app_repeatability = compute_repeatability(sessions)
    for app, repeatability in app_repeatability:
        print app, repeatability
    print
    """

    # compute idf
    # app_idf = compute_idf(sessions)
    # for app, idf in app_idf:
    #     print app, idf
    # print

    get_installed_apps_history(user)

    print