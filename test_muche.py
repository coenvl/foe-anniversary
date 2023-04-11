#!python3
from math import floor, log
import types
from enum import Enum
from timeit import default_timer as timer
from typing import Tuple, List
from test_cases import TestCaseType, tests_suite

# active solver
from solver import solve
#from mooing15 import solve
#from my_solver import solve
#from solver_v31 import solve

# reference solver by MooingCat
import mooing15 as solver_mooing15
# other reference solvers used to establish best results in dev mode
import solver as solver_optimized_bruteforce
#import solver_v31


version = "v1.1"


def get_solvers() -> List[types.FunctionType]:
    solvers = [val.solve for name, val in globals().items() if name.startswith("solver_") and
                isinstance(val, types.ModuleType) and val.solve and
                isinstance(val.solve, types.FunctionType)]
    # active solver is imported directly, insert it at second position after the MooingCat's solver,
    # because it's the fastest, which is useful with PERF tests to get a quick baseline result
    solvers.insert(1, solve)
    return solvers

run_testcases_and = TestCaseType.ALL
#run_testcases_and = TestCaseType.ALL ^ TestCaseType.PERF  # don't run PERF tests
#run_testcases_and = TestCaseType.ALL | TestCaseType.SKIP  # run skipped tests as well
run_testcases_or = TestCaseType.ALL  # run everything
# run_testcases_or = TestCaseType.DEV  # run only tests under development
#run_testcases_or = TestCaseType.FOCUS  # run only focused cases

class RunResult(Enum):
    PASS = 0
    IMPR = 1
    FAIL = 2

    def try_impr(self):
        """ returns IMPR if current result was not FAIL """
        return self if self == self.FAIL else self.IMPR

class TestCase():
    PASS = "\033[32mpassed\033[0m test"
    FAIL = "\033[31mfailed\033[0m test"
    IMPR = "\033[31mimproved\033[0m test"
    SKIP = "skipped test"
    DONE = "\033[35mdone test\033[0m"

    def __init__(
            self, name:str, tctype:TestCaseType,
            # inputs
            locked_bottom: Tuple[int, int, int, int],
            locked_top: Tuple[int, int, int, int],
            free: Tuple[int, int, int, int],
            free_bottom: Tuple[int, int, int, int] = (0,0,0,0),
            free_top: Tuple[int, int, int, int] = (0,0,0,0),
            free_full: Tuple[int, int, int, int] = (0,0,0,0),
            # results
            keys: int = 0, max_keys: int = 0,  # i.e. L3 full + 3*L4 full
            progress: int = 0, potential_progress: int = 0,
            unlocked_part: int = 0, unlocked_empty: int = 0  # remaining unlocked gems, they matter only in the case of a cleared board
            ):
        self.name = name
        self.tctype = tctype if isinstance(tctype, TestCaseType) else TestCaseType(tctype)
        self.locked_bottom = tuple(locked_bottom)
        self.locked_top = tuple(locked_top)
        self.free = tuple(free)
        self.free_bottom = tuple(free_bottom)
        self.free_top = tuple(free_top)
        self.free_full = tuple(free_full)
        self.keys = keys
        self.max_keys = max_keys
        self.progress = progress
        self.potential_progress = potential_progress
        self.unlocked_part = unlocked_part
        self.unlocked_empty = unlocked_empty

    def is_dev(self) -> bool:
        return self.tctype & TestCaseType.DEV != TestCaseType.NONE

    def _run_dev(self) -> str:
        for solver in get_solvers():
            print(f"\n\t\033[35mRunning test '{self.name}' with solver {solver.__module__}:\033[0m")
            t_start = timer()
            # MooingCat's solver expects lists and modifies them, so copy the inputs
            try:
                print(solver(list(self.locked_bottom), list(self.locked_top), list(self.free),
                              list(self.free_bottom), list(self.free_top), list(self.free_full)))
            except KeyboardInterrupt:
                print("Solver interrupted by the user!")
            t_end = timer()
            print(f"Elapsed time: {t_end-t_start:.3f}s")
        return f"{self.DONE} '{self.name}'"

    def _run_skip(self) -> str:
        return f"{self.SKIP} '{self.name}'"

    @staticmethod
    def _compare(result: RunResult, result_string: List[str], expected_value, got_value, name: str) -> RunResult:
        if got_value < expected_value:
            result_string.append(f"Expected {expected_value} {name}, got {got_value}.")
            return RunResult.FAIL
        if got_value > expected_value:
            result_string.append(f"Expected {expected_value} {name}, got more ({got_value}).")
            return result.try_impr()
        return result

    def _run_normal(self) -> Tuple[str, int, int, int, int]:
        run_result = RunResult.PASS
        result_string: List[str] = []
        t_start = timer()
        try:
            # MooingCat's solver expects lists and modifies them, so copy the inputs
            (result_keys, _starting, result_max_keys,
             result_progress, result_potential_progress, _remaining_locked,
             result_unlocked_part, result_unlocked_empty) = solve(
                list(self.locked_bottom), list(self.locked_top), list(self.free),
                list(self.free_bottom), list(self.free_top), list(self.free_full), True)

            run_result = self._compare(run_result, result_string, self.keys, result_keys, "keys")
            run_result = self._compare(run_result, result_string, self.max_keys, result_max_keys, "max_keys")
            run_result = self._compare(run_result, result_string, self.progress, result_progress, "progress")
            run_result = self._compare(run_result, result_string, self.potential_progress, result_potential_progress, "potential_progress")
            run_result = self._compare(run_result, result_string, self.unlocked_part, result_unlocked_part, "unlocked_part")
            run_result = self._compare(run_result, result_string, self.unlocked_empty, result_unlocked_empty, "unlocked_empty")
        except KeyboardInterrupt:
            run_result = RunResult.FAIL
            result_string = ["Solver interrupted by the user!"]
        finally:
            t_end = timer()

        status, passed, improved, failed = ((self.PASS, 1, 0, 0) if run_result == RunResult.PASS else
                                           ((self.IMPR, 0, 1, 0) if run_result == RunResult.IMPR else
                                            (self.FAIL, 0, 0, 1)))
        if result_string:
            result_string.insert(0, " -")
        return (f"{status} '{self.name}' in {t_end-t_start:.3f}s{' '.join(result_string)}", 0, passed, improved, failed)

    def run(self, mask_and: TestCaseType, mask_or: TestCaseType) -> Tuple[str, int, int, int, int]:
        if (self.tctype & mask_and != self.tctype) or (self.tctype & mask_or == TestCaseType.NONE):
            return (self._run_skip(), 1, 0, 0, 0)
        if self.is_dev():
            return (self._run_dev(), 0, 1, 0, 0)
        return self._run_normal()

testcases = [TestCase(**args) for args in tests_suite]

def check_duplicate_tests():
    """ check tests for duplicates (inputs, or names) """
    tests_inputs = {}  # dictionary of tests, key is tuple of test's inputs, value is tuple (index, test)
    tests_name = {}  # dictionary of tests, key is str of test's name, value is tuple (index, test)
    for i, test in enumerate(testcases):
        key = (test.locked_bottom, test.locked_top, test.free, test.free_bottom, test.free_top, test.free_full)
        if key in tests_inputs:
            # duplicate found
            test_orig = tests_inputs[key]
            print(f"Test #{i+1} '{test.name}' ({test.tctype}) is a duplicate of #{test_orig[0]+1} '{test_orig[1].name}' ({test_orig[1].tctype})")
        else:
            tests_inputs[key] = (i, test)

        if test.name in tests_name:
            # duplicate found
            test_orig = tests_name[test.name]
            print(f"Test #{i+1} '{test.name}' ({test.tctype}) has the same name as #{test_orig[0]+1} '{test_orig[1].name}' ({test_orig[1].tctype})")
        else:
            tests_name[test.name] = (i, test)

def run_test_suite():   
    tests_skipped=0
    tests_passed = 0
    tests_improved = 0
    tests_failed = 0
    width = floor(log(len(testcases), 10)) + 1
    t_start = timer()

    for i, testcase in enumerate(testcases):
        result, skipped, passed, improved, failed = testcase.run(run_testcases_and, run_testcases_or)
        tests_skipped += skipped
        tests_passed += passed
        tests_improved += improved
        tests_failed += failed
        print(f"#{i+1: >{width}} {result}")
    t_end = timer()
    print(f"\nSummary: {len(testcases)} tests ran in {t_end-t_start:.3f}s, "+
          f"{tests_skipped} skipped, {tests_passed} passed, "+
          f"{tests_improved} improved, {tests_failed} failed.")

if __name__ == '__main__':
    print(f"\nTester version {version}\n")

    check_duplicate_tests()
    run_test_suite()
