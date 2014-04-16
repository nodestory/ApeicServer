import bisect
import random

def cdf(weights):
    total = sum(weights)
    result = []
    cumsum = 0
    for w in weights:
        cumsum += w
        result.append(cumsum/total)
    return result

def choice(population, weights):
    assert len(population) == len(weights)
    cdf_vals = cdf(weights)
    x = random.random()
    idx = bisect.bisect(cdf_vals,x)
    return population[idx]

def choice_by_distr(distr):
    population = distr.keys()
    weights = distr.values()
    cdf_vals = cdf(weights)
    x = random.random()
    idx = bisect.bisect(cdf_vals,x)
    return population[idx]    