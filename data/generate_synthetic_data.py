import math
import os
import random
from collections import defaultdict
from itertools import groupby
from operator import itemgetter
from selector import choice, choice_by_distr

import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper

      
# TODO  
from tt import *          
def format(log):
    day = log['datetime'].isoweekday()
    hour = log['datetime'].hour
    if log['activity'] in ['STILL', 'TILTING']:
        activity = 'STATIC'
    else:
        activity = log['activity']
    application = log['application']
    return day, hour, activity, application

class AppDistr(object):

    def __init__(self, ocrs, day_distr, hour_distr, activity_distr):
        self.ocrs = ocrs
        self.ocr_porb = 0
        self.day_distr = day_distr
        self.hour_distr = hour_distr
        self.activity_distr = activity_distr

class SessionGenerator():

    def __init__(self, app_num=15, session_num=400):
        self.app_num = app_num
        self.session_num = session_num

        app_distrs = self._get_app_distrs()
        self.app_distrs = random.sample(app_distrs, app_num)

        self.session_len_distr = self._get_session_len_distr()

        self.app_causality = self._create_app_causality()

    def _get_app_distrs(self):
        app_traces = self._get_app_traces()

        app_distrs = []
        for application, traces in groupby(app_traces, lambda x: x[-1]):
            # day
            ocrs = 0
            cluster = list(traces)
            day_distr = defaultdict(lambda: 0.00001)
            for k, v in groupby(cluster, lambda x: x[0]):
                day_distr[k] += sum(1 for _ in v)
                ocrs += day_distr[k]
            n = float(sum(day_distr.values()))
            for d in day_distr:
                day_distr[d] /= n

            # hour
            hour_distr = defaultdict(lambda: 0.00001)
            for k, v in groupby(cluster, lambda x: x[1]):
                hour_distr[k] += sum(1 for _ in v)
            n = float(sum(hour_distr.values()))
            for h in hour_distr:
                hour_distr[h] /= n

            # activity
            activity_distr = defaultdict(lambda: 0.00001)
            for k, v in groupby(cluster, lambda x: x[2]):
                activity_distr[k] += sum(1 for _ in v)
            n = float(sum(activity_distr.values()))
            for a in activity_distr:
                activity_distr[a] /= n

            app_distrs.append((application, AppDistr(ocrs, day_distr, hour_distr, activity_distr)))

        n = sum(map(lambda x: x[1].ocrs, app_distrs))
        for app, distr in app_distrs:
            distr.ocr_porb = distr.ocrs/n
        return app_distrs

    def _get_app_traces(self):
        helper = ApeicDBHelper()

        logs = []
        users = helper.get_users()
        for user in users:
            logs.extend(helper.get_logs(user))

        logs = map(lambda x: format(x), logs)
        app_traces = sorted(logs, key=itemgetter(-1))
        return app_traces

    def _get_session_len_distr(self):
        """
        helper = ApeicDBHelper()

        users = helper.get_users()
        results = []
        for user in users:
            print user
            sessions = helper.get_sessions(user)
            # counter = Counter(map(lambda session: len(set(map(lambda x: x['application'], session))), sessions))
            counter = Counter(map(lambda s: len(s), sessions))
            results.append(counter)
            print counter
        
        len_dist = reduce(add, (Counter(dict(x)) for x in results))
        print len_dist
        return len_dist
        """
        # {1: 1302, 2: 577, 3: 216, 4: 121, 5: 34, 6: 20, 7: 8, 8: 7, 9: 4, 12: 1, 16: 1}
        # {1: 1307, 2: 439, 3: 199, 4: 122, 5: 67, 6: 47, 8: 25, 7: 23, 11: 14, 10: 9, 9: 8, 12: 8, 16: 6, 14: 4, 15: 4, 18: 3, 19: 3, 13: 2, 17: 1, 20: 1, 22: 1, 25: 1, 28: 1, 30: 1, 41: 1}
        return {1: 1302, 2: 577, 3: 216, 4: 121, 5: 34, 6: 20, 7: 8, 8: 7, 9: 4, 12: 1, 16: 1}
    
    def _create_app_causality(self):
        causality = {}
        for app in map(lambda x: x[0], self.app_distrs):
            causality[app] = App(app)

        for s in causality:
            count = 0
            cdf = 0
            for p in causality:
                count += 1
                if count < len(self.app_distrs) and cdf < 1:
                    influence = random.uniform(0.0001, 1 - cdf)
                    causality[s].pred_influence[p] = influence
                    cdf += influence
                else:
                    influence = max(1 - cdf, 0.0001)
                    causality[s].pred_influence[p] = influence
        return causality

    def generate_sessions(self):
        sessions = []
        init_contexts = self._generate_init_contexts()
        for init_context in init_contexts:
            session = []
            env_context = init_context[0][:-1]
            launched_apps = [init_context[0][-1]]
            session.append(init_context[0])
            for i in xrange(choice_by_distr(self.session_len_distr)):
                application = self._generate_next_app(launched_apps)
                launched_apps.append(application)
                log = env_context + (application, )
                session.append(log)
            sessions.append(session)
        return sessions

    def _generate_init_contexts(self):
        os.system('benerator.sh test.xml')
        with open('app_usage_logs.flat', 'r') as f:
            lines = f.readlines()
            contexts = map(lambda x: x.strip().split(), lines)

        init_contexts = []
        for d, h, a in contexts:
            candidates = map(lambda x: (x[0], x[1].ocrs, x[1].day_distr[d]*x[1].hour_distr[h]*x[1].activity_distr[a]), self.app_distrs)
            results = sorted(candidates, key=itemgetter(2), reverse=True)
            # print results[:10]
            # log = (d, h, a, choice(candidates.keys(), candidates.values()))
            log = (d, h, a, choice(map(lambda x: x[0], results[:10]), map(lambda x: x[1], results[:10])))
            init_contexts.append([log])
        return init_contexts

    def _generate_next_app(self, launched_apps):
        candidates = defaultdict(int)

        for p in launched_apps:
            for s in self.app_causality:
                candidates[s] += self.app_causality[s].pred_influence[p]
        # p = launched_apps[-1]
        # for s in self.app_causality:
        #     candidates[s] += self.app_causality[s].pred_influence[p]
        # for p in launched_apps:
        #     candidates[p] += 1
        winner = choice(candidates.keys(), candidates.values())
        while winner == p:
            winner = choice(candidates.keys(), candidates.values())
        return winner
        

def main():
    helper = ApeicDBHelper()

    logs = []
    users = helper.get_users()
    for user in users:
        logs.extend(helper.get_logs(user))
    logs = map(lambda x: format(x), logs)
    logs = sorted(logs, key=itemgetter(-1))

    app_distrs = []
    for application, traces in groupby(logs, lambda x: x[-1]):
        # day
        cluster = list(traces)
        day_distr = defaultdict(lambda: 0.00001)
        for k, v in groupby(cluster, lambda x: x[0]):
            day_distr[k] += sum(1 for _ in v)
        n = float(sum(day_distr.values()))
        for d in day_distr:
            day_distr[d] /= n

        # hour
        hour_distr = defaultdict(lambda: 0.00001)
        for k, v in groupby(cluster, lambda x: x[1]):
            hour_distr[k] += sum(1 for _ in v)
        n = float(sum(hour_distr.values()))
        for h in hour_distr:
            hour_distr[h] /= n

        # activity
        activity_distr = defaultdict(lambda: 0.00001)
        for k, v in groupby(cluster, lambda x: x[2]):
            activity_distr[k] += sum(1 for _ in v)
        n = float(sum(activity_distr.values()))
        for a in activity_distr:
            activity_distr[a] /= n

        # n = float(sum(hour_distr.values()))
        # if n > 100:
            # print application
            # for h in xrange(24):
            #     print hour_distr[h]/n
        app_distrs.append((application, AppDistr(day_distr, hour_distr, activity_distr)))

    # for dist in app_distrs:
    #     for h in xrange(24):
    #         print h, dist.hour_distr[h]

    distrs = random.sample(app_distrs, 10)
    with open('app_usage_logs.flat', 'r') as f:
        lines = f.readlines()
        _logs = map(lambda x: x.strip().split(), lines)


    logs = []
    for d, h, a in _logs:
        candidates = dict(map(lambda x: (x[0], x[1].day_distr[d]*x[1].hour_distr[h]*x[1].activity_distr[a]), distrs))
        log = (d, h, a, choice(candidates.keys(), candidates.values()))
        print log
        logs.append(log)

    training_logs, testing_logs = split(logs)
    extractor = FeatureExtractor()
    X, y = extractor.generate_training_instances(training_logs)
    nb = MultinomialNB()
    nb_predictor = nb.fit(X, y)

    hits = 0.0
    misses = 0.0
    for log in testing_logs:
        instance = extractor.transform(log)
        ranking = sorted(zip(nb_predictor.classes_, nb_predictor.predict_proba(instance)[0]), \
                            key=operator.itemgetter(1), reverse=True)
        candidates = map(lambda x: x[0], ranking[:4])
        if log[-1] in candidates:
            hits += 1.0
        else:
            misses += 1.0
    acc = hits/(hits + misses)
    print acc, hits, misses


def test():
    generator = SessionGenerator()
    sessions = generator.generate_sessions()
    training_sessions, testing_sessions = split(sessions)
        
    # logs = list(itertools.chain(*sessions))
    # training_logs, testing_logs = split(logs)
    training_logs = list(itertools.chain(*training_sessions))
    testing_logs = list(itertools.chain(*testing_sessions))
    extractor = FeatureExtractor()
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
            # log = session[i][:-1] + [last_app] + [session[i][-1]]
            log = session[i]
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
    for log in testing_logs:
        instance = extractor.transform(log)
        ranking = sorted(zip(nb_predictor.classes_, nb_predictor.predict_proba(instance)[0]), \
                            key=operator.itemgetter(1), reverse=True)
        candidates = map(lambda x: x[0], ranking[:4])
        if log[-1] in candidates:
            hits += 1.0
        else:
            misses += 1.0
    acc = hits/(hits + misses)
    print acc, hits, misses


from operator import add
if __name__ == '__main__':
    test()

    """
    helper = ApeicDBHelper()

    users = helper.get_users()
    for user in users[1:]:
        # print len(helper.get_used_apps(user))
        sessions = helper.get_sessions(user)
        for session in sessions:
            for log in session:
                print log['datetime'], log['application']
            print
        break
    """