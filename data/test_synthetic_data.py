import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper
from predictor import *
from generate_synthetic_data import SyntheticDataGenerator
      
def format(log):
    day = log['datetime'].isoweekday()
    hour = log['datetime'].hour
    if log['activity'] in ['STILL', 'TILTING']:
        activity = 'STATIC'
    else:
        activity = log['activity']
    application = log['application']
    return day, hour, activity, application

def test(sessions):
    training_sessions, testing_sessions = split(sessions, 0.8)
    training_logs = list(itertools.chain(*training_sessions))
    testing_logs = list(itertools.chain(*testing_sessions))

    extractor = FeatureExtractor()
    X, y = extractor.generate_training_instances(training_logs)
    nb = MultinomialNB()
    nb_predictor = nb.fit(X, y)

    apeic_predictor = ApeicPredictor()
    for session in training_sessions:
        apeic_predictor.update(session)

    hits = 0.0
    misses = 0.0
    last_app = ''
    for session in testing_sessions:
        for i in xrange(len(session)):
            log = session[i]
            instance = extractor.transform(log, last_app)
            ei = dict(zip(nb_predictor.classes_, nb_predictor.predict_proba(instance)[0]), \
                key=operator.itemgetter(1), reverse=True)
            candidates = apeic_predictor.predict(session[:i], ei, last_app, 4)
            # last_app = log[-1]
            if session[i][-1] in candidates:
                hits += 1.0
            else:
                misses += 1.0
        # apeic_predictor.update(session)

    apeic_acc = (hits)/(hits + misses)
    print apeic_acc, hits, misses

    # nb
    X, y = extractor.generate_training_instances(training_logs, True)
    nb = MultinomialNB()
    nb_predictor = nb.fit(X, y)

    hits = 0.0
    misses = 0.0
    last_app = ''
    for log in testing_logs:
        instance = extractor.transform(log, last_app, True)
        ranking = sorted(zip(nb_predictor.classes_, nb_predictor.predict_proba(instance)[0]), \
                            key=operator.itemgetter(1), reverse=True)
        last_app = log[-1]
        candidates = map(lambda x: x[0], ranking[:4])
        if log[-1] in candidates:
            hits += 1.0
        else:
            misses += 1.0
    nb_acc = hits/(hits + misses)
    print nb_acc, hits, misses

    # lu
    hits = 0.0
    misses = 0.0
    predictor = LUPredictor(0.25)
    predictor.train(training_logs)

    for i in xrange(2, len(testing_logs)):
        candidates = predictor.predict(testing_logs[i-2][-1], testing_logs[i-1][-1])
        if testing_logs[i][-1] in candidates:
            hits += 1.0
        else:
            misses += 1.0
    lu_acc = hits/(hits + misses)
    print lu_acc, hits, misses

    # mru
    hits = 0.0
    misses = 0.0
    logs = training_logs + testing_logs
    candidates = map(lambda x: x[-1], logs[:4])
    for log in logs[4:]:
        if log[-1] in candidates:
            hits += 1.0
        else:
            misses += 1.0
        candidates = candidates[1:] + [log[-1]]
    mru_acc = hits/(hits + misses)
    print mru_acc, hits, misses    

    # mfu
    used_apps = []
    for session in training_sessions:
        used_apps += map(lambda x: x[-1], session)
    counter = Counter(used_apps)
    candidates = map(lambda x: x[0], counter.most_common(4))

    hits = 0.0
    misses = 0.0
    for log in testing_logs:
        if log[-1] in candidates:
            hits += 1.0
        else:
            misses += 1.0
    mfu_acc = hits/(hits + misses)
    print mfu_acc, hits, misses

    return apeic_acc, nb_acc, lu_acc, mru_acc, mfu_acc


def run():
    s = 4
    k = 1
    m = 100
    l = 3
    c = 0.2
    generator = SyntheticDataGenerator(s, k, m, l, c)
    with open('data/s=%d,k=%d,m=%d,l=%d,c=%2f.txt' % (s, k, m, l, c), 'w') as f:
        # for n in xrange(10, 61, 5):
        for n in [50]:
            generator.set_params(n, s, k, m, l, c)

            result = []
            for i in xrange(30):
                print n, i
                sessions = generator.generate_sessions()
                result.append(test(sessions))
            apeic_acc = sum(map(lambda x: x[0], result))/len(result)
            nb_acc = sum(map(lambda x: x[1], result))/len(result)
            lu_acc = sum(map(lambda x: x[2], result))/len(result)
            mru_acc = sum(map(lambda x: x[3], result))/len(result)
            mfu_acc = sum(map(lambda x: x[4], result))/len(result)
            print n, apeic_acc, nb_acc, lu_acc, mru_acc, mfu_acc
            f.write('%d\t%f\t%f\t%f\t%f\t%f\n' % (n, apeic_acc, nb_acc, lu_acc, mru_acc, mfu_acc))

def temp():
    s = 3
    k = 1
    m = 300
    l = 3
    c = 0.3
    n = 50
    generator = SyntheticDataGenerator(s, k, m, l, c)
    generator.set_params(n, s, k, m, l, c)
    sessions = generator.generate_sessions()
    print test(sessions)

if __name__ == '__main__':
    run()
