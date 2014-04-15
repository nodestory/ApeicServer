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
        for d, h, a, s, app in logs:
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
        instance['stay_point'] = s
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
        if len(session) == 0:
            results = {}
            for a in ei.keys():
                # print a
                if a != 'reverse' and a != 'key':
                    results[a] = ei[a]/2**self.ic[a].crf
            results = sorted(results.iteritems(), key=operator.itemgetter(1), reverse=True)
            results = sorted(ei.iteritems(), key=operator.itemgetter(1), reverse=True)
            # for a in ei:
            #     ranking[a] = ei[a]
            candidates = map(lambda x: x[0], results[2:k+2])
            # if last not in candidates:
            #     candidates = map(lambda x: x[0], results[2:k+1]) + [last]
            return candidates, ranking

        # ranking = defaultdict(int)
        for pkg_name in self.ic:
            # ranking[pkg_name] = ei[pkg_name] if pkg_name in ei else 0
            ranking[pkg_name] += self.ic[pkg_name].pred_influence[session[-1][-1]]
            # ranking[pkg_name] += self.ic[pkg_name].pred_influence[session[-1][-1]] \
            #                         + ei[pkg_name] if pkg_name in ei.keys() else 0

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
        return candidates, ranking

def split(data, ratio=0.8):
    split_index = int(len(data)*ratio)
    return data[:split_index], data[split_index:]

def get_pairs(apps):
    # pair_num = random.choice(range(3))
    pair_num = 3
    pairs = []
    for i in xrange(pair_num):
        pair = random.sample(apps, 2)
        pairs.append(pair)
    return pairs

def generate_next_app(applications, used_apps, pairs):
    predecessor = random.choice(used_apps)
    for p, s in pairs:
        if predecessor == p and random.choice(range(10)) > 3:
            return s
    if len(used_apps) > 2:
        if random.choice(range(10)) > 1:
            return random.choice(used_apps[:-1])
        else:
            return random.choice(applications)
    else:
        if random.choice(range(10)) > 5:
            return random.choice(used_apps)
        else:
            return random.choice(applications)


class SessionGenerator():

    def __init__(session_num=100, app_num=20):
        self.session_num = session_num
        self.app_num = app_num

    def generate(self):
        causality = _generate_causality()

        for i in xrange(session_num):
            used_apps = []
            session = []
            application = random.choice(applications)
            used_apps.append(application)
            log = logs[i][:-1] + [application]
            session.append(log)
            for j in xrange(random.choice(range(1, 5))):
                application = generate_next_app(causality, used_apps)
                used_apps.append(application)
                log = logs[i][:-1] + [application]
                session.append(log)
            sessions.append(session)
        
    def _init_session(self):
        with open('app_usage_logs.flat', 'r') as f:
            lines = f.readlines()
            logs = map(lambda x: x.strip().split(), lines)
            applications = map(lambda x: x[-1], logs)
            self.app_num = len(applications)

    def _generate_causality(self):
        causality = {}
        for i in xrange(len(self.app_num)):
            causality[hex(i)] = App(hex(i))

        for s in causality:
            count = 0
            cdf = 0
            for p in causality:
                count += 1
                if count < len(applications) and cdf < 1:
                    influence = random.uniform(0.0001, 1 - cdf)
                    causality[s].pred_influence[p] = influence
                    cdf += influence
                else:
                    influence = max(1 - cdf, 0.0001)
                    causality[s].pred_influence[p] = influence
        return causality

    def _generate_successor(self):
        candidates = defaultdict(int)

        for p in used_apps:
            for s in causality:
                candidates[s] += causality[s].pred_influence[p]

        successor = choice(candidates.keys(), candidates.values())
        while successor == p:
            successor = choice(candidates.keys(), candidates.values())
        return successor


def generate_causality(applications):
    causality = {}
    for app in applications:
        causality[app] = App(app)

    # for i in xrange(len(applications)):
    #     cdf = 0
    #     for j in xrange(len(applications)):
    #         if i != len(applications) - 1:
    #             influence = random.uniform(0.0001, max(1 - cdf, 0.7))
    #             causality[applications[i]].pred_influence[applications[j]] = influence
    #             cdf += influence
    #         else:
    #             influence = 1 - cdf
    #             causality[applications[i]].pred_influence[applications[j]] = influence

    for s in causality:
        count = 0
        cdf = 0
        for p in causality:
            count += 1
            if count < len(applications) and cdf < 1:
                influence = random.uniform(0.0001, 1 - cdf)
                causality[s].pred_influence[p] = influence
                cdf += influence
            else:
                influence = max(1 - cdf, 0.0001)
                causality[s].pred_influence[p] = influence

    # for s in causality:
    #     print s
    #     for p in causality:
    #         print p, causality[s].pred_influence[p]
    #     print sum(causality[s].pred_influence.values())
    #     print
    return causality

def generate_next_app(causality, used_apps):
    candidates = defaultdict(int)

    for p in used_apps:
        # p = used_apps[-1]
        for s in causality:
            candidates[s] += causality[s].pred_influence[p]

    winner = choice(candidates.keys(), candidates.values())
    while winner == p:
        winner = choice(candidates.keys(), candidates.values())
    return winner

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
    # start generating sessions
    for i in xrange(1):
        with open('app_usage_logs.flat', 'r') as f:
            lines = f.readlines()
            logs = map(lambda x: x.strip().split(), lines)
            applications = map(lambda x: x[-1], logs)

        causality = generate_causality(applications)

        sessions = []
        for i in xrange(len(logs)):
            used_apps = []
            session = []
            application = random.choice(applications)
            used_apps.append(application)
            log = logs[i][:-1] + [application]
            session.append(log)
            for j in xrange(random.choice(range(1, 5))):
                application = generate_next_app(causality, used_apps)
                used_apps.append(application)
                log = logs[i][:-1] + [application]
                session.append(log)
            sessions.append(session)
        # finish generating sessions


        training_sessions, testing_sessions = split(sessions)

        extractor = FeatureExtractor()
        training_logs = list(itertools.chain(*training_sessions))
        X, y = extractor.generate_training_instances(training_logs)
        nb = MultinomialNB()
        nb_predictor = nb.fit(X, y)

        predictor = ApeicPredictor()
        for session in training_sessions:
            predictor.update(session)

        hits = 0.0
        misses = 0.0
        last_app = ''
        for session in testing_sessions:
            ranking = defaultdict(int)
            for i in xrange(len(session)):
                log = session[i][:-1] + [last_app] + [session[i][-1]]
                instance = extractor.transform(log)
                ei = dict(zip(nb_predictor.classes_, nb_predictor.predict_proba(instance)[0]), \
                    key=operator.itemgetter(1), reverse=True)
                candidates, ranking = predictor.predict(session[:i], ei, ranking, 4)
                last_app = session[i][-1]
                if session[i][-1] in candidates:
                    hits += 1.0
                else:
                    misses += 1.0
            predictor.update(session)

        acc = (hits)/(hits + misses)
        print acc, hits, misses


        hits = 0.0
        misses = 0.0
        last_app = ''
        for log in list(itertools.chain(*testing_sessions)):
            log = log[:-1] + [last_app] + [log[-1]]
            instance = extractor.transform(log)
            ranking = sorted(zip(nb_predictor.classes_, nb_predictor.predict_proba(instance)[0]), \
                                key=operator.itemgetter(1), reverse=True)
            candidates = map(lambda x: x[0], ranking[:4])
            last_app = log[-1]
            if log[-1] in candidates:
                hits += 1.0
            else:
                misses += 1.0

        acc = hits/(hits + misses)
        print acc, hits, misses

        hits = 0.0
        misses = 0.0
        used_applications = map(lambda x: x[-1], list(itertools.chain(*training_sessions)))
        counter = Counter(used_applications)
        candidates = map(lambda x: x[0],  counter.most_common(4))
        for log in list(itertools.chain(*testing_sessions)):
            if log[-1] in candidates:
                hits += 1.0
            else:
                misses += 1.0
        acc = hits/(hits + misses)
        print acc, hits, misses

        print


if __name__ == '__main__':
    main()