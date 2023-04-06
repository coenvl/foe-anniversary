#!python3
import types
from enum import Enum, Flag
from timeit import default_timer as timer
from typing import Tuple, List

# active solver
from solver import solve
#from mooing15 import solve
#from my_solver import solve
#from solver_v31 import solve

# reference solver by MooingCat
import mooing15 as solver_mooing15
# other reference solvers used to establish best results in dev mode
#import my_solver as solver_my
import solver as solver_optimized_bruteforce
#import solver_v31


version = "v1.1"


def get_solvers() -> List[types.FunctionType]:
    solvers = [val.solve for name, val in globals().items() if name.startswith("solver_") and isinstance(val, types.ModuleType) and val.solve and isinstance(val.solve, types.FunctionType)]
    # active solver is imported directly, insert it at second position after the MooingCat's solver, because it's the fastest, which is useful with PERF tests to get a quick baseline result
    solvers.insert(1, solve)
    return solvers


class TestCaseType(Flag):
    NONE = 0
    SKIP = 1
    DEV = 2  # instead of running the test and comparing the results, run all imported solvers with the input to find out the results
    FOCUS = 4  # to be able to mark test(s) selectively and run only it/them
    BASE = 8  # manually crafted tests focusing on some feature
    FULL = 16  # full boards as gotten from the game
    PERF = 32  # performance tests, usually tests containing lots of gems leading to lots of possibilities, thus longer running times
    ALL = DEV | FOCUS | BASE | FULL | PERF

run_testcases_and = TestCaseType.ALL
#run_testcases_and = TestCaseType.ALL ^ TestCaseType.PERF  # don't run PERF tests
#run_testcases_and = TestCaseType.ALL | TestCaseType.SKIP  # run skipped tests as well
run_testcases_or = TestCaseType.ALL  # run everything
#run_testcases_or = TestCaseType.DEV  # run only tests under development
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
        self.tctype = tctype
        self.locked_bottom = locked_bottom
        self.locked_top = locked_top
        self.free = free
        self.free_bottom = free_bottom
        self.free_top = free_top
        self.free_full = free_full
        self.keys = keys
        self.max_keys = max_keys
        self.progress = progress
        self.potential_progress = potential_progress
        self.unlocked_part = unlocked_part
        self.unlocked_empty = unlocked_empty

    def is_dev(self) -> bool:
        return self.tctype & TestCaseType.DEV != TestCaseType.NONE;

    def _run_dev(self) -> str:
        for solver in get_solvers():
            print(f"\n\t\033[35mRunning test '{self.name}' with solver {solver.__module__}:\033[0m")
            tStart = timer()
            # MooingCat's solver expects lists and modifies them, so need to copy & transform the inputs
            try:
                print(solver(list(self.locked_bottom), list(self.locked_top), list(self.free), list(self.free_bottom), list(self.free_top), list(self.free_full)))
            except KeyboardInterrupt:
                print("Solver interrupted by the user!")
            tEnd = timer()
            print(f"Elapsed time: {tEnd-tStart:.3f}s")
        return f"{self.DONE} '{self.name}'"

    def _run_skip(self) -> str:
        return f"{self.SKIP} '{self.name}'"

    @staticmethod
    def _compare(rr:RunResult, rrstr:List[str], expected_value, got_value, name:str) -> RunResult:
        if (got_value < expected_value):
            rrstr.append(f"Expected {expected_value} {name}, got {got_value}.")
            return RunResult.FAIL
        elif (got_value > expected_value):
            rrstr.append(f"Expected {expected_value} {name}, got more ({got_value}).")
            return rr.try_impr()
        return rr

    def _run_normal(self) -> Tuple[str, int, int, int, int]:
        rr = RunResult.PASS
        rrstr: List[str] = []
        tStart = timer()
        try:
            # MooingCat's solver expects lists and modifies them, so need to copy & transform the inputs
            result = solve(list(self.locked_bottom), list(self.locked_top), list(self.free), list(self.free_bottom), list(self.free_top), list(self.free_full), True)
            result_keys = result[0]
            result_max_keys = result[2]
            result_progress = result[3]
            result_potential_progress = result[4]
            result_unlocked_part = result[6]
            result_unlocked_empty = result[7]

            rr = self._compare(rr, rrstr, self.keys, result_keys, "keys")
            rr = self._compare(rr, rrstr, self.max_keys, result_max_keys, "max_keys")
            rr = self._compare(rr, rrstr, self.progress, result_progress, "progress")
            rr = self._compare(rr, rrstr, self.potential_progress, result_potential_progress, "potential_progress")
            rr = self._compare(rr, rrstr, self.unlocked_part, result_unlocked_part, "unlocked_part")
            rr = self._compare(rr, rrstr, self.unlocked_empty, result_unlocked_empty, "unlocked_empty")
        except KeyboardInterrupt:
            rr = RunResult.FAIL
            rrstr = ["Solver interrupted by the user!"]
        finally:
            tEnd = timer()

        status, p, i, f = ((self.PASS, 1, 0, 0) if rr == RunResult.PASS else ((self.IMPR, 0, 1, 0) if rr == RunResult.IMPR else (self.FAIL, 0, 0, 1)))
        if rrstr:
            rrstr.insert(0, " -")
        return (f"{status} '{self.name}' in {tEnd-tStart:.3f}s{' '.join(rrstr)}", 0, p, i, f)

    def run(self, mask_and: TestCaseType, mask_or: TestCaseType) -> Tuple[str, int, int, int, int]:
        if (self.tctype & mask_and != self.tctype) or (self.tctype & mask_or == TestCaseType.NONE):
            return (self._run_skip(), 1, 0, 0, 0)
        if self.is_dev():
            return (self._run_dev(), 0, 1, 0, 0)
        return self._run_normal()


testcases: List[TestCase] = [
    TestCase(name="empty board", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,0,0), free=(0,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=0, potential_progress=0,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L1 bottom", tctype=TestCaseType.BASE,
        locked_bottom=(1,0,0,0), locked_top=(0,0,0,0), free=(0,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=0, potential_progress=1,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L1 top", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(1,0,0,0), free=(0,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=0, potential_progress=1,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L1 free", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,0,0), free=(1,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=0, potential_progress=0,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="one L1 bot merge", tctype=TestCaseType.BASE,
        locked_bottom=(1,0,0,0), locked_top=(0,0,0,0), free=(1,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=1, potential_progress=1,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="one L1 top merge", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(1,0,0,0), free=(1,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=1, potential_progress=1,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="two L1 free", tctype=TestCaseType.BASE,  # prefer leaving unlocked unmerged gems for a clear board bonus purposes
        locked_bottom=(0,0,0,0), locked_top=(0,0,0,0), free=(2,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=0, potential_progress=0,
        unlocked_part = 0, unlocked_empty = 2
    ),
    TestCase(name="one L1 bot L2 top merge", tctype=TestCaseType.BASE,
        locked_bottom=(1,0,0,0), locked_top=(0,1,0,0), free=(1,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=1, max_keys=3, progress=2, potential_progress=2,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L1 top L2 bot merge", tctype=TestCaseType.BASE,
        locked_bottom=(0,1,0,0), locked_top=(1,0,0,0), free=(1,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=1, max_keys=3, progress=2, potential_progress=2,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L2 bot L3 top merge", tctype=TestCaseType.BASE,
        locked_bottom=(0,1,0,0), locked_top=(0,0,1,0), free=(0,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=2, potential_progress=2,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L2 top L3 bot merge", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,1,0), locked_top=(0,1,0,0), free=(0,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=2, potential_progress=2,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L3 bot L4 top merge", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,1,0), locked_top=(0,0,0,1), free=(0,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=3, potential_progress=3,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L3 top L4 bot merge", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(0,0,1,0), free=(0,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=3, potential_progress=3,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L4 top L4 bot merge", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(0,0,0,1), free=(0,0,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=4, potential_progress=4,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="two L1 top L2 bot merges into L4", tctype=TestCaseType.BASE,  # prefer merging two L3 fulls into one L4
        locked_bottom=(2,0,0,0), locked_top=(0,2,0,0), free=(2,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=6, progress=4, potential_progress=4,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="two L1 bot L2 top merges into L4", tctype=TestCaseType.BASE,
        locked_bottom=(0,2,0,0), locked_top=(2,0,0,0), free=(2,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=6, progress=4, potential_progress=4,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="one L1 top ignores free L2", tctype=TestCaseType.BASE,
        locked_bottom=(1,0,0,0), locked_top=(0,0,0,0), free=(1,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=1, potential_progress=1,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="one L1 bot ignores free L2", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(1,0,0,0), free=(1,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=1, potential_progress=1,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="one L2 top ignores free L3", tctype=TestCaseType.BASE,
        locked_bottom=(0,1,0,0), locked_top=(0,0,0,0), free=(0,1,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=1, potential_progress=1,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="one L2 bot ignores free L3", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,1,0,0), free=(0,1,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=1, potential_progress=1,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="one L3 top ignores free L4", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,1,0), locked_top=(0,0,0,0), free=(0,0,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=1, potential_progress=1,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="one L3 bot ignores free L4", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,1,0), free=(0,0,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=1, potential_progress=1,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="gobble locked L4 bot with free", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(0,0,0,0), free=(0,0,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=2, potential_progress=2,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 top with free", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,0,1), free=(0,0,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=2, potential_progress=2,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 bots with free", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,2), locked_top=(0,0,0,0), free=(0,0,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=4, potential_progress=4,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 tops with free", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,0,2), free=(0,0,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=4, potential_progress=4,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 bot with bot", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,1,1), locked_top=(0,0,0,0), free=(0,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=3, potential_progress=3,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 top with top", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,1,1), free=(0,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=3, potential_progress=3,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 bots with bot", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,1,2), locked_top=(0,0,0,0), free=(0,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=5, potential_progress=5,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 tops with top", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,1,2), free=(0,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=5, potential_progress=5,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 bot with full", tctype=TestCaseType.BASE,
        locked_bottom=(0,1,0,1), locked_top=(0,0,1,0), free=(0,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=4, potential_progress=4,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 top with full", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,1,0), locked_top=(0,1,0,1), free=(0,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=4, potential_progress=4,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 bots with full", tctype=TestCaseType.BASE,
        locked_bottom=(0,1,0,2), locked_top=(0,0,1,0), free=(0,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=6, potential_progress=6,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="gobble locked L4 tops with full", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,1,0), locked_top=(0,1,0,2), free=(0,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=6, potential_progress=6,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="leave free L4 unmerged", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,0,0), free=(0,0,0,2),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=0, potential_progress=0,
        unlocked_part = 0, unlocked_empty = 2
    ),
    TestCase(name="leave free L4 unmerged in presence of merged key", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(0,0,0,1), free=(0,0,0,3),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=4, potential_progress=4,
        unlocked_part = 0, unlocked_empty = 2
    ),
    TestCase(name="leave free L1-4 unmerged", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,0), locked_top=(0,0,0,0), free=(2,2,2,2),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=0, potential_progress=0,
        unlocked_part = 0, unlocked_empty = 8
    ),
    TestCase(name="leave free L1-4 unmerged in presence of merged key", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(0,0,0,1), free=(2,2,2,3),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=4, potential_progress=4,
        unlocked_part = 0, unlocked_empty = 8
    ),
    TestCase(name="leave free L1-2, merge free L3 for L4 key", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(0,0,0,1), free=(2,2,4,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=4, potential_progress=4,
        unlocked_part = 0, unlocked_empty = 6
    ),
    TestCase(name="leave free L2 bot unmerged, merge free L2 for L4 key", tctype=TestCaseType.BASE,
        locked_bottom=(2,0,0,1), locked_top=(0,0,0,1), free=(2,2,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=6, potential_progress=6,
        unlocked_part = 2, unlocked_empty = 0
    ),
    TestCase(name="leave free L2 top unmerged, merge free L2 for L4 key", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(2,0,0,1), free=(2,2,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=6, potential_progress=6,
        unlocked_part = 2, unlocked_empty = 0
    ),
    TestCase(name="unmerged top is better than unmerged empty", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(1,0,0,1), free=(1,2,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=5, potential_progress=5,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="unmerged bot is better than unmerged empty", tctype=TestCaseType.BASE,
        locked_bottom=(1,0,0,1), locked_top=(0,0,0,1), free=(1,2,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=5, potential_progress=5,
        unlocked_part = 1, unlocked_empty = 0
    ),
    # numbers technically based on clear board reward (1 key per 10 empty gems, 1 key per 4 gems with a key part)
    # but still it's rare, circumstential and debatable
    TestCase(name="one unmerged top is better than two unmerged empties", tctype=TestCaseType.BASE,
        locked_bottom=(0,0,0,1), locked_top=(1,0,0,1), free=(3,1,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=5, potential_progress=5,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="one unmerged bot is better than two unmerged empties", tctype=TestCaseType.BASE,
        locked_bottom=(1,0,0,1), locked_top=(0,0,0,1), free=(3,1,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=5, potential_progress=5,
        unlocked_part = 1, unlocked_empty = 0
    ),


    # boards from comments at https://www.mooingcatguides.com/event-guides/2023-anniversary-event-guide#comments
    TestCase(name="comment-6153598555 by Centaurus", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(3,3,0,2), locked_top=(4,3,1,1), free=(1,2,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=10, max_keys=24, progress=11, potential_progress=20,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="comment-6152735906 by Stella Yolanda Zonker", tctype=TestCaseType.FULL,
        locked_bottom=(2,1,0,0), locked_top=(2,2,1,1), free=(0,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=9, progress=3, potential_progress=10,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="comment-6151362161 by szevasz", tctype=TestCaseType.FULL,
        locked_bottom=(0,0,1,0), locked_top=(1,0,2,1), free=(2,2,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=4, potential_progress=6,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="comment-6149964806 by Muche", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(1,1,1,2), locked_top=(2,5,1,1), free=(4,0,3,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=15, max_keys=15, progress=14, potential_progress=17,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="comment-6149249510 by Muche", tctype=TestCaseType.FULL,
        locked_bottom=(3,1,0,1), locked_top=(4,0,0,0), free=(3,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=4, max_keys=12, progress=6, potential_progress=10,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="comment-6148461376 by Stella Yolanda Zonker", tctype=TestCaseType.FULL,
        locked_bottom=(1,2,0,1), locked_top=(0,0,2,0), free=(1,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=6, progress=5, potential_progress=7,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="comment-6148124724 by Max Barbarian", tctype=TestCaseType.FULL,
        locked_bottom=(1,2,1,3), locked_top=(0,1,2,0), free=(0,1,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=9, progress=9, potential_progress=13,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="comment-6147057517 by Rigel Blue", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(4,0,1,2), locked_top=(2,1,2,1), free=(2,6,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=12, max_keys=18, progress=12, potential_progress=16,
        unlocked_part = 1, unlocked_empty = 4
    ),
    TestCase(name="comment-6153869993 by Stella Yolanda Zonker", tctype=TestCaseType.FULL,
        locked_bottom=(0,2,2,1), locked_top=(3,1,1,0), free=(4,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=15, progress=11, potential_progress=11,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="comment-6155079334 by MarkusS", tctype=TestCaseType.FULL,
        locked_bottom=(1,0,0,2), locked_top=(1,3,2,0), free=(4,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=7, max_keys=9, progress=11, potential_progress=11,
        unlocked_part = 0, unlocked_empty = 0
    ),


    # some of my boards
    TestCase(name="tc1", tctype=TestCaseType.FULL,
        locked_bottom=(0,3,1,3), locked_top=(1,0,0,0), free=(1,0,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=9, potential_progress=11,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="tc2", tctype=TestCaseType.FULL,
        locked_bottom=(2,0,2,3), locked_top=(1,0,1,0), free=(4,0,2,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=6, progress=12, potential_progress=12,
        unlocked_part = 3, unlocked_empty = 1
    ),
    TestCase(name="tc3", tctype=TestCaseType.FULL,
        locked_bottom=(2,0,0,2), locked_top=(0,0,1,1), free=(4,0,0,2),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=6, progress=9, potential_progress=9,
        unlocked_part = 2, unlocked_empty = 0
    ),
    TestCase(name="tc4", tctype=TestCaseType.FULL,
        locked_bottom=(0,1,0,0), locked_top=(0,3,1,1), free=(3,1,1,2),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=5, potential_progress=7,
        unlocked_part = 2, unlocked_empty = 3
    ),
    TestCase(name="tc5", tctype=TestCaseType.FULL,
        locked_bottom=(0,1,0,0), locked_top=(3,3,3,2), free=(1,3,2,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=12, potential_progress=14,
        unlocked_part = 5, unlocked_empty = 0
    ),
    TestCase(name="tc6", tctype=TestCaseType.FULL,
        locked_bottom=(2,1,1,0), locked_top=(5,0,0,0), free=(4,2,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=12, progress=6, potential_progress=9,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc7", tctype=TestCaseType.FULL,
        locked_bottom=(0,3,0,0), locked_top=(0,3,0,0), free=(2,1,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=9, progress=2, potential_progress=6,
        unlocked_part = 0, unlocked_empty = 2
    ),
    TestCase(name="tc8 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(3,4,4,1), locked_top=(1,3,0,1), free=(4,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=13, max_keys=15, progress=17, potential_progress=19,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc9", tctype=TestCaseType.FULL,
        locked_bottom=(0,1,0,1), locked_top=(1,0,0,2), free=(1,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=1, max_keys=6, progress=2, potential_progress=8,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="tc10 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(2,2,4,1), locked_top=(1,0,2,1), free=(9,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=12, max_keys=12, progress=14, potential_progress=15,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc11", tctype=TestCaseType.FULL,
        locked_bottom=(3,2,2,1), locked_top=(5,1,0,0), free=(3,0,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=18, progress=10, potential_progress=15,
        unlocked_part = 1, unlocked_empty = 0
    ),
    # some solver versions display L4 merges in an order that is not user-friendly, i.e. first merges use L4 fullgem which is created in the last displayed L4 merge
    # currently there is no automated way of checking it
    TestCase(name="tc12 displayorder", tctype=TestCaseType.FULL,
        locked_bottom=(1,0,0,2), locked_top=(1,3,0,1), free=(0,2,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=9, progress=8, potential_progress=11,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc13 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(1,1,1,0), locked_top=(1,1,1,3), free=(5,1,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=9, progress=12, potential_progress=12,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="tc14 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(2,3,1,0), locked_top=(2,0,1,2), free=(2,3,2,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=12, max_keys=15, progress=11, potential_progress=13,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc15", tctype=TestCaseType.FULL,
        locked_bottom=(3,1,2,0), locked_top=(3,2,0,1), free=(1,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=18, progress=7, potential_progress=13,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc16", tctype=TestCaseType.FULL,
        locked_bottom=(1,1,0,2), locked_top=(1,2,1,0), free=(1,0,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=4, max_keys=12, progress=7, potential_progress=10,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc17", tctype=TestCaseType.FULL,
        locked_bottom=(1,0,2,2), locked_top=(0,2,2,1), free=(3,1,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=15, progress=11, potential_progress=13,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc18", tctype=TestCaseType.FULL,
        locked_bottom=(3,1,1,0), locked_top=(2,3,0,1), free=(2,2,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=15, progress=9, potential_progress=12,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc19", tctype=TestCaseType.FULL,
        locked_bottom=(1,3,0,3), locked_top=(0,0,2,1), free=(3,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=9, progress=13, potential_progress=14,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc20", tctype=TestCaseType.FULL,
        locked_bottom=(4,0,1,3), locked_top=(3,0,0,0), free=(2,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=9, progress=9, potential_progress=14,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc21", tctype=TestCaseType.FULL,
        locked_bottom=(3,0,1,2), locked_top=(0,3,0,0), free=(5,0,3,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=9, progress=11, potential_progress=11,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="tc22", tctype=TestCaseType.FULL,
        locked_bottom=(1,3,0,0), locked_top=(1,1,2,3), free=(3,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=12, progress=12, potential_progress=14,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="tc23", tctype=TestCaseType.FULL,
        locked_bottom=(3,2,3,0), locked_top=(1,2,0,1), free=(3,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=12, progress=11, potential_progress=13,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc24 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(2,2,3,2), locked_top=(2,4,2,0), free=(5,3,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=18, max_keys=24, progress=19, potential_progress=19,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="tc25 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(1,1,2,4), locked_top=(2,2,0,2), free=(3,1,4,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=13, max_keys=18, progress=20, potential_progress=20,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc26 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(1,3,2,1), locked_top=(2,2,2,1), free=(7,0,4,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=19, max_keys=21, progress=16, potential_progress=16,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc27 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(0,1,2,2), locked_top=(3,3,1,1), free=(3,1,4,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=15, max_keys=15, progress=16, potential_progress=16,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc28", tctype=TestCaseType.FULL,
        locked_bottom=(0,1,3,0), locked_top=(1,0,0,2), free=(4,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=9, progress=8, potential_progress=9,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="tc29", tctype=TestCaseType.FULL,
        locked_bottom=(1,2,2,2), locked_top=(3,1,0,1), free=(2,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=7, max_keys=15, progress=13, potential_progress=15,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc30", tctype=TestCaseType.FULL,
        locked_bottom=(2,0,2,1), locked_top=(2,1,1,2), free=(4,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=15, progress=14, potential_progress=14,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc31", tctype=TestCaseType.FULL,
        locked_bottom=(3,1,3,1), locked_top=(2,1,0,1), free=(6,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=10, max_keys=12, progress=14, potential_progress=14,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="tc32", tctype=TestCaseType.FULL,
        locked_bottom=(1,1,1,0), locked_top=(3,1,1,1), free=(4,0,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=7, max_keys=9, progress=10, potential_progress=10,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc33", tctype=TestCaseType.FULL,
        locked_bottom=(0,2,2,1), locked_top=(3,2,0,0), free=(4,2,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=10, max_keys=15, progress=11, potential_progress=11,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="tc34", tctype=TestCaseType.FULL,
        locked_bottom=(1,2,0,1), locked_top=(1,4,3,0), free=(4,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=10, max_keys=12, progress=11, potential_progress=13,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc35", tctype=TestCaseType.FULL,
        locked_bottom=(2,0,2,3), locked_top=(1,1,0,1), free=(1,1,2,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=9, progress=12, potential_progress=14,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="tc36", tctype=TestCaseType.FULL,
        locked_bottom=(1,0,1,0), locked_top=(1,2,1,3), free=(1,0,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=6, progress=9, potential_progress=12,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc37 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(1,2,5,3), locked_top=(1,2,4,0), free=(3,2,2,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=18, max_keys=21, progress=18, potential_progress=21,
        unlocked_part = 1, unlocked_empty = 1
    ),
    TestCase(name="tc38", tctype=TestCaseType.FULL,
        locked_bottom=(1,1,1,0), locked_top=(1,1,0,0), free=(2,3,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=6, progress=5, potential_progress=5,
        unlocked_part = 1, unlocked_empty = 2
    ),
    TestCase(name="tc39", tctype=TestCaseType.FULL,
        locked_bottom=(0,0,0,0), locked_top=(3,0,0,1), free=(1,1,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=3, potential_progress=5,
        unlocked_part = 2, unlocked_empty = 2
    ),
    TestCase(name="tc40", tctype=TestCaseType.FULL,
        locked_bottom=(0,2,0,1), locked_top=(4,3,5,0), free=(2,2,4,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=9, progress=13, potential_progress=16,
        unlocked_part = 4, unlocked_empty = 2
    ),
    TestCase(name="tc41", tctype=TestCaseType.FULL,
        locked_bottom=(1,3,1,2), locked_top=(2,2,1,1), free=(3,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=7, max_keys=18, progress=14, potential_progress=16,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc42", tctype=TestCaseType.FULL,
        locked_bottom=(3,0,5,0), locked_top=(2,2,2,0), free=(0,2,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=18, progress=4, potential_progress=14,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc43 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(2,1,1,2), locked_top=(1,1,1,1), free=(4,3,2,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=12, max_keys=12, progress=13, potential_progress=13,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="tc44", tctype=TestCaseType.FULL,
        locked_bottom=(1,1,0,0), locked_top=(4,2,0,0), free=(2,1,2,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=6, progress=5, potential_progress=8,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc45", tctype=TestCaseType.FULL,
        locked_bottom=(0,0,0,2), locked_top=(1,0,0,0), free=(3,0,2,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=3, max_keys=3, progress=5, potential_progress=5,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="tc46", tctype=TestCaseType.FULL,
        locked_bottom=(2,1,1,0), locked_top=(0,3,0,0), free=(4,2,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=9, progress=7, potential_progress=7,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc47 perf", tctype=TestCaseType.FULL | TestCaseType.PERF,
        locked_bottom=(1,6,2,4), locked_top=(1,2,3,3), free=(6,6,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=21, max_keys=27, progress=29, potential_progress=29,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc48", tctype=TestCaseType.FULL,
        locked_bottom=(2,0,1,0), locked_top=(1,0,1,1), free=(4,2,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=6, max_keys=9, progress=7, potential_progress=7,
        unlocked_part = 2, unlocked_empty = 1
    ),
    TestCase(name="tc49", tctype=TestCaseType.FULL,
        locked_bottom=(4,2,5,1), locked_top=(1,1,1,1), free=(1,2,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=12, progress=11, potential_progress=18,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc50", tctype=TestCaseType.FULL,
        locked_bottom=(1,2,0,0), locked_top=(2,1,2,2), free=(5,1,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=9, progress=12, potential_progress=12,
        unlocked_part = 0, unlocked_empty = 0
    ),
    TestCase(name="tc51", tctype=TestCaseType.FULL,
        locked_bottom=(3,2,0,1), locked_top=(1,1,1,2), free=(4,0,0,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=15, progress=14, potential_progress=14,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc52", tctype=TestCaseType.FULL,
        locked_bottom=(1,3,1,0), locked_top=(4,0,1,0), free=(2,1,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=9, max_keys=15, progress=7, potential_progress=10,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="tc53", tctype=TestCaseType.FULL,
        locked_bottom=(0,0,3,2), locked_top=(2,1,2,1), free=(2,1,2,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=12, max_keys=15, progress=13, potential_progress=14,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc54", tctype=TestCaseType.FULL,
        locked_bottom=(2,1,1,0), locked_top=(0,1,1,2), free=(2,0,1,1),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=7, max_keys=12, progress=10, potential_progress=10,
        unlocked_part = 1, unlocked_empty = 0
    ),
    TestCase(name="tc55", tctype=TestCaseType.FULL,
        locked_bottom=(1,2,3,1), locked_top=(2,1,1,1), free=(4,0,1,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=12, max_keys=15, progress=14, potential_progress=14,
        unlocked_part = 0, unlocked_empty = 1
    ),
    TestCase(name="tc56", tctype=TestCaseType.FULL,
        locked_bottom=(2,2,2,1), locked_top=(3,1,0,1), free=(5,0,2,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=12, max_keys=15, progress=14, potential_progress=14,
        unlocked_part = 0, unlocked_empty = 0
    ),

]
"""
    # template is block-commented out, because it's technically a duplicate of empty board testcase
    #  it's also out of list, as its "block-comment" is a docstring, not a real comment
    # template has listed most of types for easier usage - removing unneeded ones instead of adding needed one
    TestCase(name="template", tctype=TestCaseType.FULL | TestCaseType.FOCUS | TestCaseType.DEV,
        locked_bottom=(0,0,0,0), locked_top=(0,0,0,0), free=(0,0,0,0),
        free_bottom=(0,0,0,0), free_top=(0,0,0,0), free_full=(0,0,0,0),
        keys=0, max_keys=0, progress=0, potential_progress=0,
        unlocked_part = 0, unlocked_empty = 0
    ),
"""


def check_duplicate_tests():
    """ check tests for duplicates (inputs, or names) """
    tests_inputs = {}  # dictionary of tests, key is tuple of test's inputs, value is tuple (index, test)
    tests_name = {}  # dictionary of tests, key is str of test's name, value is tuple (index, test)
    for i, test in enumerate(testcases):
        try:
            key_inputs = (test.locked_bottom, test.locked_top, test.free, test.free_bottom, test.free_top, test.free_full)
        except Exception as e:
            print(f"Error accessing test #{i} '{test}' - ", e)
            continue
        if key_inputs in tests_inputs:
            # duplicate found
            test_orig = tests_inputs[key_inputs]
            print(f"Test #{i+1} '{test.name}' ({test.tctype}) is a duplicate of #{test_orig[0]+1} '{test_orig[1].name}' ({test_orig[1].tctype})")
        else:
            tests_inputs[key_inputs] = (i, test)

        try:
            key_name = test.name
        except Exception as e:
            print(f"Error accessing test #{i} '{test}' - ", e)
            continue
        if key_name in tests_name:
            # duplicate found
            test_orig = tests_name[key_name]
            print(f"Test #{i+1} '{test.name}' ({test.tctype}) has the same name as #{test_orig[0]+1} '{test_orig[1].name}' ({test_orig[1].tctype})")
        else:
            tests_name[key_name] = (i, test)


if __name__ == '__main__':
    print(f"\nTester version {version}\n")

    check_duplicate_tests()

    tests_skipped=0
    tests_passed = 0
    tests_improved = 0
    tests_failed = 0
    width = len(f"{len(testcases)+1}")
    tStart = timer()
    for i, testcase in enumerate(testcases):
        result, sk, pa, im, fa = testcase.run(run_testcases_and, run_testcases_or)
        tests_skipped += sk
        tests_passed += pa
        tests_improved += im
        tests_failed += fa
        print(f"#{i+1: >{width}} {result}")
    tEnd = timer()
    print(f"\nSummary: {len(testcases)} tests ran in {tEnd-tStart:.3f}s, {tests_skipped} skipped, {tests_passed} passed, {tests_improved} improved, {tests_failed} failed.")
