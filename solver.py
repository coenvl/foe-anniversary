""" Solver for the FOE anniversary event """
from __future__ import annotations
from math import ceil
from typing import Tuple, List, Set
from enum import Enum

class Part(Enum):
    EMPTY = 0
    TOP = 1
    BOT = 2
    FULL = 3

# @functools.total_ordering
class Gem():
    def __init__(self, level: int, part: Part, locked: bool):
        self.level = level
        self.part = part
        self.locked = locked
        self.moves = []

    def can_merge_with(self, other: Gem) -> bool:
        return self.level == other.level and not (self.locked and other.locked)

    def __hash__(self) -> int:
        return self.level + self.part.value + self.locked

    def __eq__(self, other: Gem):
        return self.level == other.level and self.part == other.part and self.locked == other.locked

    def __lt__(self, other: Gem):
        """ Compare first based on level, then lock, then part """
        if self.level == other.level:
            if self.locked == other.locked:
                return self.part.value < other.part.value
            return self.locked < other.locked
        return self.level < other.level

    def __repr__(self):
        value = f"{'Locked' if self.locked else 'Free'} L{self.level + 1}"
        if self.part != Part.EMPTY:
            return f"{value} {self.part.name.capitalize()}"
        return value

class MergedGem(Gem):
    def __init__(self, one: Gem, two: Gem):
        assert one.level == two.level
        super().__init__(min(3,one.level + 1), Part(one.part.value | two.part.value), False)
        self.moves = one.moves + two.moves + [f"{one} + {two}"]

class State():
    def __init__(self, state: State = None, move: Tuple[Gem, Gem] = None):
        if state is None:
            self.gems: List[Gem] = []
        else:
            self.gems = state.gems.copy()
            if move is not None:
                self.gems.remove(move[0])
                self.gems.remove(move[1])
                self.gems.append(MergedGem(*move))
                self.gems = sorted(self.gems)

    def apply(self, move: Tuple[Gem, Gem]):
        """ Generate a new state by applying the move """
        return State(self, move)

    def append(self, gem: Gem):
        """ Appends a gem to the state (for building a new state) """
        self.gems.append(gem)
        self.gems = sorted(self.gems)

    def count_keys(self) -> Tuple[int]:
        level3 = sum(1 for gem in self.gems if gem.level == 2 and gem.part == Part.FULL)
        level4 = sum(1 for gem in self.gems if gem.level == 3 and gem.part == Part.FULL)
        return (level3, level4)

    def show_moves(self):
        for level in range(1,5):
            print(f"==Level {level} Merges==")
            moves = []
            for gem in self.gems:
                moves += [move for move in gem.moves if str(level) in move]
            for move in sorted(moves):
                print(move)

    def score(self) -> float:
        score = sum(1 for gem in self.gems if gem.level == 2 and gem.part == Part.FULL)
        score += sum(3 for gem in self.gems if gem.level == 3 and gem.part == Part.FULL)
        score += sum(-.01 for gem in self.gems if gem.locked)
        score += sum(-.01 for gem in self.gems if gem.locked and gem.level == 3)
        return score

    def potential_score(self) -> int:
        """ Optimistically estimate a maximum score assuming we can get all parts to level 4 """
        tops = sum(1 for gem in self.gems if gem.part == Part.TOP)
        bottoms = sum(1 for gem in self.gems if gem.part == Part.BOT)
        free = sum(1 for gem in self.gems if not gem.locked)
        return self.score() + 3 * min(tops, bottoms, free)

    def num_locked(self) -> int:
        """ Number of locked tiles in a state """
        return sum(1 for gem in self.gems if gem.locked)

    def potential_progress(self) -> int:
        """ Potential progress of this state.

        This equals number locked tiles plus locked level 3 tiles, since they account for 2 progress
        """
        return self.num_locked() + sum(1 for gem in self.gems if gem.locked and gem.level == 3)

    def __hash__(self) -> int:
        return sum(x.__hash__() for x in self.gems)

    def __eq__(self, other: State):
        if len(self.gems) != len(other.gems):
            return False
        return all(self.gems[i] == other.gems[i] for i,_ in enumerate(self.gems))

    def __repr__(self):
        return self.gems.__repr__()

class Solver():
    """ Contains the state of the game and the solver """

    def __init__(self, locked_bottom, locked_top, free, free_bottom, free_top, free_full):
        self.max_progress = sum(locked_bottom) + sum(locked_top) + locked_bottom[3] + locked_top[3]

        self.start = State()
        for level in range(0,4):
            for _ in range(locked_bottom[level]):
                self.start.append(Gem(level, Part.BOT, True))
            for _ in range(locked_top[level]):
                self.start.append(Gem(level, Part.TOP, True))
            for _ in range(free[level]):
                self.start.append(Gem(level, Part.EMPTY, False))
            for _ in range(free_bottom[level]):
                self.start.append(Gem(level, Part.BOT, False))
            for _ in range(free_top[level]):
                self.start.append(Gem(level, Part.TOP, False))
            for _ in range(free_full[level]):
                self.start.append(Gem(level, Part.FULL, False))

        self.end_states: Set[State] = set()
        self.best = self.start

    def help(self):
        print("Running bruteforce solver")
        print("==Explanation==")
        print('"Free" = Gem you can merge with other gems')
        print('"Locked" = Locked gem')
        print(f'"{Part.BOT.name.capitalize()}" = Gem has bottom key piece')
        print(f'"{Part.TOP.name.capitalize()}" = Gem has top key piece')
        print(f'"{Part.FULL.name.capitalize()}" = Gem has a full key')

        print("\n===NOTE===")
        print('There has been some confusion on what is the "top" and "bot" key piece. ' +
              'As long as you are consistent, it does not matter which you use, though ' +
              'in-game the round colored piece is "bot" and the tip of the key "top"')

        print("\nMerges should be done in the order below, starting with level 1 gems\n")

    def show_results(self):
        self.best.show_moves()
        print("==Results==")

        level3, level4 = self.best.count_keys()

        if level3 == 1:
            print("- Level 3: 1 gem (1 key)")
        elif level3 > 1:
            print(f"- Level 3: {level3} gems ({level3} keys)")
        if level4 == 1:
            print("- Level 4: 1 gem (3 keys)")
        elif level4 > 1:
            print(f"- Level 4: {level4} gems ({level4 * 3} keys)")

        keys = self.best.count_keys()
        res = keys[0] + 3*keys[1]
        max_potential = ceil(self.start.potential_score())

        if res == max_potential:
            print(f"Keys: {res}/{max_potential} (Maximum keys picked up)")
        else:
            print(f"Keys: {res}/{max_potential} (Optimized solution with gems spawned)")

        remaining_progress = self.best.potential_progress()
        total_progress = self.start.potential_progress() - remaining_progress
        remaining_locked = self.best.num_locked()

        print(f"Progress: {total_progress}/{self.max_progress} ({remaining_locked} remaining locked gems)")
        print("Keep in mind these results are only for the selected color")
        print(len(self.end_states))

    def solve(self) -> State:
        """ Solve the problem """
        search_states: List[State] = [State(self.start)]

        while search_states:
            state = search_states.pop()
            moves = self._find_possible_moves(state)
            for move in moves:
                new_state = state.apply(move)

                if new_state.potential_score() < self.best.score() or new_state in self.end_states:
                    continue
                if new_state.score() >= self.best.score():
                    self.best = new_state

                search_states.append(new_state)
                self.end_states.add(new_state)

        # best = sorted(self.end_states, key = State.score)
        return self.best

    def _find_possible_moves(self, state: State):
        moves = set()
        for i, one in enumerate(state.gems):
            moves.update((one, two) for two in state.gems[i+1:] if one.can_merge_with(two))
        return moves

def solve(locked_bottom,locked_top,free,free_bottom,free_top,free_full,silent=False) -> Tuple[int]: #pylint: disable=unused-argument
    solver = Solver(locked_bottom,locked_top,free,free_bottom,free_top,free_full)
    solver.solve()

    max_keys = 3 * min(sum(locked_bottom),sum(locked_top))
    starting = 3 * sum(free)

    if not silent:
        solver.help()
        solver.show_results()

    keys = solver.best.count_keys()

    return (keys[0] + 3*keys[1], starting, max_keys, None, None, None)
