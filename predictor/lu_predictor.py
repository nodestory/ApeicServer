import operator
from sklearn.feature_extraction import DictVectorizer
from sklearn.naive_bayes import MultinomialNB
from predictor.predictor import Predictor, split

class LUPredictor(Predictor):

    def __init__(self):
        self.vectorizer = DictVectorizer()

    def train(self, data):
        nb = MultinomialNB()

        launches = map(lambda x: x['application'], data)
        instances = map(lambda i: {'lu1': launches[i-1]}, xrange(1, len(launches)))
        X = self.vectorizer.fit_transform(instances).toarray()
        y = launches[1:]
        self.lu1_predictor = nb.fit(X, y)

        instances = map(lambda i: {'lu2': launches[i-2]}, xrange(2, len(launches)))
        X = self.vectorizer.fit_transform(instances).toarray()
        y = launches[2:]
        self.lu2_predictor = nb.fit(X, y)

        # tune mu
        max_hr = 0
        best_mu = 0
        for mu in map(lambda x: x/10.0, xrange(11)):
            self.mu = mu
            predictions = map(lambda i: self.predict({'lu1': launches[i-1], 'lu2': launches[i-2]}), \
                xrange(2, len(launches)))
            hr, mrr = self.test(launches[2:], predictions)
            if hr > max_hr:
                max_hr = hr
                best_mu = mu
        self.mu = best_mu

    def predict(self, data, k=4):
        vectorizer = DictVectorizer()

        x = self.vectorizer.transform({'lu1': data['lu1']}).toarray()[0]
        lu1_result = zip(self.lu1_predictor.classes_, self.lu1_predictor.predict_proba(x)[0])
        x = self.vectorizer.transform({'lu2': data['lu2']}).toarray()[0]
        lu2_result = zip(self.lu2_predictor.classes_, self.lu2_predictor.predict_proba(x)[0])

        result = dict(map(lambda x, y: (x[0], self.mu*x[1] + (1 - self.mu)*y[1]), lu1_result, lu2_result))
        ranking = sorted(result, key=result.get, reverse=True)
        candidates = ranking[:k]
        assert len(candidates) <= k
        return candidates

from apeic.apeic_db_manager import ApeicDBHelper
def main():
    predictor = LUPredictor()

    db_helper = ApeicDBHelper()
    users = db_helper.get_users()

    for user in users:
        sessions = db_helper.get_sessions(user)
        training_logs, testing_logs = split(sessions, aggregated=True)
        
        predictor.train(training_logs)
        launches = map(lambda x: x['application'], testing_logs[2:])
        predictions = map(lambda i: predictor.predict(\
            {'lu1': testing_logs[i-1]['application'], 'lu2': testing_logs[i-2]['application']}), \
            xrange(2, len(testing_logs)))
        hr, mrr = predictor.test(launches, predictions)
        print hr, mrr

if __name__ == '__main__':
    main()