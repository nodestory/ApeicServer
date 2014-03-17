import datetime
import itertools
import math
import MySQLdb

def get_logs(table, start_date, end_date):
    db = MySQLdb.connect(host="localhost", user="linzy", passwd="yatingcj6", db="apeic")
    cursor = db.cursor()
    cursor.execute('SELECT * FROM %s \
    	WHERE datetime BETWEEN "%s 00:00:00" AND "%s 23:59:59"' \
        % (table, start_date, end_date))
    return cursor.fetchall()

def get_logs(table, mode, proportion):	
	db = MySQLdb.connect(host="localhost", user="linzy", passwd="yatingcj6", db="apeic")
	cursor = db.cursor()

	if mode == 'ALL':
		cmd = 'SELECT * FROM %s' % table
	else:
		cmd = 'SELECT distinct date(datetime) FROM %s ORDER BY datetime' % table
		cursor.execute(cmd)
		dates = [x[0] for x in cursor.fetchall()]
		print dates
		split_point = int(math.floor(len(dates)*proportion))
		if mode == 'TRAIN':
			start_date = dates[:split_point][0]
			end_date = dates[:split_point][-1]
		if mode == 'TEST':
			start_date = dates[split_point:][0]
			end_date = dates[split_point:][-1]
		cmd = 'SELECT * FROM %s WHERE datetime BETWEEN "%s 00:00:00" AND "%s 23:59:59"' \
			% (table, start_date, end_date)
	cursor.execute(cmd)
	logs = cursor.fetchall()
	return logs

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

def sql2arff(table_name, mode, proportion):
	logs = get_logs(table_name, mode, proportion)
	segments = segment(logs)
	sessions = merge(segments)
	records = list(itertools.chain(*sessions))
	# instances = []
	# (17426L, datetime.datetime(2014, 3, 17, 10, 27, 36), 25.058175, 121.563289, \
	# 37.5, 0.0, 'TILTING', 100L, 0.015625, 0, 0, 1L, 0.98, 'com.spotify.mobile.android.ui')

	applications = list(set([x[-1] for x in records]))
	# date.weekday() or date.isoweekday()
	
	with open('%s.arff' % table_name, 'w') as f:
		f.write('@relation %s\n' % table_name)
		f.write('@attribute day_of_week {Mon, Tue, Wed, Thu, Friday, Sat, Sun}\n')
		f.write('@attribute hour_of_day {EARLY_MORNING, MORNING, AFTERNOON, EVENING, NIGHT}\n')
		f.write('@attribute activity {UNKNOWN, TILTING, STILL, IN_VEHICLE, ON_FOOT, ON_BICYCLE}\n')
		f.write('@attribute application {%s}\n' % ', '.join(applications))
		f.write('@data\n')
		for record in records:
			f.write('%s, %s, %s, %s\n' % (record[1].strftime('%a'), get_hour_of_day(record[1]), record[6], record[-1]))

def get_hour_of_day(datetime):
	hour = int(datetime.strftime('%H'))
	print 16 <= hour < 20 
	if 4 <= hour < 8:
		return 'EARLY_MORNING'
	elif 8 <= hour < 12:
		return 'MORNING'
	elif 12 <= hour < 16:
		return 'AFTERNOON'
	elif 16 <= hour < 20:
		return 'EVENING'
	else:
		return 'NIGHT'

def main():
	# ff3be9536122e83f_app_usage_logs
	# 7fab9970aff53ef4_app_usage_logs
	table_name = 'ff3be9536122e83f_app_usage_logs'
	sql2arff(table_name, 'ALL', 0.8)

if __name__ == '__main__':
	main()
