import bisect
import random

def choice(candidates):
    population = [x for x, p in candidates]
    weights = [p for x, p in candidates]
    if sum(weights) == 0:
        return random.choice(population)
    total = float(sum(weights))

    cdf_vals = [sum(weights[:i+1])/total for i in xrange(len(candidates))]
    x = random.random()
    idx = bisect.bisect(cdf_vals, x)
    return population[idx]

def sample(candidates, k):
    samples = []
    for i in xrange(k):
        sample = choice(candidates)
        candidates = filter(lambda x: x[0] != sample, candidates)
        samples.append(sample)
    return samples

# deprecated methods
"""
def choice(population, weights):



    assert len(population) == len(weights)
    cdf_vals = _cdf(weights)
    x = random.random()
    idx = bisect.bisect(cdf_vals,x)
    return population[idx]

def _cdf(weights):
    total = sum(weights)
    result = []
    cumsum = 0
    for w in weights:
        cumsum += w
        result.append(cumsum/total)
    return result
"""