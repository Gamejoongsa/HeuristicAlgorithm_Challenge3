from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator

from action import *
from board import GameBoard
from queue import Queue, PriorityQueue

def id(state: dict) -> str:
    assert 'state_id' in state, "카탄 게임의 상태를 넣어주세요 이 빡대가리야"
    return state['state_id']

class Priority:
    def __init__(self, data, prior) -> None:
        self.data = data
        self.priority = prior
    
    def __lt__(self, other):
        return self.priority > other.priority

class Agent:  # Do not change the name of this class!
    """
    An agent class

    The list of algorithms that you can use
    - AND-OR Search or other variants
    - Online DFS or other Online variant of uninformed/heuristic search algorithms
    - LRTA*
    """
    
    def get_actions(self, board: GameBoard, state: dict) -> PriorityQueue[Priority]:
        playerID = state['player_id']
        res = PriorityQueue()
        
        for coord in board.get_applicable_villages(player=playerID):
            board.set_to_state(state)
            # Test all possible villages
            village = VILLAGE(playerID, coord)
            # Apply village construction for further construction
            evaluate_state = board.simulate_action(state, village)
            path_coord = board.get_applicable_roads_from(coord, player=playerID)[0]
            road = ROAD(playerID, path_coord)
            diversity = self.get_diversity(evaluate_state, coord)
            res.put(Priority((village, road), diversity))
        board.set_to_state(state)
        return res
    
    def get_diversity(self, state: dict, myVillage: tuple[int, int]):
        MAPTORESOURCE = {
            'FO' : 0,
            'HI' : 1,
            'MO' : 2,
            'FI' : 3,
            'PA' : 4,
            'DE' : 5
        }
        pattern1 = [(1, 0), (0, -1), (-1, 1)]
        pattern2 = [(-1, 0), (0, 1), (1, -1)]
        coordList = state['board']['intersections']
        intersectionDict = {}
        hexes = state['board']['hexes']
        for i in coordList:
            intersectionDict[i] = [0, 0, 0, 0, 0, 0]
            for weight in pattern1:
                value = (i[0] + weight[0], i[1] + weight[1])
                if value in hexes.keys():
                    intersectionDict[i][MAPTORESOURCE[hexes[value]['type'][:2]]] = 1
            for weight in pattern2:
                value = (i[0] + weight[0], i[1] + weight[1])
                if value in hexes.keys():
                    intersectionDict[i][MAPTORESOURCE[hexes[value]['type'][:2]]] = 1
            intersectionDict[i] = intersectionDict[i][:-1]
            
        # print(f'\n{intersectionDict[myVillage]}')
        return sum(intersectionDict[myVillage])
    
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
        untried: dict[str, PriorityQueue] = {}
        transition = {}
        action = (None, None)
        backtrack: dict[dict, PriorityQueue] = {}
        prev = None

        def _plan_execute(state):
            nonlocal prev
            myVillage = [key for key, value in state['board']['intersections'].items() if value['owner'] == playerID]
            if len(myVillage) == 2:
                return None, None
            if id(state) not in untried:
                untried[id(state)] = self.get_actions(board, state)
            if prev is not None:
                transition[(prev['state_id'], prev['action'])] = state
                if id(state) not in backtrack:
                    backtrack[id(state)] = PriorityQueue()
                backtrack[id(state)].put((prev['state_id'], self.get_diversity(prev['state'], myVillage[0])))
            if id(state) not in untried:
                if id(state) not in backtrack:
                    return None, None
                backState = backtrack[id(state)].get()
                for prevstate, b, bs in transition.items():
                    if bs == backState and prevstate == prev['state_id']:
                        action = b
                        break
                prev = None
            else:
                action = untried[id(state)].get().data
                prev = {'state': state, 'state_id': id(state), 'action': action}
            return action
                     
        return _plan_execute
