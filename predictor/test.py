from sklearn.cluster import DBSCAN
from apeic.apeic_db_manager import ApeicDBHelper


from math import radians, cos, sin, asin, sqrt
def get_distance(loc1, loc2):
    """ Metric for computing the great circle distance between two points (specified in decimal degrees)"""
    # convert decimal degrees to radians
    # print loc1, loc2
    lat1, lng1 = map(radians, loc1)
    lat2, lng2 = map(radians, loc2)
    # haversine formula
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    dist = 6367000 * c
    return dist # m

def tt(X, Y=None):
    """ Metric for computing the great circle distance between two points (specified in decimal degrees)"""
    # convert decimal degrees to radians
    # print loc1, loc2
    result = []
    for lat1, lng1 in X:
        for lat2, lng2 in X:
            dists = []
            lat1, lng1 = map(radians, [lat1, lng1])
            lat2, lng2 = map(radians, [lat2, lng2])
            # haversine formula
            dlng = lng2 - lng1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
            c = 2 * asin(sqrt(a))
            dist = 6367000 * c
            dists.append(dist)
        result.append(dists)
    return array(result)
            

from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.datasets.samples_generator import make_blobs
from sklearn.preprocessing import StandardScaler


##############################################################################
# Generate sample data
centers = [[1, 1], [-1, -1], [1, -1]]
X, labels_true = make_blobs(n_samples=100, centers=centers, cluster_std=0.4,
                            random_state=0)
X = StandardScaler().fit_transform(X)

from numpy import array
from predictor.predictor import Predictor, split
db_helper = ApeicDBHelper()
for user in db_helper.get_users()[7:]:
    sessions = db_helper.get_sessions(user)
    training_logs, testing_logs = split(sessions, aggregated=True)

    
    training_logs = filter(lambda x: x['latitude'] != 0 and x['longitude']!= 0, training_logs)
    latlng_pairs = list(set(map(lambda x: (x['latitude'], x['longitude']), training_logs)))
    print latlng_pairs
    print len(latlng_pairs)
    # X = array(latlng_pairs)
    # print X.size
    # print X
    result = []
    for la1, ln1 in latlng_pairs:
        dists = []
        for la2, ln2 in latlng_pairs:
            lat1, lng1 = map(radians, [la1, ln1])
            lat2, lng2 = map(radians, [la2, ln2])
            # haversine formula
            dlng = lng2 - lng1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
            c = 2 * asin(sqrt(a))
            dist = 6367 * c
            dists.append(dist)
        result.append(dists)
    print result
    X = array(result)

    print X

    db = DBSCAN(eps=0.1, min_samples=3, metric='precomputed').fit(X)
    core_samples = db.core_sample_indices_
    labels = db.labels_

    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    print n_clusters_
    break