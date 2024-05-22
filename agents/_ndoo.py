from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator

from action import *
from board import GameBoard

def expand_board_state(board: GameBoard, state: dict, player: int):
    state = board.simulate_action(state, PASS())

    for coord in board.get_applicable_villages(player=player):
        board.set_to_state(state)
        village = VILLAGE(player, coord)
        board.simulate_action(state, village)

        for path_coord in board.get_applicable_roads_from(coord, player=player)[:1]:
            road = ROAD(player, path_coord)
            yield village, road, board.simulate_action(state, village, road)

def cascade_expansion(board: GameBoard, state: dict, players: List[int]):
    if len(players) == 0:
        yield state
        return

    current_player = players[0]
    next_players = players[1:]
    current_order = board.get_remaining_setup_order()

    for _, _, next_state in expand_board_state(board, state, current_player):
        board.reset_setup_order(current_order[1:])
        for next_next_state in cascade_expansion(board, next_state, next_players):
            yield next_next_state

class Agent:  # Do not change the name of this class!
    def __init__(self):
        self.prev = None
        self.transition = {}
        self.untried = {}
        self.backtrack = {}

    def decide_new_village(self, board: GameBoard, time_limit: float = None) -> Callable[[dict], Tuple[Action, Action]]:
        initial_state = self.state_to_string(board.get_state())
        expansion_order = list(board.get_remaining_setup_order())  # Ensure it's a list
        plan = self.online_dfs(board, initial_state, expansion_order, board._current_player)

        def _plan_execute(state):
            state_string = self.state_to_string(state)
            action = plan.get(state_string, None)
            if action is None:
                return None, None

            next_action = action
            plan.clear()
            plan.update({state_string: next_action})

            return next_action

        return _plan_execute

    def online_dfs(self, board: GameBoard, state: str, remaining_order: List[int], current_player: int):
        if state not in self.untried:
            self.untried[state] = board.get_applicable_villages(player=current_player)

        if self.prev is not None:
            self.transition[(self.prev[0], self.prev[1])] = state
            if state not in self.backtrack:
                self.backtrack[state] = []
            self.backtrack[state].append(self.prev[0])

        if not self.untried[state]:
            if not self.backtrack[state]:
                return None
            back_state = self.backtrack[state].pop()
            action = next(action for action, s in self.transition.items() if s == back_state and action[0] == self.prev[0])
            self.prev = None
            return action

        action = self.untried[state].pop()
        new_state = self.state_to_string(board.simulate_action(self.string_to_state(state), VILLAGE(current_player, action)))
        self.prev = (state, VILLAGE(current_player, action))

        next_order = remaining_order[1:] + [remaining_order[0]]
        next_player = next_order[0]
        return self.online_dfs(board, new_state, next_order, next_player)

    def state_to_string(self, state: dict) -> str:
        return str(sorted(state.items()))

    def string_to_state(self, state_string: str) -> dict:
        return dict(eval(state_string))
