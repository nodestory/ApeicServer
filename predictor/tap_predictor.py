from collections import Counter, defaultdict


class AppInstance(object):
    """docstring for AppInstance"""
    def __init__(self, arg):
        super(AppInstance, self).__init__()
        self.global_feature = defaultdict(int)
        self.temporal_feature = defaultdict(int)
        self.periodical_feature = defaultdict(int)
        
class TAPPredictor(Predictor):

    def __init__(self):
        self.apps = {}

    def train(self, training_data):

        launches = map(lambda x: (x['application'], x['datetime']), training_data)
        counter = Counter(map(lambda x: x[0], launches))
        for item in counter:
            


        # global
        counter = Counter(map(lambda x: x[0], launches))

        # temporal

        # periodical

        pass


    def predict(self, lu2, lu1, k=4):
        pass

import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
from apeic_db_manager import ApeicDBHelper
def main():
    db_helper = ApeicDBHelper()
    
    hits = 0.0
    misses = 0.0
    users = db_helper.get_users()
    for user in users:
        logs = db_helper.get_logs(user)
        training_data, testing_data = split(logs)
        predictor = TAPPredictor()
        predictor.train(training_data)

        for i in xrange(2, len(testing_data)):
            candidates = predictor.predict(testing_data[i-2]['application'], testing_data[i-1]['application'], k)
            if testing_data[i]['application'] in candidates:
                hits += 1.0
            else:
                misses += 1.0

    print k, hits/(hits + misses)

if __name__ == '__main__':
    main()