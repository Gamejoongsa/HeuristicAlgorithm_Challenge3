from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator

from action import *
from board import GameBoard
from queue import Queue


class Agent:  # Do not change the name of this class!
    """
    An agent class

    The list of algorithms that you can use
    - AND-OR Search or other variants
    - Online DFS or other Online variant of uninformed/heuristic search algorithms
    - LRTA*
    """
    
    def decide_new_village(self, board: GameBoard, time_limit: float = None) -> Callable[[dict], Tuple[Action, Action]]:
        """
        This algorithm search for the best place of placing a new village.

        :param board: Game board to manipulate
        :param time_limit: Timestamp for the deadline of this search.
        :return: A Program (Function) to execute
        """
        start_time = time()
        player_id = board.get_player_id()
        board.set_to_state(board.get_initial_state())

        # Precompute the necessary information
        applicable_villages = board.get_applicable_villages(player_id)
        village_diversity = {coord: len(board.diversity_of_place(coord)) for coord in applicable_villages}

        # Find the village with the highest resource diversity
        chosen_village_coord = max(village_diversity, key=village_diversity.get)
        state = board.simulate_action(board.get_initial_state(), VILLAGE(player_id, chosen_village_coord))

        applicable_roads = board.get_applicable_roads_from(chosen_village_coord, player_id)
        road_diversity = {path: len(board.diversity_of_road(path)) for path in applicable_roads}

        # Precompute the best road from the chosen village
        chosen_road_coord = max(road_diversity, key=road_diversity.get)

        def policy(state: dict) -> Tuple[Action, Action]:
            nonlocal start_time

            if time_limit:
                elapsed_time = time() - start_time
                if elapsed_time > time_limit:
                    raise TimeoutError("Time limit exceeded for decision making")

            village_action = VILLAGE(state['player_id'], chosen_village_coord)
            road_action = ROAD(state['player_id'], chosen_road_coord)

            return village_action, road_action

        return policy
