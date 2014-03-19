# -*- coding: utf-8 -*-I
import mosql.mysql
from mosql.util import raw
from mosql.build import select, update, join, insert, delete
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

APEIC_DATABASE_URI = 'mysql://linzy:yatingcj6@localhost/apeic?charset=utf8'
# _POOL_SIZE       = APP_CONFIG['SQLALCHEMY_POOL_SIZE']
# _MAX_OVERFLOW    = APP_CONFIG['SQLALCHEMY_MAX_OVERFLOW']
# _TIMEOUT         = APP_CONFIG['SQLALCHEMY_POOL_TIMEOUT']
# _RECYCLE         = APP_CONFIG['SQLALCHEMY_POOL_RECYCLE']
# _ECHO            = False
# _USE_THREADLOCAL = True
# _DEBUG_DB_SQL_CMD = False


class ApeicDBConnManager(object):

    _POOL = create_engine(APEIC_DATABASE_URI)
                          # echo = _DEBUG_DB_SQL_CMD,
                          # echo_pool = True,
                          # poolclass = QueuePool,
                          # max_overflow = _MAX_OVERFLOW,
                          # pool_recycle = _RECYCLE,
                          # pool_timeout = _TIMEOUT,
                          # pool_size = _POOL_SIZE)
    
    @classmethod
    def execute(cls, cmd, contain_key=False):
        conn = cls._POOL.connect()
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
        """Simple insert wrapper"""
        cmd = insert(table, data)
        cls.execute(cmd)

    @classmethod
    def select(cls, table, select_items, where_items=None):
        """Simple select wrapper"""
        cmd = select(
            table = table,
            select = select_items,
            where = where_items
        )
        return cls.execute(cmd)

    @classmethod
    def delete(cls, table, where_items):
        """Simple delete wrapper"""
        cmd = delete(
            table = table,
            where = where_items
        )
        cls.execute(cmd)

    @classmethod
    def update(cls, table, set_items, where_items=None):
        """Simple update wrapper"""
        cmd = update(
            table = table,
            set = set_items,
            where = where_items
        )
        cls.execute(cmd)


def main():
    db = ApeicDBConnManager()
    results = db.select('5f83a438d9145bb2_installed_apps', 'application')
    print results

if __name__ == '__main__':
    main()