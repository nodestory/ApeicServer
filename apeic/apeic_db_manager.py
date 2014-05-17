import datetime
import mosql.mysql
from mosql.build import and_, select, update, join, insert, delete
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

APEIC_DATABASE_URI = 'mysql://linzy:yatingcj6@localhost/apeic?charset=utf8'

class ApeicDBHelper(object):

    engine = create_engine(APEIC_DATABASE_URI)
    
    @classmethod
    def execute(cls, cmd, contain_key=False):
        conn = cls.engine.connect()
        try:
            cmd = cmd.replace('%','%%')
            conn.execute('SET NAMES UTF8')
            data = conn.execute(cmd)
            # TODO:: rollback
        finally:
            conn.close()

        if data.rowcount == 0:
            return []
        else:
            if contain_key:
                return [dict(x) for x in data]
            else:
                try:
                    return data.fetchall()
                except:
                    return []

    @classmethod
    def insert(cls, table, data):
        cmd = insert(table, data)
        cls.execute(cmd)

    @classmethod
    def select(cls, table, select_items=None, where_items=None):
        cmd = select(
            table = table,
            select = select_items,
            where = where_items
        )
        return cls.execute(cmd)

    @classmethod
    def delete(cls, table, where_items):
        cmd = delete(
            table = table,
            where = where_items
        )
        cls.execute(cmd)

    @classmethod
    def update(cls, table, set_items, where_items=None):
        cmd = update(
            table = table,
            set = set_items,
            where = where_items
        )
        cls.execute(cmd)

    def get_users(self):
        cmd = 'SHOW TABLES LIKE "%_installed_apps"'
        rows = self.execute(cmd)
        return map(lambda x: x[0].replace('_installed_apps', ''), rows)

    IGNORED_APPLICATIONS = [u'null', u'com.android.launcher', u'com.htc.launcher', u'com.tul.aviate']
    def get_logs(self, user):
        rows = self.select('%s_app_usage_logs' % user, 
            where_items=and_(map(lambda x: {'application !=': x}, ApeicDBHelper.IGNORED_APPLICATIONS)))
        logs = [rows[0]]
        for i in xrange(1, len(rows)):
            if rows[i]['application'] != logs[-1]['application']:
                logs.append(rows[i])
        return logs

    def get_sessions(self, user):
        logs = self.select('%s_app_usage_logs' % user, where_items={'application !=': 'null'})
        segments = []

        # split records into independent segments
        if len(logs) == 0:
            return[]
        log = logs.pop(0)
        segments.append([])
        segments[-1].append(log)
        while logs:
            log = logs.pop(0)
            if log[0] != segments[-1][-1][0] + 1:
                segments.append([])  
            segments[-1].append(log)

        new_segments = []
        for segment in segments:
            segment = filter(lambda x: x['application'] not in [ \
                                'android', \
                                'com.android.launcher', 'com.htc.launcher', 'com.sec.android.app.launcher', \
                                'com.tul.aviate', 'com.coverscreen.cover', 'com.mycolorscreen.themer', \
                                'com.thinkyeah.smartlockfree', 'com.htc.android.worldclock', 'com.zdworks.android.zdclock' \
                                ], segment)
            if len(segment) > 0:
                new_segments.append(segment)

        # new_segments = []
        # new_segments.append(segments[0])
        # for i in xrange(1, len(segments)):
        #     if segments[i][0]['application'] == segments[i-1][-1]['application']:
        #         new_segments.append(segments[i][1:])
        # new_segments = filter(lambda x: x, new_segments)

        # remove duplicate records
        sessions = []
        for segment in new_segments:
            session = [segment[0]]
            for log in segment[1:]:
                if log['application'] != session[-1]['application']:
                    session.append(log)
            # session = filter(lambda x: x['application'] not in ['android', 'com.android.launcher', \
            #         'com.htc.launcher', 'com.sec.android.app.launcher', 'com.tul.aviate', \
            #         'com.thinkyeah.smartlockfree', 'com.htc.android.worldclock'], session)
            if session:
                sessions.append(session)
        return sessions

        # sessions = map(lambda x: x[1:] if x[0] in ['com.htc.launcher', 'com.tul.aviate'] else x, sessions)
        # return sessions
        # print len(sessions)

        # filtered_sessions = []
        # for session in sessions:
        #     new_session = []
        #     for log in session:
        #         if log['application'] not in ['com.android.launcher', \
        #             'com.htc.launcher', 'com.tul.aviate', 'com.thinkyeah.smartlockfree']:
        #             new_session.append(log)
        #     if len(new_session) > 0:
        #         filtered_sessions.append(new_session)

        # print len(filtered_sessions)
        # return filtered_sessions

        # merge sessions whose interval is less than on minute
        aggregated_sessions = []
        session = sessions.pop(0)
        aggregated_sessions.append(session)
        while sessions:
            session = sessions.pop(0)
            if (session[0]['datetime'] - aggregated_sessions[-1][-1]['datetime']).seconds < 60:
                aggregated_sessions[-1].extend(session)
            else:
                aggregated_sessions.append(session)
        return aggregated_sessions

        # remove duplicate records
        sessions = []
        for s in aggregated_sessions:
            session = [s[0]]
            for log in s[1:]:
                if log['application'] != session[-1]['application']:
                    session.append(log)
            sessions.append(session)
        return sessions

    def get_unbiased_sessions(self, user):
        self.get_sessions(user)
        last = sessions[0][-1]['application']
        test = [sessions[0]]
        for s in sessions[1:]:
            if len(s) > 1:
              print s[1]['datetime'] - s[0]['datetime']
            if s[0]['application'] == last:
              if s[1:]:
                  test.append(s[1:])
            else:
              test.append(s)
            last = s[-1]['application']
        return test

    def get_used_apps(self, user):
        rows = self.execute('SELECT DISTINCT application from %s_app_usage_logs' % user)
        apps = map(lambda x: x[0], rows)
        apps = filter(lambda x: x not in ApeicDBHelper.IGNORED_APPLICATIONS, apps)
        return apps

from pymining import itemmining
import itertools
import operator
from collections import Counter
from collections import Counter, OrderedDict, defaultdict
def main():
    db_helper = ApeicDBHelper()

    users = db_helper.get_users()
    for user in users[1:]:
        print user
        hits = 0.0
        misses = 0.0
        sessions = db_helper.get_sessions(user)
        used_apps = []
        for session in sessions:
            used_apps += map(lambda x: x['application'], session)
        # used_apps += map(lambda x: x[0]['application'], sessions)
        counter = Counter(used_apps)
        for k in counter:
            print k, counter[k]
        print
        # print len(set(used_apps))
        # print len(filter(lambda x: counter[x] > 10, counter))

        # terminator = sessions[0][-1]['application']
        # for session in sessions[1:]:
        #     if session[0]['application'] == terminator:
        #         hits += 1.0
        #     else:
        #         misses += 1.0
        #     terminator = session[0]['application']
        # print hits/(hits + misses)
        break

if __name__ == '__main__':
    main()

