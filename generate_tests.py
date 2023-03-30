import random
from numpy.random import binomial

def generate_random():
    while 1:
        yield random.sample(range(0,5),4), random.sample(range(0,5),4), random.sample(range(0,4),4)

def generate_normal():
    while 1:
        yield list(binomial(5,.35,4)), list(binomial(5,.35,4)), list(binomial(4,.25,4))

def generate_tests():
    for file in ['test_cases.txt']:
         with open(file, 'r', encoding = 'utf-8') as fid:
            while fid.readable():
                line = fid.readline()
                if not line:
                    break

                lockedB = eval(line.split(" = ")[1])
                lockedT = eval(fid.readline().split(" = ")[1])
                free = eval(fid.readline().split(" = ")[1])
                fid.readline()

                yield (lockedB, lockedT, free)
