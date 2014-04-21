import itertools
import operator
import random
from sklearn.feature_extraction import DictVectorizer
from sklearn.naive_bayes import MultinomialNB

import datetime
import itertools
import operator
from collections import Counter, OrderedDict, defaultdict
from termcolor import colored
from sklearn.svm import SVC
from sklearn.utils import resample

class FeatureExtractor():

    def __init__(self):
        self.vectorizer = DictVectorizer()

    def generate_training_instances(self, logs):
        instances = []
        last_app = ''
        # for d, h, a, s, app in logs:
        for d, h, a, app in logs:
            instance = {}
            instance['day_of_week'] = d
            instance['hour_of_day'] = h
            instance['activity'] = a
            # instance['stay_point'] = s
            # instance['last_app'] = last_app
            instances.append(instance)
            last_app = app
        X = self.vectorizer.fit_transform(instances).toarray()
        y = map(lambda x: x[-1], logs)
        return X, y

    def transform(self, log):
        # d, h, a, s, last_app, app = log
        d, h, a, app = log
        instance = {}
        instance['day_of_week'] = d
        instance['hour_of_day'] = h
        instance['activity'] = a
        # instance['stay_point'] = s
        # instance['last_app'] = last_app
        x = self.vectorizer.transform(instance)
        return self.vectorizer.transform(instance).toarray()[0]


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
        self.triggers[session[0][-1]] += 1

        count = 0
        for x in session:
            app = self.ic.setdefault(x[-1], App(x[-1]))
            app.ocrs += 1.0
        for pkg_name in self.ic:
            app = self.ic.setdefault(pkg_name, App(pkg_name))
            app.crf = (1 if pkg_name in map(lambda x: x[-1], session) else 0) + 0.8*app.crf
        count += 1

        if len(session) > 1:
            app_pkg_names = [x[-1] for x in session]
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
                        successor = session[j][-1]
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

    def predict(self, session, ei, ranking, k=4):
        # results = {}
        # results = sorted(ei.iteritems(), key=operator.itemgetter(1), reverse=True)
        # candidates = map(lambda x: x[0], results[2:k+2])
        # if len(session) == 0:
        #     candidates = map(lambda x: x[0], results[2:k+2])
        #     return candidates, ranking

        ranking = defaultdict(int)
        for pkg_name in self.ic:
            ranking[pkg_name] = ei[pkg_name] if pkg_name in ei else 0

        int_context = map(lambda x: x[-1], session[:-1])
        for a in int_context:
            for pkg_name in self.ic:
                ranking[pkg_name] += self.ic[pkg_name].pred_influence[a]
        predicted_apps = sorted(ranking.iteritems(), key=operator.itemgetter(1), reverse=True)
        candidates = [x[0] for x in predicted_apps]        
        
        if len(int_context) > 0:
            if int_context[-1] in candidates:
                candidates.remove(int_context[-1])
        return candidates[:k], ranking

        predicted_apps = sorted(ranking.iteritems(), key=operator.itemgetter(1), reverse=True)
        candidates = [x[0] for x in predicted_apps[:k]]
        return candidates, ranking

def split(data, ratio=0.8):
    split_index = int(len(data)*ratio)
    return data[:split_index], data[split_index:]

def cdf(weights):
    total=sum(weights)
    result=[]
    cumsum=0
    for w in weights:
        cumsum+=w
        result.append(cumsum/total)
    return result

import bisect
def choice(population,weights):
    assert len(population) == len(weights)
    cdf_vals=cdf(weights)
    x=random.random()
    idx=bisect.bisect(cdf_vals,x)
    return population[idx]

def main():
    pass

if __name__ == '__main__':
    main()