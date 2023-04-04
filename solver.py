""" Solver for the FOE anniversary event """
from __future__ import annotations
from math import ceil
from typing import Callable, Tuple, List, Set
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
        self.moves: List[Move] = []
        # Compute binary encoding for hashing and comparing
        self._hash = int((self.level << 3) + (self.locked << 2) + self.part.value)

    def can_merge_with(self, other: Gem) -> bool:
        return self.level == other.level and not (self.locked and other.locked)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: Gem) -> bool:
        return self.level == other.level and self.part == other.part and self.locked == other.locked

    def __lt__(self, other: Gem) -> bool:
        return self._hash < other._hash

    def __repr__(self) -> str:
        value = f"{'Locked' if self.locked else 'Free'} L{self.level + 1}"
        if self.part != Part.EMPTY:
            return f"{value} {self.part.name.capitalize()}"
        return value

Move = Tuple[Gem, ...]

class MergedGem(Gem):
    def __init__(self, move: Move):
        assert move[0].level == move[1].level
        super().__init__(min(3,move[0].level + 1),
                            Part(move[0].part.value | move[1].part.value), False)
        self.moves = move[0].moves + move[1].moves + [(move[0], move[1], self)]

class State():
    def __init__(self, state: State = None, move: Move = None):
        if state is None:
            self.gems: List[Gem] = []
        else:
            self.gems = state.gems.copy()
            if move is not None:
                self.gems.remove(move[0])
                self.gems.remove(move[1])
                self.gems.append(MergedGem(move))
                self.gems = sorted(self.gems)

        self._update_score()

    def _update_score(self):
        keys, tops, bottoms, free, lock_penalty = 0, 0, 0, 0, 0
        for gem in self.gems:
            free += not gem.locked
            lock_penalty += gem.locked
            lock_penalty += gem.locked and gem.level == 3

            keys += gem.part == Part.FULL and gem.level == 2
            keys += 3*(gem.part == Part.FULL and gem.level == 3)
            bottoms += gem.part == Part.BOT
            tops += gem.part == Part.TOP

        self._potential_score = keys + 3 * min(tops, bottoms, free)
        self._score = keys - .01 * lock_penalty

    def apply(self, move: Tuple[Gem, Gem]):
        """ Generate a new state by applying the move """
        return State(self, move)

    def append(self, gem: Gem):
        """ Appends a gem to the state (for building a new state) """
        self.gems.append(gem)
        self._update_score()

    def count_keys(self) -> Tuple[int]:
        level3 = sum(gem.level == 2 and gem.part == Part.FULL for gem in self.gems)
        level4 = sum(gem.level == 3 and gem.part == Part.FULL for gem in self.gems)
        return (level3, level4)

    def show_moves(self):
        def sort_move(move: Move) -> Move:
            return move if move[1].locked else (move[1], move[0], move[2])

        for level in range(0,4):
            print(f"==Level {level + 1} Merges==")
            for gem in self.gems:
                for move in gem.moves:
                    if move[0].level == level:
                        one, two, result = sort_move(move)
                        print(f"{str(one):>12} + {str(two):<13} => {result}")

    def score(self) -> float:
        return self._score

    def potential_score(self) -> int:
        """ Optimistically estimate a maximum score assuming we can get all parts to level 4 """
        return self._potential_score

    def num_locked(self) -> int:
        """ Number of locked tiles in a state """
        return sum(gem.locked for gem in self.gems)

    def potential_progress(self) -> int:
        """ Potential progress of this state.

        This equals number locked tiles plus locked level 3 tiles, since they account for 2 progress
        """
        return self.num_locked() + sum(gem.locked and gem.level == 3 for gem in self.gems)

    def __hash__(self) -> int:
        return hash(tuple(self.gems))

    def __eq__(self, other: State):
        return self.gems == other.gems

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
        print(f"Score: {self.best.score()}")
        print("Keep in mind these results are only for the selected color")
        print(len(self.end_states))

    def solve(self) -> State:
        """ Solve the problem """
        stack = [State(self.start)]
        while stack:
            state = stack.pop()
            moves = self._find_possible_moves(state)
            for move in moves:
                new_state = State(state, move)

                if new_state.potential_score() <= self.best.score() or new_state in self.end_states:
                    continue
                if new_state.score() > self.best.score():
                    self.best = new_state

                self.end_states.add(new_state)
                stack.append(new_state)

    def _find_possible_moves(self, state: State):
        # moves = set()
        # for i, one in enumerate(state.gems):
        #     moves.update((one, two) for two in state.gems[i+1:] if one.can_merge_with(two))
        # return moves
        return set((one, two) for i, one in enumerate(state.gems)
                        for two in state.gems[i+1:] if one.can_merge_with(two))

def solve(locked_bottom,locked_top,free,free_bottom,free_top,free_full,silent=False) -> Tuple[int]: #pylint: disable=unused-argument
    solver = Solver(locked_bottom,locked_top,free,free_bottom,free_top,free_full)
    solver.solve()

    max_keys = 3 * min(sum(locked_bottom),sum(locked_top))
    starting = 3 * sum(free)

    if not silent:
        solver.help()
        solver.show_results()

    keys = solver.best.count_keys()


    remaining_progress = solver.best.potential_progress()
    total_progress = solver.start.potential_progress() - remaining_progress


    return (keys[0] + 3*keys[1], starting, max_keys, total_progress, solver.start.potential_progress(), solver.best.num_locked())
