from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator

from action import *
from board import GameBoard
from queue import PriorityQueue

def delUnable(coord, coordList):
    modifiedCoordList = coordList.copy()
    checker = [(1,0), (-1, 1), (0, -1)]
    for i in checker:
        try:
            modifiedCoordList.remove((coord[0] + i[0], coord[1] + i[1]))
        except:
            pass
        try:
            modifiedCoordList.remove((coord[0] - i[0], coord[1] - i[1]))
        except:
            pass
    return modifiedCoordList

def id(state: dict) -> str:
    assert 'state_id' in state, "카탄 게임의 상태를 넣어주세요 이 빡대가리야"
    return state['state_id']

class Priority:
    def __init__(self, data, prior) -> None:
        self.data = data
        self.priority = prior
        
    def __repr__(self) -> str:
        return f'priority {self.priority} at {self.data}\n'
    
    def __lt__(self, other):
        # 뭔가 꼬여서 부등호를 반대로 했더니 잘 되더라구요...
        return self.priority > other.priority

class Agent:  # Do not change the name of this class!
    """
    An agent class

    The list of algorithms that you can use
    - AND-OR Search or other variants
    - Online DFS or other Online variant of uninformed/heuristic search algorithms
    - LRTA*
    """
    
    def get_distribution(self, state: dict) -> dict:
        """
        state의 board판을 참고하여, 각 좌표의 근처 자원 여부를 반환

        Args:
            state (dict): 현재 state

        Returns:
            dict: diversity 정보를 담고 있는 dictionary 리턴
        """
        MAPTORESOURCE = {
            'FO' : 0,
            'HI' : 1,
            'MO' : 2,
            'FI' : 3,
            'PA' : 4,
            'DE' : 5
        }
        # nearby patterns
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
        return intersectionDict
    
    def get_actions(self, state: dict) -> PriorityQueue[Priority]:
        """
        현재 state에서 가능한 action 시퀀스를 리턴.
        PriorityQueue 기반으로 넣어, diversity가 큰 것부터 뽑도록 만듬.

        Args:
            state (dict): current state

        Returns:
            PriorityQueue[Priority]: 해당 village action을 수행했을 때 diversity 기준으로 정렬된 queue
        """
        playerID = state['player_id']
        res = PriorityQueue()
        paths = [((3, -5), (3, -4)), ((2, -5), (3, -5)), ((3, 1), (4, 0)), ((4, -1), (4, 0)), ((2, 0), (3, -1)), ((3, -1), (4, -1)), ((3, -2), (3, -1)), ((3, -2), (4, -3)), ((2, -2), (3, -2)), ((4, -3), (5, -3)), ((4, -4), (4, -3)), ((3, 1), (3, 2)), ((2, 1), (3, 1)), ((4, -1), (5, -2)), ((5, -3), (5, -2)), ((-5, 3), (-4, 3)), ((-5, 2), (-5, 3)), ((-1, -3), (0, -4)), ((0, -4), (1, -4)), ((-1, 3), (0, 2)), ((0, 2), (1, 2)), ((0, 1), (0, 2)), ((0, -2), (1, -3)), ((1, -3), (2, -3)), ((1, -4), (1, -3)), ((0, 1), (1, 0)), ((1, 0), (2, 0)), ((1, -1), (1, 0)), ((0, 4), (1, 3)), ((1, 3), (2, 3)), ((1, 2), (1, 3)), ((-4, 4), (-3, 4)), ((-4, 3), (-4, 4)), ((-5, 2), (-4, 1)), ((-4, 1), (-3, 1)), ((-4, 0), (-4, 1)), ((-2, -1), (-1, -2)), ((-1, -2), (0, -2)), ((-1, -3), (-1, -2)), ((-2, -1), (-2, 0)), ((-3, -1), (-2, -1)), ((-2, 5), (-1, 4)), ((-1, 4), (0, 4)), ((-1, 3), (-1, 4)), ((-2, 2), (-1, 1)), ((-1, 1), (0, 1)), ((-1, 0), (-1, 1)), ((3, -4), (4, -4)), ((-4, 3), (-3, 2)), ((-3, 2), (-2, 2)), ((-3, 1), (-3, 2)), ((-1, 0), (0, -1)), ((0, -1), (1, -1)), ((0, -2), (0, -1)), ((-3, 5), (-2, 5)), ((-3, 4), (-3, 5)), ((1, -4), (2, -5)), ((1, -1), (2, -2)), ((2, -3), (2, -2)), ((1, 2), (2, 1)), ((2, 0), (2, 1)), ((-4, 0), (-3, -1)), ((-2, -3), (-1, -3)), ((-3, -2), (-2, -3)), ((-3, 1), (-2, 0)), ((-2, 0), (-1, 0)), ((-3, 4), (-2, 3)), ((-2, 3), (-1, 3)), ((-2, 2), (-2, 3)), ((2, -3), (3, -4)), ((2, 3), (3, 2)), ((-3, -2), (-3, -1))]
        coordList = state['board']['intersections']
        myVillage = [key for key, value in coordList.items() if value['owner'] == playerID]
        ableCoordList = [key for key, value in coordList.items() if value['owner'] is None]
        unableCoordList = [key for key, value in coordList.items() if value['owner'] is not None]
        
        for i in unableCoordList:
            ableCoordList = delUnable(i, ableCoordList)
        
        for coord in ableCoordList:
            village = VILLAGE(playerID, coord)
            # diversity 평가를 위한 evaluate_state 생성
            
            # 도로는 아무데나(중요 사항 아님)
            path_coord = [(i, j) for i, j in paths if i == coord or j == coord][0]
            road = ROAD(playerID, path_coord)
            
            # diversity 계산
            diversity = self.get_diversity(self.get_distribution(state), myVillage + [coord])
            res.put(Priority((village, road), diversity))
        # print(res.queue)
        return res
    
    def get_diversity(self, intersectionDict: dict, myVillage: list[tuple[int, int]]):
        """
        해당 state에서, myVillage 좌표의 diversity를 계산

        Args:
            intersectionDict (dict): diversity 정보를 담고 있는 dictionary
            myVillage (tuple[int, int]): diversity를 계산할 village의 좌표

        Returns:
            myVillage 좌표들의 diversity를 return
        """
        diversity = [0,0,0,0,0]
        for i in myVillage:
            diversity = [x+y for x,y in zip(diversity, intersectionDict[i])]
        return len(diversity) - diversity.count(0)
    
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
        untried: dict[str, PriorityQueue] = {} # 아직 시도하지 않은 action을 저장
        transition: dict[tuple[str, tuple[VILLAGE, ROAD]], dict] = {} # prev state, prev action -> state
        action = (None, None)
        backtrack: dict[dict, PriorityQueue] = {}
        intersectionDict = self.get_distribution(initial) # 자원 분포
        prev = None

        def _plan_execute(state: dict):
            nonlocal prev
            nonlocal action
            
            # 현재 내 village 위치를 리스트로 받음
            myVillage = [key for key, value in state['board']['intersections'].items() if value['owner'] == playerID]
            
            if len(myVillage) == 2: # if the setup is end
                return None, None # do nothing
            if id(state) not in untried:
                untried[id(state)] = self.get_actions(state)
            
            # 이하는 online DFS pseudo code 참고
            # 다른 점: LifoQueue 대신 PriorityQueue 기반으로 사용
            if prev is not None:
                transition[(prev['state_id'], prev['action'])] = state
                if id(state) not in backtrack:
                    backtrack[id(state)] = PriorityQueue()
                backtrack[id(state)].put((prev['state_id'], self.get_diversity(intersectionDict, myVillage)))
            
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
                prev = {'state_id': id(state), 'action': action}
            return action
                     
        return _plan_execute
