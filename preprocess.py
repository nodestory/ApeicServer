import MySQLdb

db = MySQLdb.connect(host="localhost", user="linzy", passwd="yatingcj6", db="apeic")
cursor = db.cursor()
cursor.execute("SHOW TABLES")
tables = [x[0] for x in cursor.fetchall()]
for table in tables:
    cursor.execute("SELECT COUNT(*) FROM %s" % table)
    count = cursor.fetchone()[0]
    print table, count

    sessions = []
    cursor.execute('SELECT id, application FROM %s' % table)
    records = cursor.fetchall()

    cursor.execute('SELECT distinct application FROM %s' % table)
    records = cursor.fetchall()
    for r in records:
        print r
    
    session = []
    for r in records:
        # id, datetime, lat, lng, location_acc, speed, activity, activity_conf, app = r
        id, app = r
        if app != 'null':
            session.append(r)
        else:
            if session:
                sessions.append(session)
            session = []

    for session in sessions[:5]:
        # print ' '.join([str(app[0]) for app in session])
        new_session = [session[0][1]]
        for id, app in session[1:]:
            if app != new_session[-1]:
                new_session.append(app)
        print '====='
        print '\n'.join(new_session)
        print 
        print '\n'.join([app for id, app in session])