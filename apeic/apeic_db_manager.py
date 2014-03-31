# -*- coding: utf-8 -*-I
import datetime
import mosql.mysql
from mosql.util import raw
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

    # def get_logs(self, user):
    #     rows = self.select('%s_app_usage_logs' % user, 
    #         where_items=and_(map(lambda x: {'application !=': x}, ApeicDBHelper.IGNORED_APPLICATIONS)))
    #     logs = [rows[0]]
    #     for i in xrange(1, len(rows)):
    #         if rows[i]['application'] != logs[-1]['application']:
    #             logs.append(rows[i])
    #     return logs

    def get_logs(self, user):
        rows = self.select('%s_app_usage_logs' % user, 
            where_items=and_(map(lambda x: {'application !=': x}, ApeicDBHelper.IGNORED_APPLICATIONS)))
        return rows

    # IGNORED_APPLICATIONS = ['null', 'com.htc.launcher', 'com.tul.aviate', 'com.android.settings', 'android']
    IGNORED_APPLICATIONS = ['null', 'com.htc.launcher', 'com.tul.aviate']
    def get_sessions(self, user):
        logs = self.select('%s_app_usage_logs' % user, 
            where_items=and_(map(lambda x: {'application !=': x}, ApeicDBHelper.IGNORED_APPLICATIONS)))
        segments = []

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

        # TODO: merge sessions whose interval is less than on minute
        # interval = (log[1] - segments[-1][-1][1]).seconds
        # 0 < interval <= 60

        sessions = []
        for segment in segments:
            session = [segment[0]]
            for log in segment[1:]:
                if log['application'] != session[-1]['application']:
                    session.append(log)
            sessions.append(session)
        sessions = map(lambda x: x[1:] if x[0] in ['com.htc.launcher', 'com.tul.aviate'] else x, sessions)
        return sessions

def main():
    db_helper = ApeicDBHelper()
    print '\n'.join(db_helper.get_users())
    sessions = db_helper.get_sessions('5f83a438d9145bb2')
    for session in sessions:
        for x in session:
            pass
            #print x
        #print 

if __name__ == '__main__':
    main()
