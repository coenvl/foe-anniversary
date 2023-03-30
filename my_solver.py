""" Solver for the FOE anniversary event """
from typing import Tuple

class Solver():
    """ Contains the state of the game and the solver """

    def __init__(self, locked_bottom, locked_top, free, free_bottom, free_top, free_full, silent: bool = False):
        self.max = 3 * min(sum(locked_bottom),sum(locked_top))
        self.starting = 3 * sum(free)
        self.max_progress = sum(locked_bottom) + sum(locked_top) + locked_bottom[3] + locked_top[3]

        self.locked_bottom = locked_bottom
        self.locked_top = locked_top

        self.free = free
        self.free_bottom = free_bottom
        self.free_top = free_top
        self.free_full = free_full

        self.silent = silent
        self._print('Running optimized solver')
        if not silent:
            self.help()

    def _print(self, msg):
        if not self.silent:
            print(msg)
        return True

    def help(self):
        print("==Explanation==")
        print('"Free" = Gem you can merge with other gems')
        print('"Locked" = Locked gem')
        print('"Bot" = Gem has bottom key piece')
        print('"Top" = Gem has top key piece')
        print('"Full" = Gem has a full key')

        print("Merges should be done in the order below, starting with level 1 gems")
        print("\n===NOTE===")
        print('There has been some confusion on what is the "top" and "bot" key piece. ' +
              'As long as you are consistent, it does not matter which you use, though ' +
              'in-game the round colored piece is "bot" and the tip of the key "top"')

    def solve(self) -> Tuple[int]:
        """ Solve the problem """
        self._solve_level(0)
        self._solve_level(1)
        self._solve_level(2)
        self._solve_last_level()

        self._print("==Results==")

        res = self.free_full[2] + self.free_full[3]

        if res == self.max:
            self._print(f"Keys: {res}/{self.max} (Maximum keys picked up)")
        elif res == self.starting:
            self._print(f"Keys: {res}/{self.max} (Maximum keys picked up with gems spawned)")
        else:
            self._print(f"Keys: {res}/{self.max} (Likely best possible solution with gems spawned)")

        if self.free_full[2] > 0:
            if self.free_full[2] == 1:
                self._print(f"- Level 3: {self.free_full[2]} key")
            else:
                self._print(f"- Level 3: {self.free_full[2]} keys")
        if self.free_full[3] > 0:
            if self.free_full[3] == 1:
                self._print(f"- Level 4: {self.free_full[3]} key")
            else:
                self._print(f"- Level 4: {self.free_full[3]} keys")

        remaining_progress = sum(self.locked_bottom) + sum(self.locked_top) + self.locked_bottom[3] + self.locked_top[3]
        total_progress = self.max_progress - remaining_progress
        remaining_locked = sum(self.locked_bottom) + sum(self.locked_top)

        self._print(f"Progress: {total_progress}/{self.max_progress} ({remaining_locked} remaining locked gems)")
        self._print("Keep in mind these results are only for the selected color")
        return (res, self.starting, self.max, total_progress, self.max_progress, remaining_locked)

    def _solve_level(self, level):
        self._print(f"==Level {level + 1} Merges==")
        while True:
            if self._make_full_keys(level):
                continue
            if self._unlock_tiles(level):
                continue
            if self._use_free_tiles(level):
                continue
            else:
                break

    def _solve_last_level(self):
        self._print("==Level 4 Merges==")
        level = 3
        while True:
            if self._make_full_keys(level, level):
                continue
            if self._unlock_tiles(level, level):
                continue
            if self.free_full[level] > 0 and self.locked_bottom[level] > 0:
                self.locked_bottom[level] -= 1
                self._print("Free L4 Full + Locked L4 Bot")
            elif self.free_full[level] > 0 and self.locked_top[level] > 0:
                self.locked_top[level] -= 1
                self._print("Free L4 Full + Locked L4 Top")
            else:
                break

    # Sub functions used by level solvers

    def _make_full_keys(self, level: int, to_level: int = None) -> bool:
        """ Find any combinations to make full keys """
        if to_level is None:
            to_level = level + 1

        if self.free_top[level] > 0 and self.locked_bottom[level] > 0:
            self.free_top[level] -= 1
            self.locked_bottom[level] -= 1
            self.free_full[to_level] += 1
            return self._print(f"Free L{level + 1} Top + Locked L{level + 1} Bot")

        if self.free_bottom[level] > 0 and self.locked_top[level] > 0:
            self.free_bottom[level] -= 1
            self.locked_top[level] -= 1
            self.free_full[to_level] += 1
            return self._print(f"Free L{level + 1} Bot + Locked L{level + 1} Top")

        if self.free_bottom[level] > 0 and self.free_top[level] > 0:
            self.free_bottom[level] -= 1
            self.free_top[level] -= 1
            self.free_full[to_level] += 1
            return self._print(f"Free L{level + 1} Bot + Free L{level + 1} Top")

        return False

    def _unlock_tiles(self, level: int, to_level: int = None) -> bool:
        """ Unlock remaining tiles """
        if to_level is None:
            to_level = level + 1

        # We already know we cannot make full keys, so to unlock we must have empty free gems
        if self.free[level] > 0 and self.locked_top[level] + self.locked_bottom[level] > 0:
            if self._prefer_unlock_top(level):
                self.free[level] -= 1
                self.locked_top[level] -= 1
                self.free_top[to_level] += 1
                return self._print(f"Free L{level + 1} + Locked L{level + 1} Top")

            self.free[level] -= 1
            self.locked_bottom[level] -= 1
            self.free_bottom[to_level] += 1
            return self._print(f"Free L{level + 1} + Locked L{level + 1} Bot")

        if self.free_top[level] > 0 and self.locked_top[level] > 0:
            self.locked_top[level] -= 1
            self.free_top[level] -= 1
            self.free_top[to_level] += 1
            return self._print(f"Free L{level + 1} Top + Locked L{level + 1} Top")

        if self.free_bottom[level] > 0 and self.locked_bottom[level] > 0:
            self.locked_bottom[level] -= 1
            self.free_bottom[level] -= 1
            self.free_bottom[to_level] += 1
            return self._print(f"Free L{level + 1} Bot + Locked L{level + 1} Bot")

        return False

    def _prefer_unlock_top(self, level: int):
        """ Wether to prefer top pieces or bottom pieces """

        if self.locked_top[level] == 0:
            return False
        if self.locked_bottom[level] == 0:
            return True
        if self._total_available_top(level + 1) != self._total_available_bottom(level + 1):
            return self._total_available_top(level + 1) < self._total_available_bottom(level + 1)
        if self._total_locked_top(level + 1) != self._total_locked_bottom(level + 1):
            return self._total_locked_top(level) > self._total_locked_bottom(level)
        return True

    def _use_free_tiles(self, level: int, to_level: int = None) -> bool:
        """ Use up any remaining free tiles """
        if to_level is None:
            to_level = level + 1

        if self.free_bottom[level] > 0 and self.free[level] > 0:
            self.free_bottom[level] -= 1
            self.free[level] -= 1
            self.free_bottom[to_level] += 1
            return self._print(f"Free L{level + 1} + Free L{level + 1} Bot")

        if self.free_top[level] > 0 and self.free[level] > 0:
            self.free_top[level] -= 1
            self.free[level] -= 1
            self.free_top[to_level] += 1
            return self._print(f"Free L{level + 1} + Free L{level + 1} Top")

        if self.free[level] >= 2:
            self.free[level] -= 2
            self.free[to_level] += 1
            return self._print(f"Free L{level + 1} + Free L{level + 1}")

        if self.free_top[level] >= 2:
            self.free_top[level] -= 2
            self.free_top[to_level] += 1
            return self._print(f"Free L{level + 1} Top + Free L{level + 1} Top")

        if self.free_bottom[level] >= 2:
            self.free_bottom[level] -= 2
            self.free_bottom[to_level] += 1
            return self._print(f"Free L{level + 1} Bot + Free L{level + 1} Bot")

        return False

    def _total_locked_bottom(self, from_level: int = 0) -> int:
        return sum(self.locked_bottom[from_level:])

    def _total_locked_top(self, from_level: int = 0) -> int:
        return sum(self.locked_top[from_level:])

    def _total_available_bottom(self, from_level: int = 0) -> int:
        return sum(self.locked_bottom[from_level:]) + sum(self.free_bottom[from_level:])

    def _total_available_top(self, from_level: int = 0) -> int:
        return sum(self.locked_top[from_level:]) + sum(self.free_top[from_level:])

def solve(locked_bottom,locked_top,free,free_bottom,free_top,free_full,silent=False) -> Tuple[int]: #pylint: disable=unused-argument
    solver = Solver(locked_bottom,locked_top,free,free_bottom,free_top,free_full)
    return solver.solve()
