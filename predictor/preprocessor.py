import itertools
from collections import Counter
from sklearn.feature_extraction import DictVectorizer

def some(items, predicate, key=None, func=None):
    if not items:
        return -1
    if not func and not key:
        for item in items:
            if predicate(item):
                return items.index(item)
    elif not func and key:
        for item in items:
            if predicate(item, key):
                return items.index(item)
    elif not key and func:
        for item in items:
            if predicate(func(item)):
                return items.index(item)
    else:
        for item in items:
            if predicate(func(item), key):
                return items.index(item)
    return -1

from math import radians, cos, sin, asin, sqrt
def get_distance(lng1, lat1, lng2, lat2):
    """ Calculate the great circle distance between two points on the earth (specified in decimal degrees)."""
    # convert decimal degrees to radians
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    # haversine formula
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km

class Preprocessor():

    def aggregate_sessions(self, sessions):
        return list(itertools.chain(*sessions))

    def split(self, data, ratio=0.8):
        split_index = int(len(data)*ratio)
        return data[:split_index], data[split_index:]

    def format(self, logs):
        pass


    def get_stay_points(self, logs):
        logs = filter(lambda x: x['activity'] in [u'STILL', u'TILTING', u'UNKNOWN'], logs)
        locations = list(set(map(lambda x: (x['latitude'], x['longitude']), logs)))
        stay_points = []
        for lat, lng in locations:
            index = some(stay_points, lambda x: get_distance(x[1], x[0], lng, lat) < 1)
            if index < 0:
            	stay_points.append((lat, lng))

        counts = []
        for lat, lng in locations:
            counts.append(some(stay_points, lambda x: get_distance(x[1], x[0], lng, lat) < 1))
        counter = Counter(counts)
        stay_points = filter(lambda x: counter[stay_points.index(x)] > 1, stay_points)
        return stay_points

    def to_weka(self, user, logs):
        stay_points = self.get_stay_points(logs)
        counter = Counter(map(lambda x: x['application'], logs))
        for c in counter:
            print c, counter[c], len(logs), counter[c] < len(logs)*0.5
        # used_apps = set(map(lambda x: x['application'], logs))
        used_apps = filter(lambda x: counter[x] < len(logs)*0.8 , set(map(lambda x: x['application'], logs)))
        # used_apps = filter(lambda x: counter[x] > 5, set(map(lambda x: x['application'], logs)))
        with open('data/%s.arff' % user, 'w') as f:
            f.write('@RELATION apeic\n')
            f.write('@ATTRIBUTE hour_of_day {%s}\n' % ', '.join(map(lambda x: str(x), xrange(6))))
            f.write('@ATTRIBUTE day_of_week {%s}\n' % ', '.join(map(lambda x: str(x + 1), xrange(7))))
            f.write('@ATTRIBUTE stay_point {%s, -1}\n' % ', '.join(map(lambda x: str(x), xrange(len(stay_points)))))
            f.write('@ATTRIBUTE activity {STILL, TILTING, UNKNOWN, ON_FOOT, ON_BICYCLE, IN_VEHICLE}\n')
            f.write('@ATTRIBUTE application {%s}\n' % ', '.join(used_apps))
            f.write('@data\n')
            for log in logs:
                if log['activity'] in [u'STILL', u'TILTING', u'UNKNOWN']:
                    index = some(stay_points, lambda x: get_distance(x[1], x[0], log['longitude'], log['latitude']) < 1)
                else:
                    index = -1
                if log['application'] not in used_apps:
                    continue
                f.write('%d, %d, %d, %s, %s\n' % (
                    log['datetime'].hour % 4, 
                    log['datetime'].isoweekday(), 
                    index, 
                    log['activity'], 
                    log['application']))


    def to_sklearn(self, logs):
        # (25.017881, 121.544028
        # 20.0, 0.0, u'STILL', 67L, 0.021973, 0, 0, 0L, 0.63, u'mong.moptt')
        # u'id', u'datetime', u'latitude', u'longitude', u'location_acc', u'speed', 
        # u'activity', u'activity_conf', u'illumination', 
        # u'mobile_connection', u'wifi_connection', u'wifi_ap_num', u'battery_power', u'application'
        X = []
        y = []
        i = 0
        last_stay_point = str(1)
        last_activity = logs[0]['activity']
        stay_points = []
        for log in logs[1:]:
        	instance = {}
        	instance['hour_of_day'] = log['datetime'].hour
        	instance['day_of_week'] = 'Y' if log['datetime'].isoweekday() in ['6', '7'] else 'N'
        	if log['activity'] in [u'STILL', u'TILTING', u'UNKNOWN']:
        		index = some(stay_points, lambda x: get_distance(x[1], x[0], log['longitude'], log['latitude']) < 1)
        		if index < 0:
        			stay_points.append((log['latitude'], log['longitude']))
        			instance['stay_point'] = str(len(stay_points) - 1)
        		else:
        			instance['stay_point'] = str(index)
        	else:
        		instance['stay_point'] = str(-1)

        	# instance['last_stay_point'] = last_stay_point
        	# if last_stay_point != instance['stay_point']:
        	# 	last_stay_point = instance['stay_point']
        	# instance['activity'] = log['activity']
        	# instance['last_activity'] = last_activity
        	# if last_activity != log['activity']:
        	# 	last_activity = log['activity']
        	# instance['illumination'] = log['illumination']
        	# instance['mobile_connection'] = log['mobile_connection']
        	# instance['wifi_connection'] = log['wifi_connection']
        	# instance['wifi_ap_num'] = log['wifi_ap_num']
        	instance['last_used_app'] = logs[i-1]['application']
        	X.append(instance)
        	y.append(log['application'])
        	i += 1
        vec = DictVectorizer()
        return vec.fit_transform(X).toarray(), y
