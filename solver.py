""" Solver for the FOE anniversary event """
from __future__ import annotations
from math import ceil
from typing import Tuple, List, Set, Union
from enum import Enum

VERSION=3.2

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
        self.free = not locked
        self.moves: List[Move] = []
        # Compute binary encoding for hashing and comparing
        self._hash = int((self.level << 3) + (self.locked << 2) + self.part.value)

        self.score = self._compute_score()

    def _compute_score(self) -> float:
        lock_penalty = self.locked
        keys = self.part == Part.FULL
        empty_gem_penalty = self.part == Part.EMPTY
        # empty_gem_penalty += self.part != Part.FULL
        if self.level == 3:
            keys *= 3
            lock_penalty *= 2

        return keys - .01 * lock_penalty - 0.0001 * empty_gem_penalty

    def can_merge_with(self, other: Gem) -> bool:
        return self.level == other.level and (self.free or other.free)

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

class EmptyState():
    gems = []

class State():
    def __init__(self, state: Union[EmptyState, State], move: Move = None):
        self.gems: List[Gem] = state.gems.copy()

        if move:
            self.gems.remove(move[0])
            self.gems.remove(move[1])
            new_gem = MergedGem(move)
            self.gems.append(new_gem)
            self.gems = sorted(self.gems) # Must sort for equality

            # Computing score based on previous. Makes it much faster
            merge_penalty = 0.0002
            self.score = state.score - move[0].score - move[1].score + new_gem.score - merge_penalty
            self._tops = state._tops - (move[0].part == Part.TOP) - (move[1].part == Part.TOP) + (new_gem.part == Part.TOP)
            self._bottoms = state._bottoms - (move[0].part == Part.BOT) - (move[1].part == Part.BOT) + (new_gem.part == Part.BOT)
            self._free = state._free - (move[0].free and move[1].free)
            potential_score_bonus = 3 # this is not right, but I am not sure why we need it for e.g. tc45, tc58 and tc71
            self.potential_score = potential_score_bonus + ceil(self.score) + 3 * min(self._tops, self._bottoms, self._free)

    def _update_score(self):
        score, tops, bottoms, free = 0, 0, 0, 0
        for gem in self.gems:
            score += gem.score
            free += gem.free
            bottoms += gem.part == Part.BOT
            tops += gem.part == Part.TOP

        self._tops = tops
        self._bottoms = bottoms
        self._free = free
        
        self.potential_score = ceil(score) + 3 * min(tops, bottoms, free)
        self.score = score

    def append(self, gem: Gem, count: int = 1):
        """ Appends a gem to the state (for building a new state) """
        for _ in range(count):
            self.gems.append(gem)
        self._update_score()

    def count_keys(self) -> Tuple[int]:
        level3 = sum(gem.level == 2 and gem.part == Part.FULL for gem in self.gems)
        level4 = sum(gem.level == 3 and gem.part == Part.FULL for gem in self.gems)
        return (level3, level4)

    def show_moves(self):
        def sort_move(move: Move) -> Move:
            return move if move[0] < move[1] else (move[1], move[0], move[2])

        for level in range(0,4):
            print(f"==Level {level + 1} Merges==")
            moves: List[Move] = []
            for gem in self.gems:
                for move in gem.moves:
                    if move[0].level == level:
                        one, two, result = sort_move(move)
                        moves.append((one, two, result))

            for move in sorted(moves):
                print(f"{str(move[0]):>12} + {str(move[1]):<13} => {move[2]}")

    def num_locked(self) -> int:
        """ Number of locked tiles in a state """
        return sum(gem.locked for gem in self.gems)

    def potential_progress(self) -> int:
        """ Potential progress of this state.

        This equals number locked tiles plus locked level 3 tiles, since they account for 2 progress
        """
        return self.num_locked() + sum(gem.locked and gem.level == 3 for gem in self.gems)

    def num_unlocked_part(self) -> int:
        """ Number of unlocked gems with only a key part """
        return sum(1 for gem in self.gems if gem.free and (gem.part == Part.TOP or gem.part == Part.BOT))

    def num_unlocked_empty(self) -> int:
        """ Number of unlocked gems with no key part """
        return sum(1 for gem in self.gems if gem.free and gem.part == Part.EMPTY)

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

        self.start = State(EmptyState())
        for level in range(0,4):
            self.start.append(Gem(level, Part.BOT, True), locked_bottom[level])
            self.start.append(Gem(level, Part.TOP, True), locked_top[level])
            self.start.append(Gem(level, Part.EMPTY, False), free[level])
            self.start.append(Gem(level, Part.BOT, False), free_bottom[level])
            self.start.append(Gem(level, Part.TOP, False), free_top[level])
            self.start.append(Gem(level, Part.FULL, False), free_full[level])

        self.end_states: Set[State] = set()
        self.best = self.start

    def help(self):
        print(f"Running fast optimized solver v{VERSION}")
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
        max_potential = ceil(self.start.potential_score)

        if res == max_potential:
            print(f"Keys: {res}/{max_potential} (Maximum keys picked up)")
        else:
            print(f"Keys: {res}/{max_potential} (Optimized solution with gems spawned)")

        remaining_progress = self.best.potential_progress()
        total_progress = self.start.potential_progress() - remaining_progress
        remaining_locked = self.best.num_locked()

        print(f"Progress: {total_progress}/{self.max_progress} ({remaining_locked} remaining locked gems)")
        print("Keep in mind these results are only for the selected color")
        print(f" -- Score: {self.best.score:0.4f} out of {len(self.end_states)} evaluated games.")

    def solve(self) -> State:
        """ Solve the problem """
        stack = [self.start]
        while stack:
            state = stack.pop()
            moves = self._find_possible_moves(state)
            for move in moves:
                new_state = State(state, move)

                if new_state in self.end_states or new_state.potential_score <= self.best.score:
                    continue
                if new_state.score > self.best.score:
                    self.best = new_state

                self.end_states.add(new_state)
                stack.append(new_state)

    def _find_possible_moves(self, state: State):
        # return set((one, two) for i, one in enumerate(state.gems)
        #         for two in state.gems[i+1:] if one.can_merge_with(two))
        moves = set()
        # limit possible moves to the lowest level with merges of locked gems, but allow merging of two free gems in levels lower than that
        minlevel = 100  # minimum level at which locked gems can be merged
        minlevel_free = 100  # minimum level at which free gems can merge
        for i, one in enumerate(state.gems):
            minlevel = min(minlevel, min([one.level for two in state.gems[i+1:] if one.can_merge_with(two) and (one.locked or two.locked)], default=100))
            minlevel_free = min(minlevel_free, min([one.level for two in state.gems[i+1:] if one.can_merge_with(two) and one.free and two.free], default=100))
        for i, one in enumerate(state.gems):
            moves.update((one, two) for two in state.gems[i+1:] if (one.level == minlevel and one.can_merge_with(two) and (one.locked or two.locked))
                                                                    or (minlevel_free < minlevel and one.can_merge_with(two) and one.free and two.free))
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

    remaining_progress = solver.best.potential_progress()
    total_progress = solver.start.potential_progress() - remaining_progress

    return (keys[0] + 3*keys[1], starting, max_keys,
            total_progress, solver.start.potential_progress(), solver.best.num_locked(),
            solver.best.num_unlocked_part(), solver.best.num_unlocked_empty())
