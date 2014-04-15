import datetime
import itertools
import operator
from collections import Counter, OrderedDict, defaultdict
from termcolor import colored
from preprocessor import Preprocessor
from predictor import Predictor
from nb_predictor import *

class App():
    def __init__(self, pkg_name):
        self.pkg_name = pkg_name
        self.ocrs = 0
        self.pred_co_ocrs = defaultdict(int)
        self.pred_influence = defaultdict(int)

        self.crf = 0

class ApeicPredictor():

    def __init__(self):
        self.triggers = defaultdict(int)
        self.ec = {}
        self.ic = {}

    def train(self, sessions):
        # environmental context
        logs = aggregate_sessions(sessions)
        extractor = FeatureExtractor()
        X, y = extractor.generate_training_instances(logs)
        nb = MultinomialNB()
        nb_predictor = nb.fit(X, y)

        # interactional context
        for session in sessions:
            self.update(session)

    def update(self, session):                  
        self.triggers[session[0]['application']] += 1

        count = 0
        for x in session:
            app = self.ic.setdefault(x['application'], App(x['application']))
            app.ocrs += 1.0
        for pkg_name in self.ic:
            app = self.ic.setdefault(pkg_name, App(pkg_name))
            app.crf = (1 if pkg_name in map(lambda x: x['application'], session) else 0) + 0.8*app.crf
        count += 1

        if len(session) > 1:
            app_pkg_names = [x['application'] for x in session]
            for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
                successors = []
                indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]
                # if len(indices) == 1:
                #   if i < len(session) - 1:
                #       successor = session[i+1]['application']
                #       app = self.ic.setdefault(successor, App(successor))
                #       app.pred_co_ocrs[predecessor] += 1.0
                #   continue

                indices.append(len(session))
                for i in xrange(len(indices) - 1):
                    for j in xrange(indices[i] + 1, indices[i+1]):
                        successor = session[j]['application']
                        if successor not in successors:
                            app = self.ic.setdefault(successor, App(successor))
                            app.pred_co_ocrs[predecessor] += 1.0
                            successors.append(successor)

            # for i in xrange(1, len(session)):
            #   successor = session[i]['application']
            #   app = self.ic.setdefault(successor, App(successor))
            #   app.pred_co_ocrs[session[i-1]['application']] += 1.0

        for pkg_name in self.ic:
            successor = self.ic[pkg_name]
            for p in successor.pred_co_ocrs:
                predecessor = self.ic[p]
                # TODO: perform experiments with differnect measures
                successor.pred_influence[p] = successor.pred_co_ocrs[p]/predecessor.ocrs

    def predict(self, session, last, ei, k=4):
        if len(session) == 0:
            results = {}
            for a in ei.keys():
                # print a
                if a != 'reverse' and a != 'key':
                    results[a] = ei[a]/2**self.ic[a].crf
            results = sorted(results.iteritems(), key=operator.itemgetter(1), reverse=True)
            results = sorted(ei.iteritems(), key=operator.itemgetter(1), reverse=True)
            candidates = map(lambda x: x[0], results[2:k+2])
            if last not in candidates:
                candidates = map(lambda x: x[0], results[2:k+1]) + [last]
            return candidates

        ranking = defaultdict(int)
        for pkg_name in self.ic:
            ranking[pkg_name] = ei[pkg_name] if pkg_name in ei else 0
            ranking[pkg_name] = self.ic[pkg_name].pred_influence[session[-1]['application']]
            ranking[pkg_name] = self.ic[pkg_name].pred_influence[session[-1]['application']] \
                                    + ei[pkg_name] if pkg_name in ei.keys() else 0

            # TODO: take recency into consideration
            # if pkg_name in map(lambda x: x['application'], session[-4:-1]):
            #   ranking[pkg_name] += 1
            # if pkg_name in map(lambda x: x['application'], session[:-4]):
            #   ranking[pkg_name] -= 1
            # temp = map(lambda x: x['application'], session[:-1])
            # if pkg_name in temp:
                # print temp.index(pkg_name), len(temp), temp.index(pkg_name)/float(len(temp))
                # ranking[pkg_name] += 0.3 - 0.05*(len(temp) - temp.index(pkg_name))
                # ranking[pkg_name] += 1
        
        predicted_apps = sorted(ranking.iteritems(), key=operator.itemgetter(1), reverse=True)
        candidates = [x[0] for x in predicted_apps[:k]]
        return candidates


def split(sessions, ratio=0.8):
    # print (sessions[-1][-1]['datetime'] - sessions[0][0]['datetime']).days
    start_date = sessions[0][0]['datetime']
    midnight = datetime.time(0)
    start_date = datetime.datetime.combine(start_date.date(), midnight)
    end_date = start_date + datetime.timedelta(days=21)

    split_index = int(len(sessions)*ratio)
    # for i in xrange(len(sessions)):
    #   if (sessions[i][0]['datetime'] - end_date).days > 0:
    #       split_index = i
    #       break
    
    # print split_index, len(sessions) - split_index
    return sessions[:split_index], sessions[split_index:]

import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper
def main():
    hits = 0.0
    misses = 0.0
    db_helper = ApeicDBHelper()
    users = db_helper.get_users()
    # users = ['475f258ecc566658']
    accuracies = []
    trigger_errors = []
    for user in users:
        if user == '11d1ef9f845ec10e':
            continue
        sessions = db_helper.get_sessions(user)
        training_sessions, testing_sessions = split(sessions, 0.8)
        logs = aggregate_sessions(training_sessions)
        extractor = FeatureExtractor()
        X, y = extractor.generate_training_instances(logs)
        nb = MultinomialNB()
        nb_predictor = nb.fit(X, y)

        sessions = db_helper.get_sessions(user)
        print colored(user, attrs=['blink'])
        
        predictor = ApeicPredictor()
        for session in training_sessions:
            predictor.update(session)
        lengths = map(lambda x: len(x), training_sessions)
        avg = sum(lengths)/float(len(lengths))
        # print avg, len(db_helper.get_used_apps(user))


        # hits = 0.0
        # misses = 0.0
        new = 0.0
        trigger_misses = 0.0
        error = defaultdict(int)
        last_session = testing_sessions[0]
        last = ''
        for session in testing_sessions:
            # print '\n'.join(map(lambda x: x['application'], session))
            for i in xrange(len(session)):
                # print session[i]['activity'], session[i]['activity_conf']
                # if session[i]['application'] in ['com.android.settings', \
                #   'com.android.packageinstaller', 'com.htc.android.worldclock', 'com.android.systemui']:
                #   continue
                instance = extractor.transform(last, session[i])
                ei = dict(zip(nb_predictor.classes_, nb_predictor.predict_proba(instance)[0]), \
                    key=operator.itemgetter(1), reverse=True)
                candidates = predictor.predict(session[:i], last_session[-1]['application'], ei, 5)
                if session[i]['application'] in candidates:
                    hits += 1.0
                else:
                    misses += 1.0
                    if session[i]['application'] not in ei:
                        new += 1.0
                    if i == 0:
                        # print '\t', session[i]['application']
                        trigger_misses += 1.0
                        error[session[i]['application']] += 1
            # print
            last_session = session
            last = session[0]['application']
            predictor.update(session)

            # logs = aggregate_sessions(training_sessions + [session])
            # extractor = FeatureExtractor()
            # X, y = extractor.generate_training_instances(logs)
            # nb = MultinomialNB()
            # nb_predictor = nb.fit(X, y)

        acc = (hits)/(hits + misses)
        accuracies.append(acc)
        trigger_errors.append(trigger_misses/misses if misses > 0 else 0)
        print acc, trigger_misses/misses if misses > 0 else 0, trigger_misses, new, misses, (hits + misses)
        # print error
        # break
    print sum(accuracies)/len(accuracies), sum(trigger_errors)/len(trigger_errors)


if __name__ == '__main__':
    main()
