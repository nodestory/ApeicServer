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
    for session in sessions:
        print ' '.join([str(app[0]) for app in session])