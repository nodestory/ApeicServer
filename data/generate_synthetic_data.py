# TODO
import os
import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper

import itertools
import operator
import math
import numpy
import random
import nonrandom
from collections import Counter, defaultdict
from itertools import groupby
from operator import itemgetter

class RealDataAnalyzer():

    def __init__(self):
    	self.feature_names = ['day', 'hr', 'act']

    def _format(self, log):
        day = log['datetime'].isoweekday()
        hour = log['datetime'].hour
        act = 'STATIC' if log['activity'] in ['STILL', 'TILTING'] else log['activity']
        app = log['application']
        return day, hour, act, app

    def get_env_context_distrs(self, logs, export=True):
        logs = map(lambda x: self._format(x), logs)
        env_context_distrs = map(lambda i: self._get_feature_distr(i, logs), range(3))
        if export:
            for i in xrange(len(self.feature_names)):
                self._export_att_weights(self.feature_names[i], env_context_distrs[i])
        return env_context_distrs

    def _export_att_weights(self, feature_name, distr):
        with open('xml/%s.wgt.csv' % feature_name, 'w') as f:
            # result = sorted(distr.iteritems(), key=operator.itemgetter(0))
            result = sorted(distr.iteritems(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
            for k, v in result:
                f.write('%s,%f\n' % (k, v))

    def get_segment_len_distrs(self):
        distr = defaultdict(list)

        db = ApeicDBHelper()
        for user in db.get_users():
            sessions = db.get_sessions(user)
            for session in sessions:
                int_context = map(lambda x: x['application'], session)
                session_len = len(int_context)
                initiator = max(set(int_context), key=int_context.count)
                indices = [i for i, x in enumerate(int_context) if x == initiator] + [session_len]
                if session_len <= 2:
                	distr[session_len].append((session_len, ))
                else:
                    segment_lens = ()
                    for i in xrange(indices[0]):
                        segment_lens += (1, )
                    for i in xrange(1, len(indices)):
                        segment_lens += (indices[i] - indices[i-1], )
                    distr[session_len].append(segment_lens)
        distr = dict(map(lambda x: (x, Counter(distr[x]).items()), distr))
        return distr

    def get_app_usage_distrs(self):
    	app_usage_distrs = {}

    	db = ApeicDBHelper()
    	for user in db.get_users():
            sessions = db.get_sessions(user)
            logs = list(itertools.chain(*sessions))
            logs = map(lambda x: self._format(x), logs)
            user_traces = sorted(logs, key=itemgetter(-1))
            for app, traces in groupby(user_traces, lambda x: x[-1]):
            	cluster = list(traces)
            	count = app_usage_distrs.keys().count(app)
            	app_usage_distrs['%s_%d' % (app, count + 1)] = \
                    tuple(map(lambda i: self._get_feature_distr(i, cluster), range(len(self.feature_names))))
        return app_usage_distrs
        
    def _get_feature_distr(self, feature_index, cluster):
        # TODO:
    	distr = defaultdict(lambda: 1e-5)
    	for k, v in groupby(cluster, lambda x: x[feature_index]):
    		distr[str(k)] += sum(1 for _ in v)
    	n = float(sum(distr.values()))
    	for att in distr:
    	    distr[att] /= n
    	return distr

class SyntheticDataGenerator():

    def __init__(self, s, k, m, l, c):
        analyzer = RealDataAnalyzer()
        self.feature_num = len(analyzer.feature_names)
    	self.app_usage_distrs = analyzer.get_app_usage_distrs()

    def set_params(self, n, s, k, m, l, c):
        self.n = n
        self.s = s
        self.k = k
        self.m = m
        self.l = l
        self.c = c

    def generate_sessions(self):
        app_usage_distrs = {}
        for i in xrange(self.n):
            app, distr = random.choice(self.app_usage_distrs.items())
            app = app.split('_')[0] + '_%d' % i
            app_usage_distrs[app] = distr
        self.app_pool = app_usage_distrs
        self.segments = self._gen_segments()

        sessions = []
    	env_contexts = self._generate_env_contexts()
    	for env_context in env_contexts:
            session = []
            int_context = self._dev_int_context(env_context)
            for app in int_context:
                log = env_context + (app, )
                session.append(log)
            sessions.append(session)

            # """
            for s in session:
                print s
            print
            # """

        return sessions

    def _generate_env_contexts(self):
        os.system('benerator.sh xml/env_context.xml')
        with open('env_context.flat', 'r') as f:
            lines = f.readlines()
            env_contexts = map(lambda x: self._slice(x, 2, 3, 10), lines)
        return env_contexts

    def _slice(self, line, *args):
        tokens = []
        pos = 0
        for length in args:
            tokens.append(line[pos:pos+length].strip())
            pos += length
        return tuple(tokens)

    def _dev_int_context(self, ec):
        choices = []
        for segment in self.segments:
            results = map(lambda x: reduce(operator.mul, \
                            map(lambda i: self.app_pool[x][i][ec[i]], xrange(self.feature_num)), 1), \
                            segment)
            score = reduce(operator.mul, results, 1)
            choices.append((segment, score))

        int_context = []
        segment = nonrandom.choice(choices)
        for i in xrange(self.l):
            s = filter(lambda x: random.random() > self.c, segment)
            int_context.extend(s)
        if not int_context:
            int_context = segment
        return int_context

    def _gen_segments(self):
        segments = []
        segment = random.sample(self.app_pool.keys(), self.s)
        segments.append(segment)
        for i in xrange(self.m):
            prev_segment = segments[-1]
            segment = [prev_segment[i] for i in \
                    sorted(random.sample(xrange(len(prev_segment)), self.k))]
            segment += random.sample(filter(lambda x: x not in segment, self.app_pool.keys()), self.s - self.k)
            random.shuffle(segment)
            segments.append(segment)
        return segments

    ####################
    ## unused methods ##
    ####################
    def _develop_int_context(self, ec, session_len, app_usage_distrs):
        choices = []
        for segment in self.segments:
            results = map(lambda x: reduce(operator.mul, \
                            map(lambda i: app_usage_distrs[x][i][ec[i]], xrange(self.feature_num)), 1), \
                            segment)
            score = reduce(operator.mul, results, 1)
            choices.append((segment, score))

        # for app in app_usage_distrs:
        #     score = reduce(operator.mul, map(lambda i: app_usage_distrs[app][i][ec[i]], xrange(self.feature_num)), 1)
        #     choices.append(([app], score))            
        
        # int_context = []
        # while len(int_context) < session_len:
        #     size = nonrandom.choice(map(lambda x: (x, 3**x*math.exp(-3)/math.factorial(x)), \
        #             xrange(2, session_len - len(int_context) + 1)))
        #     if len(int_context) > 0:
        #         int_context.extend(nonrandom.choice(filter(lambda x: len(x[0]) == size and x[0][0] != int_context[-1], choices)))
        #     else:
        #         int_context.extend(nonrandom.choice(filter(lambda x: len(x[0]) == size, choices)))
        # return int_context


        c = 0.3
        int_context = []
        segment = nonrandom.choice(filter(lambda x: len(x[0]) == 3, choices))
        for i in xrange(3):
            s = filter(lambda x: random.random() > c, segment)
            int_context.extend(s)
        if not int_context:
            int_context = segment
        return int_context


        # return nonrandom.choice(choices)+nonrandom.choice(choices)+nonrandom.choice(choices)
        return nonrandom.choice(filter(lambda x: len(x[0]) == 4, choices))
            # nonrandom.choice(filter(lambda x: len(x[0]) == 4, choices))
        return random.choice(self.segments)+random.choice(self.segments)+random.choice(self.segments)    
        
        
        """
        candidates = map(lambda x: \
                            (x[0], random.uniform(0, 1e-4) + reduce(operator.mul, \
                                map(lambda i: x[1][i][ec[i]], xrange(self.feature_num)), 1)), \
                        app_usage_distrs.iteritems())
        initiator = nonrandom.choice(candidates)

        int_context = []
        predecessor = ''
        frames = nonrandom.choice(self.segment_len_distrs[session_len])
        for f in frames:
            segment = self._fill_segment(int_context, initiator, f, candidates, initiator)
            int_context.extend(segment)
            predecessor = int_context[-1]

        return int_context
        """

    def _fill_segment(self, int_context, initiator, segment_len, candidates, test):
        segment = []

        if len(int_context) > 0:
            predecessor = int_context[-1]
        else:
            predecessor = ''

        choices = list(candidates)
        initiator = nonrandom.choice(choices)
        if initiator == predecessor and predecessor != '' and initiator == test:
            choices = filter(lambda x: x[0] != predecessor, choices)
            initiator = nonrandom.choice(choices)


        """        
        choices = map(lambda x: (x, self.launching_contrib[x][initiator]), self.launching_contrib)
        choices = filter(lambda x: x[0] in map(lambda y: y[0], candidates), choices)
        if sum(v for k, v in choices) == 0:
            choices = list(candidates)
        """

        # """
        p = initiator
        while len(segment) < segment_len - 1:
            # choices = list(candidates)
            choices = map(lambda x: (x, self.launching_contrib[x][p]), self.launching_contrib)
            # if sum(v for k, v in choices) == 0:
            #     app = random.choice(self.launching_contrib.keys())
            app = nonrandom.choice(choices)
            while app in segment or app == initiator:
                choices = filter(lambda x: x[0] not in [initiator] + segment, choices)
                # choices = map(lambda x: (x, self.launching_contrib[x][p]), self.launching_contrib)
                app = nonrandom.choice(choices)
            segment.append(app)
            # p = app
        # """

        random.shuffle(segment)
        segment.insert(0, initiator)
        # random.shuffle(segment)
        return segment

    def _generate_launching_contrib(self, app_usage_distrs):
        contrib = {}
        for app in app_usage_distrs.keys():
            contrib[app] = defaultdict(int)


        population = app_usage_distrs.keys()
        clusters = []
        for i in xrange(20):
            print len(population)
            if len(population) <= 3:
                break
            apps = random.sample(population, random.choice([2, 3, 4]))
            clusters.append(apps)
            population = filter(lambda x: x not in apps, population)


        for s in contrib:
            cdf = 0
            c = []
            for cluster in clusters:
                if s in cluster:
                    c = list(cluster)
                    break
            for i in xrange(len(c)):
                if i == len(c) - 1:
                    influence = random.uniform(0, 1 - cdf)
                else:
                    influence = 1-cdf
                contrib[s][c[i]] = influence
                cdf += influence

            # for p in contrib:
                # if p not in c:
                    # influence = random.uniform(0, 1 - cdf)
                    # contrib[s][p] = influence
                    # cdf += influence

                            

        """
        for s in contrib:
            count = 0
            cdf = 0
            print s
            for p in contrib:
                count += 1
                if count < len(app_usage_distrs) and cdf < 1:
                    influence = random.uniform(0, 1 - cdf)
                    contrib[s][p] = influence
                    cdf += influence
                else:
                    influence = 1 - cdf
                    contrib[s][p] = influence
        """

        return contrib

    def _generate_segments(self, app_usage_distrs):
        # TODO: decide parameters
        session_len = 5
        I = 3
        l = 50

        apps = app_usage_distrs.keys()

        segments = []
        size = nonrandom.choice(map(lambda x: (x, I**x*math.exp(-I)/math.factorial(x)), xrange(2, 6)))
        segment = random.sample(apps, size)
        segments.append(segment)
        for i in xrange(l):
            prev_segment = segments[-1]
            # size = nonrandom.choice(map(lambda x: (x, I**x*math.exp(-I)/math.factorial(x)), xrange(2, 6)))
            size = 4
            # random.choice([2, 3])
            # TODO: decide how many items are preserved
            fragment_size = int(0.6*len(prev_segment))
            if fragment_size > 0:
                # segment = [prev_segment[i] for i in \
                #     sorted(random.sample(xrange(len(prev_segment)), fragment_size))]
                segment = random.sample(prev_segment, fragment_size)
            if len(segment) < size:
                segment.extend(random.sample(filter(lambda x: x not in segment, apps), size - len(segment)))
            # random.shuffle(segment)

            segment = random.sample(apps, size)
            segments.append(segment)

        return segments



def main():
    # TODO: ignore some user's data?
    # db = ApeicDBHelper()
    # logs = []
    # for user in db.get_users():
    #     logs.extend(db.get_logs(user))

    analyzer = RealDataAnalyzer()
    # analyzer.get_env_context_distrs(logs)
    analyzer.get_segment_len_distrs()

    # generator = SyntheticDataGenerator()
    # generator.generate_sessions()

if __name__ == '__main__':
	main()