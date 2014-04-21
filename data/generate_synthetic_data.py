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
        # activity = 'STATIC'
        activity = log['activity']
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

    def __init__(self, app_num=30, session_num=1000):
        self.app_num = app_num
        self.session_num = session_num

        app_distrs = self._get_a_distrs()
        self.app_distrs = {}
        for a, b in random.sample(app_distrs, app_num):
            self.app_distrs[a] = b
        # self.app_distrs = random.sample(app_distrs, app_num)

        self.session_len_distr = self._get_session_len_distr()

        self.launching_contrib = self._launching_contrib()

    def _get_app_distrs(self):
        app_traces = self._get_app_traces()

        app_distrs = []
        for application, traces in groupby(app_traces, lambda x: x[-1]):
            if application in ['android', 'com.android.launcher', 'com.htc.launcher', \
                                'com.sec.android.app.launcher', 'com.tul.aviate', \
                                'com.thinkyeah.smartlockfree', 'com.htc.android.worldclock', \
                                'com.android.settings']:
                continue
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

        """
        for app, distr in app_distrs:
            if distr.ocrs > 100:
                print app
                print distr.day_distr.values()
                print distr.hour_distr.keys()
                print distr.hour_distr.values()
                print distr.activity_distr.keys()
                print distr.activity_distr.values()
                print
        """

        n = sum(map(lambda x: x[1].ocrs, app_distrs))
        for app, distr in app_distrs:
            distr.ocr_porb = distr.ocrs/n
        return app_distrs

    def _get_a_distrs(self):
        user_traces = self._get_app_traces()

        app_distrs = []
        for user in user_traces:
            app_traces = user_traces[user]
            for application, traces in groupby(app_traces, lambda x: x[-1]):
                if application in ['android', 'com.android.launcher', 'com.htc.launcher', \
                                'com.sec.android.app.launcher', 'com.tul.aviate', \
                                'com.thinkyeah.smartlockfree', 'com.htc.android.worldclock', \
                                'com.android.settings']:
                    continue
                # day
                ocrs = 0
                cluster = list(traces)
                day_distr = defaultdict(lambda: 0.00001)
                for k, v in groupby(cluster, lambda x: x[0]):
                    day_distr[str(k)] += sum(1 for _ in v)
                    ocrs += day_distr[str(k)]
                n = float(sum(day_distr.values()))
                for d in day_distr:
                    day_distr[d] /= n

                # hour
                hour_distr = defaultdict(lambda: 0.00001)
                for k, v in groupby(cluster, lambda x: x[1]):
                    hour_distr[str(k)] += sum(1 for _ in v)
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

                app_distrs.append((user+application, AppDistr(ocrs, day_distr, hour_distr, activity_distr)))

            n = sum(map(lambda x: x[1].ocrs, filter(lambda x: user in x[0], app_distrs)))
            for app, distr in filter(lambda x: user in x[0], app_distrs):
                distr.ocr_porb = distr.ocrs/n
        return app_distrs

    def _get_app_traces(self):
        """
        helper = ApeicDBHelper()

        logs = []
        users = helper.get_users()
        for user in users:
            logs.extend(helper.get_logs(user))

        logs = map(lambda x: format(x), logs)
        app_traces = sorted(logs, key=itemgetter(-1))
        return app_traces
        """

        helper = ApeicDBHelper()

        app_traces = defaultdict(list)
        users = helper.get_users()
        for user in users:
            logs = helper.get_logs(user)
            logs = map(lambda x: format(x), logs)
            app_traces[user] = sorted(logs, key=itemgetter(-1))
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
        print len_dist.keys()
        print len_dist.values()
        return len_dist
        """
        # {1: 1302, 2: 577, 3: 216, 4: 121, 5: 34, 6: 20, 7: 8, 8: 7, 9: 4, 12: 1, 16: 1}
        # {1: 1307, 2: 439, 3: 199, 4: 122, 5: 67, 6: 47, 8: 25, 7: 23, 11: 14, 10: 9, 9: 8, 12: 8, 16: 6, 14: 4, 15: 4, 18: 3, 19: 3, 13: 2, 17: 1, 20: 1, 22: 1, 25: 1, 28: 1, 30: 1, 41: 1}
        return {1: 1302, 2: 577, 3: 216, 4: 121, 5: 34, 6: 20, 7: 8, 8: 7, 9: 4, 12: 1, 16: 1}
        # return {1: 130, 2: 577, 3: 216, 4: 121, 5: 34, 6: 20, 7: 8, 8: 7, 9: 4, 12: 1, 16: 1}
        return {1: 1, 2: 8, 3: 8, 4: 10, 5: 20}
    
    def _launching_contrib(self):
        causality = {}
        # for app in map(lambda x: x[0], self.app_distrs):
        for app in self.app_distrs.keys():
            causality[app] = App(app)

        for s in causality:
            count = 0
            cdf = 0
            for p in causality:
                count += 1
                if count < len(self.app_distrs) and cdf < 1:
                    influence = random.uniform(0, 1 - cdf)
                    causality[s].pred_influence[p] = influence
                    cdf += influence
                else:
                    influence = 1 - cdf
                    causality[s].pred_influence[p] = influence
        return causality

    ##############################
    def generate_sessions(self):
        sessions = []

        env_contexts = self._generate_env_contexts()
        for d, h, a in env_contexts:
            session = []
            env_context = d, h, a
            int_context = []

            # TODO: determine "session_len"
            int_context = self._generate_int_context(env_context)
            for application in int_context:
                log = (d, h, a, application)
                session.append(log)
            sessions.append(session)
            print '\n'.join(map(lambda x: x[-1], session))
            print

            """
            session_len = 9
            for i in xrange(session_len):
                if i == 0:
                    application = self._init_int_context(env_context)
                else:
                    application = self._develop_int_context(env_context, int_context)
                int_context.append(application)
                log = (d, h, a, application)
                session.append(log)
            # print '\n'.join(map(lambda x: x[-1], session))
            # print
            sessions.append(session)
            """
        return sessions

    def _generate_env_contexts(self):
        # TODO: generate *.wgt.csv files
        os.system('benerator.sh test.xml')
        with open('app_usage_logs.flat', 'r') as f:
            lines = f.readlines()
            env_contexts = map(lambda x: x.strip().split(), lines)
        return env_contexts

    def _generate_int_context(self, env_context):
        d, h, a = env_context
        distrs = self.app_distrs
        candidates = map(lambda x: (x, \
                            1e-16 + distrs[x].day_distr[d]*distrs[x].hour_distr[h]*distrs[x].activity_distr[a]), \
                            distrs)
        candidates = sorted(candidates, key=itemgetter(1), reverse=True)
        int_context = []
        while(len(int_context) < 5):
            app = choice(map(lambda x: x[0], candidates), map(lambda x: x[1], candidates))
            print app
            print int_context
            if app not in int_context:
                int_context.append(app)
        return int_context

        for i in xrange(6, 10):
            index = random.choice(xrange(1, len(int_context)))
            app = random.choice(int_context[:index] + [random.choice(distrs.keys())])
            pos = random.choice(xrange(index, len(int_context)))
            while app != int_context[pos] and app != int_context[pos-1]:
                app = random.choice(int_context[:index] + [random.choice(distrs.keys())])
            int_context.insert(pos, app)
        return int_context

    def _init_int_context(self, env_context):
        d, h, a = env_context
        # candidates = map(lambda x: (x[0], x[1].day_distr[d]*x[1].hour_distr[h]*x[1].activity_distr[a]), \
        #                     self.app_distrs)
        candidates = map(lambda x: (x, \
            self.app_distrs[x].day_distr[d]*self.app_distrs[x].hour_distr[h]*self.app_distrs[x].activity_distr[a]), \
                            self.app_distrs)
        candidates = sorted(candidates, key=itemgetter(1), reverse=True)
        return choice(map(lambda x: x[0], candidates), map(lambda x: x[1], candidates))

    def _develop_int_context(self, env_context, int_context):
        d, h, a = env_context
        distrs = self.app_distrs
        results = map(lambda x: (x, 
                        distrs[x].day_distr[d]*distrs[x].hour_distr[h]*distrs[x].activity_distr[a]), \
                    self.app_distrs)
        # results = sorted(results[:2], key=itemgetter(1), reverse=True)
        # return random.choice(map(lambda x: x[0], results))

        candidates = defaultdict(lambda: 0.00001)
        for p in int_context:
            for s in self.launching_contrib:
            # for s in map(lambda x: x, result[:3]):
            # for s in result:
                if self.launching_contrib[s].pred_influence[p] > 0:
                    candidates[s] += self.launching_contrib[s].pred_influence[p]

        for s in self.launching_contrib:
            tt = self.app_distrs[s].ocr_porb
            # candidates[s] *= (tt + random.uniform(-tt*0.2, tt*0.2))
            candidates[s] *= tt


        # for a, b in results:
        #     tt = self.app_distrs[a].ocr_porb
        #     candidates[a] *= (tt + random.uniform(-tt*0.001, tt*0.001))
            # candidates[a] *= b
            # print b, max(-0.0005, -b + 0.00001), 0.0005
            # candidates[a] *= (b + random.uniform(-b*0.1, b*0.1))

        winner = choice(candidates.keys(), candidates.values())
        count = 0
        while winner == int_context[-1]:
            winner = choice(candidates.keys(), candidates.values())
            count += 1
            if count == 10:
                break
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