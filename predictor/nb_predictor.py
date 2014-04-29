from collections import Counter, defaultdict
import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper
from predictor import Predictor
from preprocessor import Preprocessor

import itertools
import logging
import math
import operator
from collections import defaultdict, Counter, OrderedDict
from termcolor import colored
from sklearn.feature_extraction import DictVectorizer
from sklearn.naive_bayes import MultinomialNB


class NBPredictor(Predictor):

    def __init__(self):
        pass

    def train(self, training_data):
        pass

    def predict(self, data, k=4):
        pass


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

class FeatureExtractor():

    def __init__(self):
        self.vectorizer = DictVectorizer()
        # TODO: get stay_points

    def generate_training_instances(self, logs):
        instances = []
        stay_points = []
        last_used_app = ''
        for i in xrange(len(logs)):
            instance = {}
            instance['hour_of_day'] = logs[i]['datetime'].hour
            instance['day_of_week'] = logs[i]['datetime'].isoweekday()
            # instance['day_of_week'] = 'Y' if logs[i]['datetime'].isoweekday() in ['6', '7'] else 'N'
            # instance['activity'] = logs[i]['activity']
            if logs[i]['activity'] in [u'STILL', u'TILTING']:
                instance['activity'] = 'S'
            else:
                instance['activity'] = logs[i]['activity']
            instance['activity'] = logs[i]['activity']
            # if logs[i]['activity_conf'] > 70:
            #     instance['activity'] = logs[i]['activity']
            # else:
            #     instance['activity'] = 'UNKNOWN'

            # if logs[i]['activity_conf'] <= 30:
            #     instance['activity_conf'] = 'L'
            # elif 30 < logs[i]['activity_conf'] < 70:
            #     instance['activity_conf'] = 'M'
            # else:
            #     instance['activity_conf'] = 'H'
            if logs[i]['activity'] in [u'STILL', u'TILTING', u'UNKNOWN']:
                index = some(stay_points, lambda x: get_distance(x[1], x[0], logs[i]['longitude'], logs[i]['latitude']) < 0.5)
                if index < 0:
                    stay_points.append((logs[i]['latitude'], logs[i]['longitude']))
                    instance['stay_point'] = str(len(stay_points) - 1)
                else:
                    instance['stay_point'] = str(index)
            else:
                instance['stay_point'] = str(-2)
                # instance['stay_point'] = logs[i]['activity']
            # instance['speed'] = logs[i]['speed']
            # instance['illumination'] = logs[i]['illumination']
            # instance['mobile_connection'] = logs[i]['mobile_connection']
            # instance['wifi_connection'] = logs[i]['wifi_connection']
            if logs[i]['mobile_connection'] == '1' or logs[i]['wifi_connection'] == '1':
                instance['c'] = 'Y'
            else:
                instance['c'] = 'N'
            # instance['wifi_ap_num'] = logs[i]['wifi_ap_num']
            # instance['last_used_app'] = last_used_app
            instances.append(instance)
            last_used_app = logs[i]['application']
        # print len(stay_points)
        self.stay_points = stay_points
        X = self.vectorizer.fit_transform(instances).toarray()
        # y = map(lambda x: x['application'], logs[1:])
        y = map(lambda x: x['application'], logs)
        return X, y

    def transform(self, last_used_app, log):
        instance = {}
        instance['hour_of_day'] = log['datetime'].hour
        instance['day_of_week'] = log['datetime'].isoweekday()
         # 'Y' if log['datetime'].isoweekday() in ['6', '7'] else 'N'
        if log['activity'] in [u'STILL', u'TILTING']:
            instance['activity'] = 'S'
        else:
            instance['activity'] = log['activity']
        instance['activity'] = log['activity']
        # if log['activity_conf'] > 70:
        #         instance['activity'] = log['activity']
        # else:
        #     instance['activity'] = 'UNKNOWN'

        # if log['activity_conf'] <= 30:
        #         instance['activity_conf'] = 'L'
        # elif 30 < log['activity_conf'] < 70:
        #     instance['activity_conf'] = 'M'
        # else:
        #     instance['activity_conf'] = 'H'
        if log['activity'] in [u'STILL', u'TILTING', u'UNKNOWN']:
            index = some(self.stay_points, lambda x: get_distance(x[1], x[0], log['longitude'], log['latitude']) < 0.5)
            if index < 0:
                instance['stay_point'] = str(len(self.stay_points) - 1)
            else:
                instance['stay_point'] = str(index)
        else:
            instance['stay_point'] = str(-2)
            # instance['stay_point'] = log['activity']
        # instance['last_used_app'] = last_used_app
        # instance['illumination'] = log['illumination']
        # instance['mobile_connection'] = log['mobile_connection']
        # instance['wifi_connection'] = log['wifi_connection']
        if log['mobile_connection'] == '1' or log['wifi_connection'] == '1':
            instance['c'] = 'Y'
        else:
            instance['c'] = 'N'
        # instance['speed'] = log['speed']
        # instance['wifi_ap_num'] = log['wifi_ap_num']
        x = self.vectorizer.transform(instance)
        return self.vectorizer.transform(instance).toarray()[0]

# def split(sessions, ratio=0.8):
#     split_index = int(len(sessions)*ratio)
#     return sessions[:split_index], sessions[split_index:]

import datetime
def split(sessions, ratio=0.8):
    # start_date = sessions[0][0]['datetime']
    # midnight = datetime.time(0)
    # start_date = datetime.datetime.combine(start_date.date(), midnight)
    # end_date = start_date + datetime.timedelta(days=21)

    # split_index = int(len(sessions)*ratio)
    # for i in xrange(len(sessions)):
    #     if (sessions[i][0]['datetime'] - end_date).days > 0:
    #         split_index = i
    #         break
    
    # print split_index, len(sessions) - split_index
    # return sessions[:split_index], sessions[split_index:]

    # print (sessions[-1][-1]['datetime'] - sessions[0][0]['datetime']).days
    start_date = sessions[0][0]['datetime']
    midnight = datetime.time(0)
    start_date = datetime.datetime.combine(start_date.date(), midnight)
    end_date = start_date + datetime.timedelta(days=21)

    split_index = int(len(sessions)*ratio)
    # return sessions[:split_index], sessions[split_index:]
    for i in xrange(len(sessions)):
        if (sessions[i][0]['datetime'] - end_date).days > 0:
            split_index = i
            break

    test_sessions = sessions[split_index:]
    start_date = test_sessions[0][0]['datetime']
    midnight = datetime.time(0)
    start_date = datetime.datetime.combine(start_date.date(), midnight)
    end_date = start_date + datetime.timedelta(days=7)
    tt = -1
    for i in xrange(len(test_sessions)):
        if (test_sessions[i][0]['datetime'] - end_date).days > 0:
            tt = i
            break
    if tt != -1:
        test_sessions = test_sessions[:tt]

    # print split_index, len(sessions) - split_index
    return sessions[:split_index], sessions[split_index:]
    # return sessions[:split_index], test_sessions


def aggregate_sessions(sessions):
    return list(itertools.chain(*sessions))

def main():
    hits = 0.0
    misses = 0.0
    db_helper = ApeicDBHelper()
    users = db_helper.get_users()

    accuracies = []
    for user in users:
        if user == '11d1ef9f845ec10e':
            continue
        print colored(user, attrs=['blink'])

        sessions = db_helper.get_sessions(user)

        last = sessions[0][-1]['application']
        test = [sessions[0]]
        for s in sessions[1:]:
            if s[0]['application'] == last:
                if s[1:]:
                    test.append(s[1:])
            else:
                test.append(s)
            last = s[-1]['application']
        training_sessions, testing_sessions = split(test, 0.8)

        training_sessions, testing_sessions = split(sessions, 0.8)
        logs = aggregate_sessions(training_sessions)

        extractor = FeatureExtractor()
        X, y = extractor.generate_training_instances(logs)
        nb = MultinomialNB()
        predictor = nb.fit(X, y)

        last_used_app = ''
        for session in testing_sessions:
            for log in session:
                # if log['application'] in ['com.android.settings', \
                #     'com.android.packageinstaller', 'com.htc.android.worldclock', 'com.android.systemui']:
                #     continue
                
                instance = extractor.transform(last_used_app, log)
                ranking = sorted(zip(predictor.classes_, predictor.predict_proba(instance)[0]), \
                                    key=operator.itemgetter(1), reverse=True)
                candidates = map(lambda x: x[0], ranking[:4])
                if log['application'] in candidates:
                    hits += 1.0
                else:
                    misses += 1.0
                last_used_app = log['application'] 

        # order = 3
        # tesiting_sessions = filter(lambda x: len(x) > order, tesiting_sessions)
        # if len(tesiting_sessions) == 0:
        #     continue
        # for session in tesiting_sessions:
        #     log = session[order]
        #     if log['application'] in [ u'com.android.systemui', u'com.htc.launcher', u'android', \
        #             u'com.tul.aviate', u'com.android.settings']:
        #             continue
        #     instance = extractor.transform(log)
        #     ranking = sorted(zip(predictor.classes_, predictor.predict_proba(instance)[0]), \
        #         key=operator.itemgetter(1), reverse=True)
        #     candidates = map(lambda x: x[0], ranking[:4])
        #     if log['application'] in candidates:
        #         hits += 1.0
        #     else:
        #         misses += 1.0        

        acc = hits/(hits + misses)
        accuracies.append(acc)
        print acc, hits, misses
        # break
    print sum(accuracies)/len(accuracies)

if __name__ == '__main__':
    main()