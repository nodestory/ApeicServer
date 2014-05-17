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

    return apeic_acc, nb_acc, mfu_acc


if __name__ == '__main__':
    s = 2
    k = 1
    m = 80
    l = 2
    c = 0.3
    generator = SyntheticDataGenerator(s, k, m, l, c)
    with open('data/s=%d,k=%d,m=%d,l=%d,c=%.1f.txt' % (s, k, m, l, c), 'w') as f:
        for n in xrange(10, 51, 5):
            generator.set_params(n, s, k, m, l, c)

            result = []
            for i in xrange(30):
                print n, i
                sessions = generator.generate_sessions()
                result.append(test(sessions))
            apeic_acc = sum(map(lambda x: x[0], result))/len(result)
            nb_acc = sum(map(lambda x: x[1], result))/len(result)
            mfu_acc = sum(map(lambda x: x[2], result))/len(result)
            print n, apeic_acc, nb_acc, mfu_acc
            f.write('%d\t%f\t%f\t%f\n' % (n, apeic_acc, nb_acc, mfu_acc))
