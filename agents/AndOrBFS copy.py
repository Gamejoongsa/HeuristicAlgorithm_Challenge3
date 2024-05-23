from random import choice
from time import time
from traceback import print_exc, format_exc
from typing import Tuple, List, Callable, Dict, Generator
from queue import Queue

from action import *
from board import GameBoard

def has_no_child(board: GameBoard, player: int):
    return len(board.get_applicable_cities(player=player)) != 2

def get_state_id(state: dict) -> str:
    assert 'state_id' in state, "카탄 게임의 상태를 넣어주세요 이 빡대가리야"
    return state['state_id']

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
        path_coord = board.get_applicable_roads_from(coord, player=player)[0]
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

class Node:
    def __init__(self, state, priority, order, action=None, parent=None, children=None, status=None) -> None:
        self.state = state
        self.priority = priority
        if parent is None:
            parent = self
        self.parent = parent
        if children is None:
            children = []
        self.children = children
        self.status = status
        self.order = order
        self.action = action
        
    def set_parent(self, parent):
        self.parent = parent
        
    def set_child(self, child):
        self.children.append(child)
        
    def id(self):
        return self.state['state_id']
        
    def __lt__(self, other):
        return self.priority < other.priority
        

class Agent:  # Do not change the name of this class!
    """
    An agent class, with and-or search (DFS) method
    """
    
    def failureLabel(self, board: GameBoard, state: Node, is_init=True):
        if is_init:
            state.status = 'Failure'
            parent = state.parent
            parent.status = 'Failure'
            grandparent = parent.parent
            return self.failureLabel(board, grandparent, is_init=False)
        else:
            for action in state.children:
                if action.status is not None:
                    if action.status == 'Failure':
                        continue
                    else:
                        return False # Not Failure
                else:
                    return False # not determined yet
            state.status = 'Failure'
            parent = state.parent
            if parent.id() == get_state_id(board.get_initial_state()):
                return True # initial is Failure
            parent.status = 'Failure'
            grandparent = parent.parent
            return self.failureLabel(board, grandparent, is_init=False)
            
    
    def solvableLabel(self, board: GameBoard, state: Node, is_init=True):
        if is_init:
            state.status = 'Solvable'
            return self.solvableLabel(board, state.parent, is_init=False)
        else:
            for child in state.children:
                if child.status is not None:
                    if child.status == 'Solvable':
                        continue
                    else:
                        return False # Not Solvable
                else:
                    return False # not determined yet
            state.status = 'Solvable'
            if state.id() == get_state_id(board.get_initial_state()):
                return True # initial is Solvable
            parent = state.parent
            parent.status = 'Solvable'
            grandparent = parent.parent
            return self.solvableLabel(board, grandparent, is_init=False)
        
    def make_ssambbong_plan(self, board: GameBoard, initial: Node):
        plans = {}
        for state in initial.children:
            for action in state.children:
                if action.status == 'Solvable':
                    plan = {}
                    for child in action.children:
                        for child_action in child.children:
                            if child_action.status == 'Solvable':
                                plan[child] = [child_action.action, {}]
                plans[state] = [action.action, plan]
                break
        return plans
            

    def AndOrBFS(self, board: GameBoard) -> dict:
        frontiers = Queue()
        remaining_order = board.reset_setup_order()
        player_id = board.get_player_id()
        player_turn = remaining_order.index(player_id)
        initial = Node(board.get_state(), 1, remaining_order)
        
        before_player = remaining_order[:player_turn]
        next_order = remaining_order[player_turn:]
        
        for next_state in cascade_expansion(board, initial.state, before_player):
            next_state = Node(next_state, 1, next_order, parent=initial)
            initial.set_child(next_state)
            frontiers.put(next_state)
        
        while not frontiers.empty():
            node = frontiers.get()
            remaining_order = node.order
            
            board.set_to_state(node.state)
            board.reset_setup_order(remaining_order)
            remaining_order = remaining_order[1:]
            
            if player_id not in remaining_order: # after second turn - goal
                isSolved = self.solvableLabel(board, node)
                if isSolved:
                    return self.make_ssambbong_plan(self, board)
                # remove
                continue
            # if has_no_child(board, player=player_id): # has no child
            #     isFailure = self.failureLabel(board, node)
            #     if isFailure:
            #         raise Exception('No solution exists: Errors on all AND children.\n [Cause]\n' + '\n' + '-' * 80)
            #     # remove
            #     continue
            
            player_turn = remaining_order.index(player_id)
            before_player = remaining_order[:player_turn]
            next_order = remaining_order[player_turn:]
            
            for village, road, child in expand_board_state(board, node.state, player=player_id):
                # set parent and children attribute
                diversity = board.diversity_of_state(child)
                if diversity == 3 or diversity == 5:
                    pass
                else:
                    continue
                child = Node(child, 1, remaining_order, action=(village, road), parent=node)
                node.set_child(child)
                # print(child.id())
                
                # expand states from action
                for grandchild in cascade_expansion(board, child.state, before_player):
                    grandchild = Node(grandchild, 1, next_order, parent=child)
                    child.set_child(grandchild)
                    frontiers.put(grandchild)
                

    def decide_new_village(self, board: GameBoard, time_limit: float = None) -> Callable[[dict], Tuple[Action, Action]]:
        """
        This algorithm search for the best place of placing a new village.

        :param board: Game board to manipulate
        :param time_limit: Timestamp for the deadline of this search.
        :return: A Program (Function) to execute
        """
        initial = board.get_state()
        expansion_order = board.reset_setup_order()
        plans = self.AndOrBFS(board)

        def _plan_execute(state):
            plan = plans.get(state['state_id'], None)
            if plan is None:
                return None, None

            actions, next_step_plan = plan
            plans.clear()
            plans.update(next_step_plan)

            return actions

        return _plan_execute
