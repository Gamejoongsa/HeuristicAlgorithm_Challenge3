from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator

from action import *
from board import GameBoard


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

        raise NotImplementedError()