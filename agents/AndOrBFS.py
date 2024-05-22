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
    def __init__(self) -> None:
        self.parent = {}
        self.children = {}
        self.status = {}
        self.order = {}
        self.action = {}
        
    def set_parent_and_children(self, parent: dict, child: dict):
        self.parent[get_state_id(child)] = get_state_id(parent)
        if get_state_id(parent) not in self.children:
            self.children[get_state_id(parent)] = []
        self.children[get_state_id(parent)].append(get_state_id(child))
    
    def failureLabel(self, board: GameBoard, state_id: str, is_init=True):
        if is_init:
            self.status[state_id] = 'Failure'
            parent_id = self.parent[state_id]
            self.status[parent_id] = 'Failure'
            grandparent_id = self.parent[parent_id]
            return self.failureLabel(board, grandparent_id, is_init=False)
        else:
            for action in self.children[state_id]:
                if action in self.status:
                    if self.status[action] == 'Failure':
                        continue
                    else:
                        return False # Not Failure
                else:
                    return False # not determined yet
            self.status[state_id] = 'Failure'
            parent_id = self.parent[state_id]
            if parent_id == get_state_id(board.get_initial_state()):
                return True # initial is Failure
            self.status[parent_id] = 'Failure'
            grandparent_id = self.parent[parent_id]
            return self.failureLabel(board, grandparent_id, is_init=False)
            
    
    def solvableLabel(self, board: GameBoard, state_id: str, is_init=True):
        if is_init:
            self.status[state_id] = 'Solvable'
            return self.solvableLabel(board, self.parent[state_id], is_init=False)
        else:
            for state in self.children[state_id]:
                if state in self.status:
                    if self.status[state] == 'Solvable':
                        continue
                    else:
                        return False # Not Solvable
                else:
                    return False # not determined yet
            self.status[state_id] = 'Solvable'
            if state_id == get_state_id(board.get_initial_state()):
                return True # initial is Solvable
            parent_id = self.parent[state_id]
            self.status[parent_id] = 'Solvable'
            grandparent_id = self.parent[parent_id]
            return self.solvableLabel(board, grandparent_id, is_init=False)
        
    def make_ssambbong_plan(self, board: GameBoard):
        plans = {}
        for initial in self.children[board.get_initial_state()['state_id']]:
            for action in self.children[initial]:
                if self.status[action] == 'Solvable':
                    plan = {}
                    for child in self.children[action]:
                        for child_action in self.children[child]:
                            if self.status[child_action] == 'Solvable':
                                plan[child] = [self.action[child_action], {}]
                plans[initial] = [self.action[action], plan]
                break
        return plans
            

    def AndOrBFS(self, board: GameBoard) -> dict:
        frontiers = Queue()
        initial = board.get_state()
        remaining_order = board.reset_setup_order()
        player_id = board.get_player_id()
        player_turn = remaining_order.index(player_id)
        plans = {}
        
        before_player = remaining_order[:player_turn]
        next_order = remaining_order[player_turn:]
        
        for next_state in cascade_expansion(board, initial, before_player):
            frontiers.put(next_state)
            self.set_parent_and_children(parent=initial, child=next_state)
            self.order[get_state_id(next_state)] = next_order
        
        while not frontiers.empty():
            node = frontiers.get()
            remaining_order = self.order[get_state_id(node)]
            
            board.set_to_state(node)
            board.reset_setup_order(remaining_order)
            
            if player_id not in remaining_order: # after second turn - goal
                isSolved = self.solvableLabel(board, get_state_id(node))
                if isSolved:
                    return self.make_ssambbong_plan(self, board)
                # remove
                continue
            if has_no_child(board, player=player_id): # has no child
                isFailure = self.failureLabel(board, get_state_id(node))
                if isFailure:
                    raise Exception('No solution exists: Errors on all AND children.\n [Cause]\n' + '\n' + '-' * 80)
                # remove
                continue
            
            remaining_order = remaining_order[1:]
            player_turn = remaining_order.index(player_id)
            before_player = remaining_order[:player_turn]
            next_order = remaining_order[player_turn:]
            
            for village, road, child in expand_board_state(board, node, player=player_id):
                # set parent and children attribute
                self.set_parent_and_children(parent=node, child=child)
                self.order[get_state_id(child)] = remaining_order
                self.action[get_state_id(child)] = (village, road)
                
                # expand states from action
                for grandchild in cascade_expansion(board, child, before_player):
                    frontiers.put(grandchild)
                    self.set_parent_and_children(parent=child, child=grandchild)
                    self.order[get_state_id(grandchild)] = next_order
                

    def decide_new_village(self, board: GameBoard, time_limit: float = None) -> Callable[[str], Tuple[Action, Action]]:
        """
        This algorithm search for the best place of placing a new village.

        :param board: Game board to manipulate
        :param time_limit: Timestamp for the deadline of this search.
        :return: A Program (Function) to execute
        """
        initial = board.get_state()
        expansion_order = board.reset_setup_order()
        plans = self.AndOrBFS(board)

        def _plan_execute(state_id):
            plan = plans.get(state_id, None)
            if plan is None:
                return None, None

            actions, next_step_plan = plan
            plans.clear()
            plans.update(next_step_plan)

            return actions

        return _plan_execute
