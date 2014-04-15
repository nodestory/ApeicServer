import itertools
import numpy
import operator
import random
from collections import Counter, OrderedDict, defaultdict

import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
sys.path.append('/home/linzy/Projects/ApeicServer/predictor')
from apeic_db_manager import ApeicDBHelper
# from preprocessor import Preprocessor


class App():
    def __init__(self, pkg_name):
        self.pkg_name = pkg_name
        self.ocrs = 0
        self.pred_co_ocrs = defaultdict(int)
        self.pred_influence = defaultdict(int)

class Preprocessor():

    def __init__(self, logs):        
        self.logs = logs


    def get_stay_points(self, logs):
        logs = filter(lambda x: x['activity'] in [u'STILL', u'TILTING', u'UNKNOWN'], logs)
        locations = list(set(map(lambda x: (x['latitude'], x['longitude']), logs)))
        locations = filter(lambda x: not x[0] == 0 or not x[1] == 0, locations)
        stay_points = []
        for lat, lng in locations:
            index = some(stay_points, lambda x: get_distance(x[1], x[0], lng, lat) < 0.1)
            if index < 0:
                stay_points.append((lat, lng))

        counts = []
        for lat, lng in locations:
            counts.append(some(stay_points, lambda x: get_distance(x[1], x[0], lng, lat) < 0.1))
        counter = Counter(counts)
        stay_points = filter(lambda x: counter[stay_points.index(x)] > 3, stay_points)
        # print stay_points
        return stay_points

    def get_stay_point(self, log, stay_points):
        if log['activity'] in [u'STILL', u'TILTING', u'UNKNOWN']:
            index = some(stay_points, lambda x: get_distance(x[1], x[0], log['longitude'], log['latitude']) < 0.1)
            if index < 0:
                # stay_points.append((log['latitude'], log['longitude']))
                result = str(len(stay_points) - 1)
            else:
                result = str(index)
        else:
            result = str(-1)
        return result

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

    def get_stay_point(self, log, stay_points):
        if log['activity'] in [u'STILL', u'TILTING', u'UNKNOWN']:
            index = some(stay_points, lambda x: get_distance(x[1], x[0], log['longitude'], log['latitude']) < 1)
            if index < 0:
                stay_points.append((log['latitude'], log['longitude']))
                result = str(len(stay_points) - 1)
            else:
                result = str(index)
        else:
            result = str(-1)
        return result


def aggregate_sessions(sessions):
    return list(itertools.chain(*sessions))

import random
import bisect
import collections

def cdf(weights):
    total=sum(weights)
    result=[]
    cumsum=0
    for w in weights:
        cumsum+=w
        result.append(cumsum/total)
    return result

def choice(population,weights):
    assert len(population) == len(weights)
    cdf_vals=cdf(weights)
    x=random.random()
    idx=bisect.bisect(cdf_vals,x)
    return population[idx]

def export_weight_file(file_name, weights):
    with open(file_name, 'w') as f:
        for w in weights:
            f.write('%s,%f\n' % (w, weights[w]))

def get_activity_code(activity_name):
    if activity_name in ['STILL', 'TILTING']:
        return 'STATIC'
    else:
        return activity_name
    # elif activity_name == 'ON_FOOT':
    #     return 'FT'
    # elif activity_name == 'ON_BICYCLE':
    #     return 'BI'
    # elif activity_name == 'ON_VEHICLE':
    #     return 'VH'
    # else:
    #     return 'UN'

# def get_stay_point_code(stay_point_index):



def main():
    db_helper = ApeicDBHelper()
    users = db_helper.get_users()
    for user in users:
        if user != '7fab9970aff53ef4':
            continue
        sessions = db_helper.get_sessions(user)
        sessions = map(lambda x: [x[0]], sessions)
        print len(sessions)
        logs = aggregate_sessions(sessions)
        apps = db_helper.get_used_apps(user)       
        
        days = Counter(map(lambda x: x['datetime'].isoweekday(), logs))
        nc = float(sum(days.values()))
        days = dict(map(lambda (k,v): (k, v/nc), days.iteritems()))
        print days
        export_weight_file('day.wgt.csv', days)

        hours = Counter(map(lambda x: x['datetime'].hour, logs))
        # hours = Counter(map(lambda x: x['datetime'].hour, filter(lambda x: x['datetime'].isoweekday() not in [6, 7], logs)))
        # for h in xrange(24):
        #     print hours[h],
        # print
        # hours = Counter(map(lambda x: x['datetime'].hour, filter(lambda x: x['datetime'].isoweekday() in [6, 7], logs)))
        # for h in xrange(24):
        #     print hours[h],
        # print
        nc = float(sum(hours.values()))
        hours = dict(map(lambda (k,v): ('%02d' % k, v/nc), hours.iteritems()))
        print hours
        export_weight_file('hour.wgt.csv', hours)
        

        activities = Counter(map(lambda x: get_activity_code(x['activity']), logs))
        print activities
        # nc = float(sum(activities.values()))
        # activities = dict(map(lambda (k,v): (k, v/nc), activities.iteritems()))
        # print activities
        export_weight_file('activity.wgt.csv', activities)

        preprocessor = Preprocessor(logs)
        stay_points = preprocessor.get_stay_points(logs)
        preprocessor.get_stay_point(logs[0], stay_points)
        stay_points = Counter(map(lambda x: preprocessor.get_stay_point(x, stay_points), logs))
        nc = float(sum(stay_points.values()))
        stay_points = dict(map(lambda (k,v): ('%02d' % int(k), v/nc), stay_points.iteritems()))
        print stay_points
        export_weight_file('stay_point.wgt.csv', stay_points)

        applications = Counter(map(lambda x: x['application'], logs))
        nc = float(sum(activities.values()))
        applications = dict(map(lambda (k,v): (k, v/nc), applications.iteritems()))
        print applications
        export_weight_file('application.wgt.csv', applications)


        used_apps = {}
        for session in sessions:
            for x in session:
                app = used_apps.setdefault(x['application'], App(x['application']))
                app.ocrs += 1.0

            for log in session[1:]:
                app_pkg_names = [x['application'] for x in session]
                for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
                    successors = []
                    indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]

                    indices.append(len(session))
                    for i in xrange(len(indices) - 1):
                        for j in xrange(indices[i] + 1, indices[i+1]):
                            successor = session[j]['application']
                            if successor not in successors:
                                app = used_apps.setdefault(successor, App(successor))
                                app.pred_co_ocrs[predecessor] += 1.0
                                successors.append(successor)
        for pkg_name in used_apps:
            successor = used_apps[pkg_name]
            for p in successor.pred_co_ocrs:
                predecessor = used_apps[p]
                successor.pred_influence[p] = successor.pred_co_ocrs[p]/predecessor.ocrs

        # lengths = map(lambda x: len(x), sessions)
        # lengths = Counter(lengths)
        # nc = float(sum(lengths))
        # lengths = dict(map(lambda (k,v): (k, v/nc), lengths.iteritems()))

        # for i in xrange(len(sessions)):
        #     # day, hour, activity, stay_point
        #     day = choice(days.keys(), days.values())
        #     hour = choice(hours.keys(), hours.values())
        #     activity = choice(activities.keys(), activities.values())
        #     stay_point = choice(stay_points.keys(), stay_points.values())
        #     application = random.choice(apps)

        #     session_len = choice(lengths.keys(), lengths.values())
        #     print session_len
        #     followers = []
        #     for i in xrange(session_len):
        #         successors = dict(map(lambda x: (x, used_apps[x].pred_influence[application]), apps))
        #         if sum(successors.values()) == 0:
        #             successor = random.choice(successors.keys())
        #         else: 
        #             successor = choice(successors.keys(), successors.values())
        #         followers.append(successor)
        #     print day, hour, activity, stay_point, application, ' '.join(followers)
        print
        break

        

if __name__ == '__main__':
    main()
