import math
import random
from dataclasses import dataclass, field
from typing import Optional

from core.actions import Action, ActionType
from core.board import HexResource


DICE_WEIGHT = {
    None: 0,
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    6: 5,
    8: 5,
    9: 4,
    10: 3,
    11: 2,
    12: 1,
}


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
        return 120
    if action.type == ActionType.BUILD_SETTLEMENT:
        return 100
    if action.type == ActionType.TRADE_BANK:
        return 75
    if action.type == ActionType.BUILD_ROAD:
        return 55
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


def vertex_hexes(board, vertex: int) -> list[int]:
    result = []
    for hex_id, verts in enumerate(board.hex_vertices):
        if vertex in verts:
            result.append(hex_id)
    return result


def vertex_production_score(state, vertex: int) -> float:
    """
    Jak dobre jest miejsce pod osadę/miasto.
    """
    score = 0.0
    distinct_resources = set()

    for hex_id in vertex_hexes(state.board, vertex):
        if hex_id == state.robber_hex:
            continue

        resource = state.board.hex_resources[hex_id]
        number = state.board.hex_numbers[hex_id]

        if resource == HexResource.DESERT:
            continue

        distinct_resources.add(resource)
        score += DICE_WEIGHT[number]

        if resource == HexResource.LUMBER:
            score += 2.0
        elif resource == HexResource.BRICK:
            score += 1.8
        elif resource == HexResource.GRAIN:
            score += 1.4
        elif resource == HexResource.ORE:
            score += 1.4
        elif resource == HexResource.WOOL:
            score += 1.0

    score += 1.2 * len(distinct_resources)
    return score


def controlled_production_score(state, player_id: int) -> float:
    """
    Suma jakości pól kontrolowanych przez gracza.
    Osada liczy się x1, miasto x2.
    """
    player = state.players[player_id]
    score = 0.0

    for vertex in player.settlements:
        score += vertex_production_score(state, vertex)

    for vertex in player.cities:
        score += 2.0 * vertex_production_score(state, vertex)

    return score


def open_settlement_spots_score(state, player_id: int) -> float:
    """
    Szacujemy, ile dobrych miejsc pod osadę gracz ma już 'otwartych' przez drogi.
    """
    player = state.players[player_id]
    score = 0.0

    for vertex in range(len(state.board.vertex_positions)):
        if vertex in state.occupied_vertices:
            continue

        # zasada odległości
        blocked = False
        for n in state.board.vertex_neighbors[vertex]:
            if n in state.occupied_vertices:
                blocked = True
                break
        if blocked:
            continue

        # czy dotyka drogi gracza
        connected = False
        for edge_id in state.board.vertex_edges[vertex]:
            if edge_id in player.roads:
                connected = True
                break

        if connected:
            score += 0.5 * vertex_production_score(state, vertex)

    return score


def build_readiness_score(player) -> float:
    """
    Premia za bycie blisko kosztów budowy.
    """
    brick = player.resources[HexResource.BRICK]
    lumber = player.resources[HexResource.LUMBER]
    wool = player.resources[HexResource.WOOL]
    grain = player.resources[HexResource.GRAIN]
    ore = player.resources[HexResource.ORE]

    settlement_ready = min(brick, 1) + min(lumber, 1) + min(wool, 1) + min(grain, 1)
    city_ready = min(grain, 2) + min(ore, 3)

    return 1.2 * settlement_ready + 1.0 * city_ready


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

    my_prod = controlled_production_score(state, root_player_id)
    opp_prod = controlled_production_score(state, opp_id)

    my_open_spots = open_settlement_spots_score(state, root_player_id)
    opp_open_spots = open_settlement_spots_score(state, opp_id)

    my_ready = build_readiness_score(me)
    opp_ready = build_readiness_score(opp)

    score = 0.0
    score += 12.0 * (my_vp - opp_vp)
    score += 3.0 * (my_cities - opp_cities)
    score += 2.0 * (my_settlements - opp_settlements)
    score += 0.2 * (my_resources - opp_resources)
    score += 0.1 * (my_roads - opp_roads)
    score += 0.35 * (my_prod - opp_prod)
    score += 0.20 * (my_open_spots - opp_open_spots)
    score += 0.35 * (my_ready - opp_ready)

    return 1.0 / (1.0 + math.exp(-score / 6.0))


def select_child(node: Node, exploration: float) -> Node:
    return max(node.children.values(), key=lambda child: child.uct_score(exploration))


def rollout(state, root_player_id: int, max_depth: int = 90) -> float:
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