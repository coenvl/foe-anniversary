from my_solver import Solver
from mooing15 import solve
from solver import solve as bruteforce_solve

from generate_tests import generate_random, generate_tests, generate_normal

# Keep in mind you have to do this for each color on each board
score_maximum = 0
score_starting = 0
score_unsure = 0
total_keys = 0

signal = 100
try:
    for test_tuple in generate_normal():
        freeBot = [0,0,0,0]
        freeTop = [0,0,0,0]
        freeFull = [0,0,0,0]

        (locked_bottom, locked_top, free) = test_tuple

        (res_best,starting_best,max_best,total_progress_best,max_p_best,remainingLocked_best) = bruteforce_solve(locked_bottom.copy(),locked_top.copy(),free.copy(),freeBot.copy(),freeTop.copy(),freeFull.copy(),silent=True)
        (res_opt,starting_opt,max_opt,total_progress_opt,max_p_opt,remainingLocked_opt) = Solver(locked_bottom.copy(),locked_top.copy(),free.copy(),freeBot.copy(),freeTop.copy(),freeFull.copy(),silent=True).solve()
        (res,starting,max_keys,total_progress,max_p,remainingLocked) = solve(locked_bottom.copy(),locked_top.copy(),free.copy(),freeBot.copy(),freeTop.copy(),freeFull.copy(),silent=True)

        if res_best > starting or res_best > max_keys:
            raise Exception('Impossible')

        if res_best < res_opt or res_best < res:
            with open('deteriorate_cases.txt', 'a') as fid:
                fid.write(f'locked_bottom = {locked_bottom}\n')
                fid.write(f'locked_top = {locked_top}\n')
                fid.write(f'free = {free}\n\n')

        if res_best > res_opt or res_best > res:
            with open('improved_cases.txt', 'a') as fid:
                fid.write(f'locked_bottom = {locked_bottom}\n')
                fid.write(f'locked_top = {locked_top}\n')
                fid.write(f'free = {free}\n\n')

        if res_opt == max_keys:
            score_maximum += 1
        elif res_opt == starting:
            score_starting += 1
        else:
            score_unsure += 1
        total_keys += res_best
        print('.', end='', flush=True)
except KeyboardInterrupt:
    pass

print(f"Scored a total of {total_keys} keys")
print(f"Scored maximum keys {score_maximum} times")
print(f"Scored maximum keys given spawned gems {score_starting} times")
print(f"Other results {score_unsure} times")
print(f"Overall score {float(score_maximum + score_starting) / float(score_maximum + score_starting + score_unsure)}")
