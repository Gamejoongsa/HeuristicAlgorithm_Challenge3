from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator

from action import *
from board import GameBoard

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

class Agent:  # Do not change the name of this class!
    """
    An agent class

    The list of algorithms that you can use
    - AND-OR Search or other variants
    - Online DFS or other Online variant of uninformed/heuristic search algorithms
    - LRTA*
    """
    
    def decide_new_village(self, board: GameBoard, time_limit: float = 30) -> Callable[[dict], Tuple[Action, Action]]:
        """
        This algorithm search for the best place of placing a new village.

        :param board: Game board to manipulate
        :param time_limit: Timestamp for the deadline of this search.
        :return: A Program (Function) to execute
        """
        MAPTORESOURCE = {
            'FO' : 0,
            'HI' : 1,
            'MO' : 2,
            'FI' : 3,
            'PA' : 4,
            'DE' : 5
        }
        initial = board.get_state()
        expansion_order = board.reset_setup_order()#(0, 1, 2, 3, 3, 2, 1, 0)
        playerID = initial['player_id']
        paths = [((3, -5), (3, -4)), ((2, -5), (3, -5)), ((3, 1), (4, 0)), ((4, -1), (4, 0)), ((2, 0), (3, -1)), ((3, -1), (4, -1)), ((3, -2), (3, -1)), ((3, -2), (4, -3)), ((2, -2), (3, -2)), ((4, -3), (5, -3)), ((4, -4), (4, -3)), ((3, 1), (3, 2)), ((2, 1), (3, 1)), ((4, -1), (5, -2)), ((5, -3), (5, -2)), ((-5, 3), (-4, 3)), ((-5, 2), (-5, 3)), ((-1, -3), (0, -4)), ((0, -4), (1, -4)), ((-1, 3), (0, 2)), ((0, 2), (1, 2)), ((0, 1), (0, 2)), ((0, -2), (1, -3)), ((1, -3), (2, -3)), ((1, -4), (1, -3)), ((0, 1), (1, 0)), ((1, 0), (2, 0)), ((1, -1), (1, 0)), ((0, 4), (1, 3)), ((1, 3), (2, 3)), ((1, 2), (1, 3)), ((-4, 4), (-3, 4)), ((-4, 3), (-4, 4)), ((-5, 2), (-4, 1)), ((-4, 1), (-3, 1)), ((-4, 0), (-4, 1)), ((-2, -1), (-1, -2)), ((-1, -2), (0, -2)), ((-1, -3), (-1, -2)), ((-2, -1), (-2, 0)), ((-3, -1), (-2, -1)), ((-2, 5), (-1, 4)), ((-1, 4), (0, 4)), ((-1, 3), (-1, 4)), ((-2, 2), (-1, 1)), ((-1, 1), (0, 1)), ((-1, 0), (-1, 1)), ((3, -4), (4, -4)), ((-4, 3), (-3, 2)), ((-3, 2), (-2, 2)), ((-3, 1), (-3, 2)), ((-1, 0), (0, -1)), ((0, -1), (1, -1)), ((0, -2), (0, -1)), ((-3, 5), (-2, 5)), ((-3, 4), (-3, 5)), ((1, -4), (2, -5)), ((1, -1), (2, -2)), ((2, -3), (2, -2)), ((1, 2), (2, 1)), ((2, 0), (2, 1)), ((-4, 0), (-3, -1)), ((-2, -3), (-1, -3)), ((-3, -2), (-2, -3)), ((-3, 1), (-2, 0)), ((-2, 0), (-1, 0)), ((-3, 4), (-2, 3)), ((-2, 3), (-1, 3)), ((-2, 2), (-2, 3)), ((2, -3), (3, -4)), ((2, 3), (3, 2)), ((-3, -2), (-3, -1))]
        pattern1 = [(1, 0), (0, -1), (-1, 1)]
        pattern2 = [(-1, 0), (0, 1), (1, -1)]
        coordList = initial['board']['intersections']
        intersectionDict = {}
        hexes = initial['board']['hexes']
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



        def _plan_execute(state):
                playerID = state['player_id']
                coordList = state['board']['intersections']
                myVilage = [key for key, value in coordList.items() if value['owner'] == playerID]
                ableCoordList = [key for key, value in coordList.items() if value['owner'] is None]
                unabelCoordList = [key for key, value in coordList.items() if value['owner'] is not None]

                if len(myVilage) == 0:
                    for i in unabelCoordList:
                        ableCoordList = delUnable(i, ableCoordList)
                    coord = [i for i in ableCoordList if sum(intersectionDict[i]) == 3]
                    coord = coord[0]
                    print('first', intersectionDict[coord])
                    path = [(i, j) for i, j in paths if i == coord or j == coord][0]#도로 아무거나 고르기.
                    return (VILLAGE(playerID, coord), ROAD(playerID, path))
                else:
                    for i in unabelCoordList:
                        ableCoordList = delUnable(i, ableCoordList)
                    coord = ableCoordList.copy()
                    coord.sort(key = lambda x : min([a+b for a, b in zip(intersectionDict[myVilage[0]], intersectionDict[x])]), reverse = True)
                    coord = coord[0]
                    print('second', intersectionDict[coord])
                    path = [(i, j) for i, j in paths if i == coord or j == coord][0]
                    return (VILLAGE(playerID, coord), ROAD(playerID, path))
                     
        return _plan_execute
        