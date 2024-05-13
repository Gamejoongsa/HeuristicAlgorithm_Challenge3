from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator

from action import *
from board import GameBoard


def expand_board_state(board: GameBoard, state: dict, player: int):
    """
    Expand all possible children of given state, when a player placing his/her village and road, using the board.

    :param board: Game board to manipulate
    :param state: State to expand it children
    :param player: Player ID who is currently doing his/her initial setup procedure.

    :returns: A generator
        Each item is a tuple of VILLAGE action, ROAD action and the resulting state dictionary.
    """
    # Pass the board to the next player
    state = board.simulate_action(state, PASS())

    # The player will put a village and a road block on his/her turn.
    for coord in board.get_applicable_villages(player=player):
        board.set_to_state(state)
        # Test all possible villages
        village = VILLAGE(player, coord)
        # Apply village construction for further construction
        board.simulate_action(state, village)

        for path_coord in board.get_applicable_roads_from(coord, player=player)[:1]:
            # Test all possible roads nearby that village
            road = ROAD(player, path_coord)
            yield village, road, board.simulate_action(state, village, road)  # Yield this simulation result


def cascade_expansion(board: GameBoard, state: dict, players: List[int]):
    """
    Expand all possible children of given state, when several players placing his/her village and road, using the board.

    :param board: Game board to manipulate
    :param state: State to expand it children
    :param players: A list of Player IDs who are currently doing their initial setup procedure.

    :returns: A generator
        Each item is a resulting state dictionary, after all construction of given players
    """
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
    """
    An agent class, with and-or search (DFS) method
    """

    def or_search(self, board: GameBoard, state: dict, remaining_order: List[int], path: list) -> list:
        """
        An Or search function.
        """
        board.set_to_state(state)
        player_id = board.get_player_id()
        board.reset_setup_order(remaining_order)

        if player_id not in remaining_order:  # After second setup turn. We reached the end point.
            return []  # Do nothing

        if state['state_id'] in path:
            raise Exception(f'We reached a cycle! {path} and {state["state_id"]}')

        # For each children state, call AND search.
        error_cause = []
        for village, road, next_state in expand_board_state(board, state, player=player_id):
            try:
                board.set_to_state(next_state)
                and_plan = self.and_search(board, next_state, remaining_order[1:], path + [state['state_id']])
                return [(village, road), and_plan]
                # Call (village, road) at this state, and run other actions by following dictionary of and_plan
            except:
                error_cause.append(format_exc())
                pass

        raise Exception('No solution exists: Errors on all AND children.\n [Cause]\n' + '\n'.join(error_cause) + '-' * 80)

    def and_search(self, board: GameBoard, state: dict, remaining_order: list, path: list) -> dict:
        """
        An And search function.
        """
        # If the remaining setup order does not contain the current player ID, finish search without doing anything
        player_id = board.get_player_id()
        board.reset_setup_order(remaining_order)
        if player_id not in remaining_order:  # We don't have to search anymore
            return {}  # Do nothing

        players_turn = remaining_order.index(player_id)
        before_player = remaining_order[:players_turn]
        order_from_player = remaining_order[players_turn:]

        if before_player:
            path = path + [state['state_id']]

        plans = {}

        # For each children state (after doing all other's actions), call OR search.
        for next_state in cascade_expansion(board, state, before_player):
            # We will call OR search here. We will throw the error as it is.
            board.set_to_state(next_state)
            or_plan = self.or_search(board, next_state, order_from_player, path)
            # Call or_plan if we reach this state
            plans[next_state['state_id']] = or_plan

        return plans

    def decide_new_village(self, board: GameBoard, time_limit: float = None) -> Callable[[str], Tuple[Action, Action]]:
        """
        This algorithm search for the best place of placing a new village.

        :param board: Game board to manipulate
        :param time_limit: Timestamp for the deadline of this search.
        :return: A Program (Function) to execute
        """
        initial = board.get_state()
        expansion_order = board.reset_setup_order()
        plans = self.and_search(board, initial, expansion_order, [])

        def _plan_execute(state_id):
            plan = plans.get(state_id, None)
            if plan is None:
                return None, None

            actions, next_step_plan = plan
            plans.clear()
            plans.update(next_step_plan)

            return actions

        return _plan_execute
