import random

def generate_random():
    while 1:
        yield random.sample(range(0,4),4), random.sample(range(0,4),4), random.sample(range(0,4),4)

def generate_test():
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