import itertools
import operator
import sys
import MySQLdb
from collections import Counter, defaultdict

class App:
    # weight for adjusting recency and frequency
    r = 0.1

    def __init__(self, package_name, installed_apps):
        self.name = package_name
        self.crf = 0
        self.recency = 0
        self.predecessors = {}
        for app in installed_apps:
            self.predecessors[app] = 0

    # CRF
    def update_crf(self, is_launched):
        self.crf = (1 if is_launched else 0) + App.r*self.crf

    # Interactional Context (IC)
    def register_predecessor(self, app):
        self.predecessors[app] = 0

    def add_predecessor_influence(self, app, dist):
        self.predecessors[app] += 1.0/dist

    # Enviromental Context (EC)

def get_logs(table, start_date, end_date):
    db = MySQLdb.connect(host="localhost", user="linzy", passwd="yatingcj6", db="apeic")
    cursor = db.cursor()
    cursor.execute('SELECT id, application FROM %s \
        WHERE datetime BETWEEN "%s 00:00:00" AND "%s 23:59:59"' \
        % (table, start_date, end_date))
    return cursor.fetchall()

def segment(logs):
    segments = []
    segment = []
    for log in logs:
        id = log[0]
        app = log[-1]
        if app != 'null':
            segment.append(log)
        else:
            if segment:
                segments.append(segment)
            segment = []
    return segments

def merge(segments):
    sessions = []
    for segment in segments:
        session = [segment[0]]
        for log in segment[1:]:
            if log[-1] != session[-1][-1]:
                session.append(log)
        sessions.append(session)
    return sessions

def train(sessions):
    installed_apps = {}
    for session in sessions:
        for id, app_pkg_name in session:
            # print id, app_pkg_name
            if app_pkg_name not in installed_apps:
                installed_apps[app_pkg_name] = App(app_pkg_name, installed_apps.keys())
                for app in installed_apps:
                    installed_apps[app].register_predecessor(app_pkg_name)

            for a in installed_apps:
                installed_apps[a].update_crf(a == app_pkg_name)

        if len(session) > 1:
            print '\n'.join([x[1] for x in session])
            for i in xrange(1, len(session)):
                for j in xrange(i):
                    # print j,
                    dist = i - j
                    installed_apps[session[i][1]]. \
                        add_predecessor_influence(session[j][1], dist)
                    # print session[j][1], '->', session[i][1], \
                    #     installed_apps[session[i][1]].predecessors[session[j][1]]
                # print ' -> ', i
                print 
            print

def test():
    pass


def compute_crf(sessions):
    installed_apps = {}
    for session in sessions:
        for id, app_pkg_name in session:
            # print id, app_pkg_name
            if app_pkg_name not in installed_apps:
                installed_apps[app_pkg_name] = App(app_pkg_name, installed_apps.keys())
                for app in installed_apps:
                    installed_apps[app].register_predecessor(app_pkg_name)

            for a in installed_apps:
                installed_apps[a].update_crf(a == app_pkg_name)
    for app in installed_apps:
        print app, installed_apps[app].crf

def compute_repeatability(sessions):
    repeatability = defaultdict(list)
    for session in sessions:        
        counts = Counter([app for id, app in session])
        for app in counts:
            repeatability[app].append(counts[app])

    for app in repeatability:
        print app, sum(repeatability[app])/float(len(repeatability[app]))

def compute_causality(sessions):
    installed_apps = {}
    for session in sessions:
        for id, app_pkg_name in session:
            # print id, app_pkg_name
            if app_pkg_name not in installed_apps:
                installed_apps[app_pkg_name] = App(app_pkg_name, installed_apps.keys())
                for app in installed_apps:
                    installed_apps[app].register_predecessor(app_pkg_name)

        if len(session) > 1:
            apps_in_session = [app for id, app in session]
            print '\n'.join(apps_in_session)
            apps = list(set(apps_in_session))
            for a, b in itertools.combinations(apps, 2):
                # print a, b
                if apps_in_session.index(a) < apps_in_session.index(b):
                    print a, '->', b
                    installed_apps[b]. \
                        add_predecessor_influence(a, 1)
                else:
                    print b, '->', a
                    installed_apps[a]. \
                        add_predecessor_influence(b, 1)
            print 

    for app in installed_apps:
        print app
        for p in installed_apps[app].predecessors:
            print p, installed_apps[app].predecessors[p]
        print 

def main():
    # 68231230_3e25_4d31_bbd1_f3d2f12031de_app_usage_logs
    # c3547530_668d_41f4_9c41_49d2164aa0de_app_usage_logs
    training_logs = get_logs('68231230_3e25_4d31_bbd1_f3d2f12031de_app_usage_logs', 
        '2014-03-12', '2014-03-15')
    segments = segment(training_logs)
    sessions = merge(segments)
    compute_causality(sessions)
    # compute_repeatability(sessions)
    # compute_crf(sessions)
    # train(sessions)
    sys.exit()

    count = 0
    for session in sessions:
        for id, app in session:
            count += 1
            print count, app
        print 

    ranking = {}
    for app in installed_apps:
        ranking[app] = installed_apps[app].get_crf()
    ranking = sorted(ranking.iteritems(), key=operator.itemgetter(1), reverse=True)
    for r in ranking:
        print r

    print [x[0] for x in ranking[:4]]


    testing_logs = get_logs('c3547530_668d_41f4_9c41_49d2164aa0de_app_usage_logs', 
        '2014-03-13', '2014-03-13')
    segments = segment(testing_logs)
    sessions = merge(segments)
    hit = total = 0 
    for session in sessions:
        for id, app in session:
            print app,
            total += 1
            if app in [x[0] for x in ranking[:4]]:
                hit += 1
    print hit, total

if __name__ == '__main__':
    main()