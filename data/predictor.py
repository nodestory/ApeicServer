import itertools
import math
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

    def generate_training_instances(self, logs, l=False):
        instances = []
        last_app = ''
        # for d, h, a, s, app in logs:
        for d, h, a, app in logs:
            instance = {}
            instance['day_of_week'] = d
            instance['hour_of_day'] = h
            instance['activity'] = a
            # instance['stay_point'] = s
            # if l:
            instance['last_app'] = last_app
            instances.append(instance)
            # last_app = app
        X = self.vectorizer.fit_transform(instances).toarray()
        y = map(lambda x: x[-1], logs)
        return X, y

    def transform(self, log, last_app, l=False):
        # d, h, a, s, last_app, app = log
        d, h, a, app = log
        instance = {}
        instance['day_of_week'] = d
        instance['hour_of_day'] = h
        instance['activity'] = a
        # instance['stay_point'] = s
        # if l:
        instance['last_app'] = last_app
        x = self.vectorizer.transform(instance)
        return self.vectorizer.transform(instance).toarray()[0]


class App():
    def __init__(self, pkg_name):
        self.pkg_name = pkg_name
        self.ocrs = 0
        self.pred_co_ocrs = defaultdict(int)
        self.pred_influence = defaultdict(int)

        self.crf = 0

class LUPredictor():

    def __init__(self, mu):
        self.mu = mu
        self.vectorizer = DictVectorizer()

    def train(self, training_data):
        nb = MultinomialNB()

        instances = []
        for i in xrange(1, len(training_data)):
            instance = {}
            instance['lu_1'] = training_data[i-1][-1]
            instances.append(instance)
        X = self.vectorizer.fit_transform(instances).toarray()
        y = map(lambda x: x[-1], training_data[1:])
        self.lu_predictor = nb.fit(X, y)

        instances = []
        for i in xrange(2, len(training_data)):
            instance = {}
            instance['lu_2'] = training_data[i-2][-1]
            instances.append(instance)
        X = self.vectorizer.fit_transform(instances).toarray()
        y = map(lambda x: x[-1], training_data[2:])
        self.lu2_predictor = nb.fit(X, y)

    def predict(self, lu2, lu1, k=4):
        vectorizer = DictVectorizer()
        instance = {}
        instance['lu_1'] = lu1
        x = self.vectorizer.transform(instance).toarray()[0]
        lu_result = zip(self.lu_predictor.classes_, self.lu_predictor.predict_proba(x)[0])

        instance = {}
        instance['lu_2'] = lu2
        x = self.vectorizer.transform(instance).toarray()[0]
        lu2_result = zip(self.lu2_predictor.classes_, self.lu2_predictor.predict_proba(x)[0])

        result = dict(map(lambda x, y: (x[0], self.mu*x[1]+(1 - self.mu)*y[1]), lu_result, lu2_result))
        ranking = sorted(result.iteritems(), key=operator.itemgetter(1), reverse=True)
        candidates = map(lambda x: x[0], ranking[:k])
        return candidates

class ApeicPredictor():

    def __init__(self):
        self.triggers = defaultdict(int)
        self.ec = {}
        self.ic = {}

    def train(self, sessions):
        # environmental context
        temp = map(lambda x: x[:1], sessions)
        logs = list(chain(*temp))
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
            # """
            app_pkg_names = [x[-1] for x in session]
            for predecessor in list(OrderedDict.fromkeys(app_pkg_names)):
                successors = []
                indices = [i for i, x in enumerate(app_pkg_names) if x == predecessor]
                indices.append(len(session))
                for i in xrange(len(indices) - 1):
                    for j in xrange(indices[i] + 1, indices[i+1]):
                        successor = session[j][-1]
                        if successor not in successors:
                            app = self.ic.setdefault(successor, App(successor))
                            app.pred_co_ocrs[predecessor] += 1.0

                            successors.append(successor)
                    instance = self.ic.setdefault(predecessor, App(predecessor))
                    instance.pred_co_ocrs[predecessor] += 1.0
            # """

            """
            for i in xrange(1, len(session)):
              successor = session[i][-1]
              app = self.ic.setdefault(successor, App(successor))
              app.pred_co_ocrs[session[i-1][-1]] += 1.0
            """

        for pkg_name in self.ic:
            successor = self.ic[pkg_name]
            for p in successor.pred_co_ocrs:
                predecessor = self.ic[p]
                # TODO: perform experiments with differnect measures
                # math.log(predecessor.ocrs)
                # predecessor.crf*
                successor.pred_influence[p] = successor.pred_co_ocrs[p]/predecessor.ocrs

    def predict(self, session, ei, terminator, k=4):
        ranking = defaultdict(int)
        for pkg_name in self.ic:
            ranking[pkg_name] = ei[pkg_name] if pkg_name in ei else 0

        int_context = map(lambda x: x[-1], session[:-1])
        N = float(len(set(int_context)))
        for a in set(int_context):
            for pkg_name in self.ic:
                ranking[pkg_name] += self.ic[pkg_name].pred_influence[a]/N

        # weight = defaultdict(lambda: 1)
        l = len(int_context)
        for app in set(filter(lambda x: x != int_context[-1], int_context)):
            n = int_context.count(app)
            first_index = (x for x in [y for y in enumerate(int_context)] if x[1] == app).next()[0]
            last_index = (x for x in reversed([y for y in enumerate(int_context)]) if x[1] == app).next()[0]
            lamb = math.ceil((last_index - first_index + 1)/float(n))
            x = int(l + 1 - last_index)
            prob = (lamb**x)*math.exp(-lamb)/math.factorial(x)
            ranking[app] += prob
        #     weight[app] = prob


        # for a in set(int_context):
        #     for pkg_name in self.ic:
        #         ranking[pkg_name] += weight[a]*self.ic[pkg_name].pred_influence[a]/N

        candidates = sorted(ranking, key=ranking.get, reverse=True)
        

        if len(int_context) > 0:
            pass
            # if int_context[-1] in candidates:
            #     candidates.remove(int_context[-1])
        return candidates[:k]

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