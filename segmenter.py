import operator
import sys
import MySQLdb

class App:
    r = 1
    def __init__(self, package_name, installed_apps):
        self.name = package_name
        self.crf = 0
        self.priors = {}
        for app in installed_apps:
            self.priors[app] = 0

    def update_crf(self, is_launched):
        self.crf = (1 if is_launched else 0) + App.r*self.crf

    def get_crf(self):
        return self.crf

    def register_prior(app):
        self.priors[app] = 0

    def update_prior(app, dist):
        self.priors[app]


R = {}

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

def add_app(app):
    R[app] = {}
    for a in R:
        R[app][a] = 0
    for a in R:
        R[a][app] = 0

def main():
    training_logs = get_logs('c3547530_668d_41f4_9c41_49d2164aa0de_app_usage_logs', '2014-03-11', '2014-03-12')
    segments = segment(training_logs)
    sessions = merge(segments)

    installed_apps = {}
    for session in sessions:
        for id, app in session:
            if app not in installed_apps:
                installed_apps[app] = App(app, installed_apps.keys())
            for a in installed_apps:
                installed_apps[a].update_crf(a == app)

            for i in xrange(1, len(session)):
                # print i, '<-',
                for j in xrange(i):
                    # print j,
                    dist = i - j
                    R[session[i][1]][session[j][1]] += (1.0/dist)
                # print 
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

    cursor.execute('SELECT id, application FROM %s \
        WHERE datetime BETWEEN "%s 00:00:00" AND "%s 23:59:59"' \
        % ('c3547530_668d_41f4_9c41_49d2164aa0de_app_usage_logs', '2014-03-13',  '2014-03-13'))
    logs = cursor.fetchall()
    segments = segment(logs)
    sessions = merge(segments)
    total = 0
    hit = 0 
    for session in sessions:
        for id, app in session:
            print app,
            total += 1
            if app in [x[0] for x in ranking[:4]]:
                hit += 1
    print hit, total



    """
    for session in sessions:
        for id, app in session:
            if app not in R:
                add_app(app)
            # print id, app
        # print 

    for session in sessions:
        # if len(session) > 1:
        if len(session) == 5:
            for id, app in session:
                print app
            for i in xrange(1, len(session)):
                # print i, '<-',
                for j in xrange(i):
                    # print j,
                    dist = i - j
                    R[session[i][1]][session[j][1]] += (1.0/dist)
                # print 
            break

    for r in R:
        print r
        for a in R[r]:
            print a, R[r][a]
        print '=='
    """

if __name__ == '__main__':
    main()