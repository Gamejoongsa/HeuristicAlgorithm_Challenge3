from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator

from action import *
from board import GameBoard
from queue import Queue, LifoQueue

def id(state: dict) -> str:
    assert 'state_id' in state, "카탄 게임의 상태를 넣어주세요 이 빡대가리야"
    return state['state_id']

class Agent:  # Do not change the name of this class!
    """
    An agent class

    The list of algorithms that you can use
    - AND-OR Search or other variants
    - Online DFS or other Online variant of uninformed/heuristic search algorithms
    - LRTA*
    """
    
    def get_actions(self, board: GameBoard, state: dict) -> list[tuple[VILLAGE, ROAD]]:
        playerID = state['player_id']
        res = []
        
        for coord in board.get_applicable_villages(player=playerID):
            board.set_to_state(state)
            # Test all possible villages
            village = VILLAGE(playerID, coord)
            # Apply village construction for further construction
            board.simulate_action(state, village)
            path_coord = board.get_applicable_roads_from(coord, player=playerID)[0]
            road = ROAD(playerID, path_coord)
            res.append((village, road))
        board.set_to_state(state)
        return res
    
    def decide_new_village(self, board: GameBoard, time_limit: float = 30) -> Callable[[dict], Tuple[Action, Action]]:
        """
        This algorithm search for the best place of placing a new village.

        :param board: Game board to manipulate
        :param time_limit: Timestamp for the deadline of this search.
        :return: A Program (Function) to execute
        """
        
        initial = board.get_state()
        expansion_order = board.reset_setup_order()#(0, 1, 2, 3, 3, 2, 1, 0)
        playerID = initial['player_id']
        untried: dict[str, list] = {}
        transition = {}
        action = (None, None)
        backtrack: dict[dict, LifoQueue] = {}
        prev = None

        def _plan_execute(state):
            nonlocal prev
            myVillage = [key for key, value in state['board']['intersections'].items() if value['owner'] == playerID]
            if len(myVillage) == 2:
                return None, None
            if id(state) not in untried:
                untried[id(state)] = self.get_actions(board, state)
            if prev is not None:
                transition[(prev['state'], prev['action'])] = state
                if id(state) not in backtrack:
                    backtrack[id(state)] = LifoQueue()
                backtrack[id(state)].put(prev['state'])
            if id(state) not in untried:
                if id(state) not in backtrack:
                    return None, None
                backState = backtrack[id(state)].get()
                for prevstate, b, bs in transition.items():
                    if bs == backState and prevstate == prev['state']:
                        action = b
                        break
                prev = None
            else:
                action = untried[id(state)].pop(0)
                prev = {'state': id(state), 'action': action}
            return action
                     
        return _plan_execute
