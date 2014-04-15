import operator
from sklearn.feature_extraction import DictVectorizer
from sklearn.naive_bayes import MultinomialNB
from apeic.apeic_db_manager import ApeicDBHelper
from predictor import Predictor

class LUPredictor(Predictor):

    def __init__(self):
        self.vectorizer = DictVectorizer()
        pass

    def train(self, training_data):
        nb = MultinomialNB()

        instances = []
        for i in xrange(1, len(training_data)):
            instance = {}
            instance['lu_1'] = training_data[i-1]['application']
            instances.append(instance)
        X = self.vectorizer.fit_transform(instances).toarray()
        y = map(lambda x: x['application'], training_data[1:])
        self.lu_predictor = nb.fit(X, y)

        instances = []
        for i in xrange(2, len(training_data)):
            instance = {}
            instance['lu_2'] = training_data[i-2]['application']
            instances.append(instance)
        X = self.vectorizer.fit_transform(instances).toarray()
        y = map(lambda x: x['application'], training_data[2:])
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

        result = dict(map(lambda x, y: (x[0], x[1]+r*y[1]), lu_result, lu2_result))
        ranking = sorted(result.iteritems(), key=operator.itemgetter(1), reverse=True)
        candidates = map(lambda x: x[0], ranking[:k])
        return candidates

def split(data, ratio=0.8):
    split_index = int(len(data)*ratio)
    return data[:split_index], data[split_index:]

r = 0.5
def main():
    db_helper = ApeicDBHelper()
    
    hits = 0.0
    misses = 0.0
    users = db_helper.get_users()
    for user in users:
        logs = db_helper.get_logs(user)
        training_data, testing_data = split(logs)
        predictor = LUPredictor()
        predictor.train(training_data)

        for i in xrange(2, len(testing_data)):
            candidates = predictor.predict(testing_data[i-2]['application'], testing_data[i-1]['application'])
            if testing_data[i]['application'] in candidates:
                hits += 1.0
            else:
                misses += 1.0

    print hits/(hits + misses)

if __name__ == '__main__':
    main()