import math
import random
from dataclasses import dataclass, field
from typing import Optional

from core.actions import Action, ActionType
from core.board import HexResource


@dataclass
class Node:
    state: object
    parent: Optional["Node"] = None
    action_from_parent: Optional[Action] = None

    children: dict[Action, "Node"] = field(default_factory=dict)
    untried_actions: list[Action] = field(default_factory=list)

    visits: int = 0
    value_sum: float = 0.0

    def is_fully_expanded(self) -> bool:
        return len(self.untried_actions) == 0

    def mean_value(self) -> float:
        if self.visits == 0:
            return 0.0
        return self.value_sum / self.visits

    def uct_score(self, exploration: float = 1.41) -> float:
        if self.visits == 0:
            return float("inf")

        exploit = self.value_sum / self.visits
        explore = exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploit + explore


def action_priority(action: Action) -> int:
    if action.type == ActionType.BUILD_CITY:
        return 100
    if action.type == ActionType.BUILD_SETTLEMENT:
        return 90
    if action.type == ActionType.TRADE_BANK:
        return 70
    if action.type == ActionType.BUILD_ROAD:
        return 50
    if action.type == ActionType.ROLL_DICE:
        return 40
    if action.type == ActionType.MOVE_ROBBER:
        return 30
    if action.type == ActionType.END_TURN:
        return 0
    return 1


def weighted_action_choice(actions: list[Action]) -> Action:
    weighted = []
    for action in actions:
        w = action_priority(action)
        weighted.append((action, max(1, w)))

    total = sum(weight for _, weight in weighted)
    r = random.uniform(0, total)

    cumulative = 0.0
    for action, weight in weighted:
        cumulative += weight
        if r <= cumulative:
            return action

    return weighted[-1][0]


def evaluate_state(state, root_player_id: int) -> float:
    """
    Heurystyczna ocena stanu z perspektywy root_player_id.
    Zwraca wartość około 0..1.
    """
    me = state.players[root_player_id]
    opp_id = 1 - root_player_id
    opp = state.players[opp_id]

    my_vp = state.victory_points(root_player_id)
    opp_vp = state.victory_points(opp_id)

    my_resources = sum(me.resources.values())
    opp_resources = sum(opp.resources.values())

    my_roads = len(me.roads)
    opp_roads = len(opp.roads)

    my_settlements = len(me.settlements)
    opp_settlements = len(opp.settlements)

    my_cities = len(me.cities)
    opp_cities = len(opp.cities)

    score = 0.0
    score += 10.0 * (my_vp - opp_vp)
    score += 2.5 * (my_cities - opp_cities)
    score += 1.5 * (my_settlements - opp_settlements)
    score += 0.3 * (my_resources - opp_resources)
    score += 0.15 * (my_roads - opp_roads)

    # mapowanie na 0..1
    return 1.0 / (1.0 + math.exp(-score / 5.0))


def select_child(node: Node, exploration: float) -> Node:
    return max(node.children.values(), key=lambda child: child.uct_score(exploration))


def rollout(state, root_player_id: int, max_depth: int = 80) -> float:
    current_state = state
    depth = 0

    while not current_state.is_terminal() and depth < max_depth:
        actions = current_state.legal_actions()
        if not actions:
            break

        action = weighted_action_choice(actions)
        current_state = current_state.apply(action)
        depth += 1

    if current_state.is_terminal():
        return current_state.reward(root_player_id)

    return evaluate_state(current_state, root_player_id)


def backpropagate(node: Node, value: float) -> None:
    current = node
    while current is not None:
        current.visits += 1
        current.value_sum += value
        current = current.parent


def mcts_search(root_state, player_id: int, iterations: int = 300, exploration: float = 1.41) -> Action:
    root = Node(state=root_state)
    root.untried_actions = list(root_state.legal_actions())

    if not root.untried_actions:
        raise ValueError("Brak legalnych akcji w stanie początkowym.")

    for _ in range(iterations):
        node = root
        state = root_state

        # 1. Selection
        while node.is_fully_expanded() and node.children and not state.is_terminal():
            node = select_child(node, exploration)
            state = state.apply(node.action_from_parent)

        # 2. Expansion
        if not state.is_terminal() and node.untried_actions:
            action = weighted_action_choice(node.untried_actions)
            node.untried_actions.remove(action)

            next_state = state.apply(action)
            child = Node(
                state=next_state,
                parent=node,
                action_from_parent=action,
            )
            child.untried_actions = list(next_state.legal_actions())

            node.children[action] = child
            node = child
            state = next_state

        # 3. Simulation
        value = rollout(state, root_player_id=player_id)

        # 4. Backpropagation
        backpropagate(node, value)

    best_child = max(root.children.values(), key=lambda child: child.visits)
    return best_child.action_from_parent