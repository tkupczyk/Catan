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
        return 160
    if action.type == ActionType.BUILD_SETTLEMENT:
        return 145
    if action.type == ActionType.PLAY_ROAD_BUILDING:
        return 110
    if action.type == ActionType.PLAY_KNIGHT:
        return 95
    if action.type == ActionType.TRADE_BANK:
        return 35
    if action.type == ActionType.BUY_DEVELOPMENT_CARD:
        return 70
    if action.type == ActionType.BUILD_ROAD:
        return 22
    if action.type == ActionType.ROLL_DICE:
        return 40
    if action.type == ActionType.MOVE_ROBBER:
        return 35
    if action.type == ActionType.END_TURN:
        return 0
    return 1


def vertex_hexes(board, vertex: int) -> list[int]:
    result = []
    for hex_id, verts in enumerate(board.hex_vertices):
        if vertex in verts:
            result.append(hex_id)
    return result


def players_touching_hex(state, hex_id: int) -> list[int]:
    touched_vertices = set(state.board.hex_vertices[hex_id])
    result = []

    for player_id, player in enumerate(state.players):
        if any(v in touched_vertices for v in player.settlements) or \
           any(v in touched_vertices for v in player.cities):
            result.append(player_id)

    return result


def vertex_production_score(state, vertex: int) -> float:
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
            score += 1.6
        elif resource == HexResource.ORE:
            score += 1.5
        elif resource == HexResource.WOOL:
            score += 1.0

        if number in (6, 8):
            score += 2.0

    score += 1.3 * len(distinct_resources)
    return score

def immediate_action_score(state, action: Action, player_id: int) -> float:
    """
    Ocena pojedynczego ruchu 'tu i teraz'.
    Używana do priorytetów taktycznych przed MCTS.
    """
    if action.type == ActionType.BUILD_CITY and action.target is not None:
        return 1000.0 + 3.0 * vertex_production_score(state, action.target)

    if action.type == ActionType.BUILD_SETTLEMENT and action.target is not None:
        return 800.0 + 2.5 * vertex_production_score(state, action.target)

    if action.type == ActionType.PLAY_KNIGHT:
        return 180.0

    if action.type == ActionType.BUY_DEVELOPMENT_CARD:
        return 140.0

    if action.type == ActionType.TRADE_BANK:
        give_res = action.resource_give
        get_res = action.resource_get
        score = 120.0

        # preferuj trade pod settlement
        if get_res in (HexResource.BRICK, HexResource.LUMBER, HexResource.WOOL, HexResource.GRAIN):
            score += 20.0

        # preferuj trade pod city
        if get_res in (HexResource.GRAIN, HexResource.ORE):
            score += 10.0

        # kara za oddawanie zasobu bardzo potrzebnego
        if give_res in (HexResource.BRICK, HexResource.LUMBER):
            score -= 5.0

        return score

    if action.type == ActionType.BUILD_ROAD and action.target is not None:
        current_player = state.players[player_id]
        edge_id = action.target
        a, b = state.board.edges[edge_id]

        candidate_vertices = []
        if a not in current_player.settlements and a not in current_player.cities:
            candidate_vertices.append(a)
        if b not in current_player.settlements and b not in current_player.cities:
            candidate_vertices.append(b)

        if candidate_vertices:
            best_future = max(vertex_production_score(state, v) for v in candidate_vertices)
            return 80.0 + 0.4 * best_future

        return 60.0

    if action.type == ActionType.MOVE_ROBBER and action.target is not None:
        return 100.0 + robber_hex_score(state, action.target, player_id)

    if action.type == ActionType.ROLL_DICE:
        return 50.0

    if action.type == ActionType.END_TURN:
        return 0.0

    return 1.0

def tactical_priority_action(state, player_id: int) -> Action | None:
    """
    Twarda polityka:
    - jeśli można zbudować miasto, zrób to
    - jeśli można zbudować osadę, zrób to
    - jeśli można zagrać silną kartę rozwoju, rozważ to
    - trade tylko wtedy, gdy naprawdę pomaga i nie ma lepszej akcji budowy
    """
    actions = state.legal_actions()

    city_actions = [a for a in actions if a.type == ActionType.BUILD_CITY]
    if city_actions:
        return max(city_actions, key=lambda a: immediate_action_score(state, a, player_id))

    settlement_actions = [a for a in actions if a.type == ActionType.BUILD_SETTLEMENT]
    if settlement_actions:
        return max(settlement_actions, key=lambda a: immediate_action_score(state, a, player_id))

    road_building_actions = [a for a in actions if a.type == ActionType.PLAY_ROAD_BUILDING]
    if road_building_actions:
        return road_building_actions[0]

    knight_actions = [a for a in actions if a.type == ActionType.PLAY_KNIGHT]
    if knight_actions:
        return knight_actions[0]

    buy_dev_actions = [a for a in actions if a.type == ActionType.BUY_DEVELOPMENT_CARD]
    if buy_dev_actions:
        return buy_dev_actions[0]

    # Trade tylko jeśli nie ma budowy i trade jest naprawdę sensowny
    trade_actions = [a for a in actions if a.type == ActionType.TRADE_BANK]
    if trade_actions:
        best_trade = max(trade_actions, key=lambda a: immediate_action_score(state, a, player_id))
        best_trade_score = immediate_action_score(state, best_trade, player_id)

        # mocniej ograniczamy spam handlu
        if best_trade_score >= 145:
            return best_trade

    return None

def controlled_production_score(state, player_id: int) -> float:
    player = state.players[player_id]
    score = 0.0

    for vertex in player.settlements:
        score += vertex_production_score(state, vertex)

    for vertex in player.cities:
        score += 2.2 * vertex_production_score(state, vertex)

    return score


def open_settlement_spots_score(state, player_id: int) -> float:
    player = state.players[player_id]
    score = 0.0

    for vertex in range(len(state.board.vertex_positions)):
        if vertex in state.occupied_vertices:
            continue

        blocked = False
        for n in state.board.vertex_neighbors[vertex]:
            if n in state.occupied_vertices:
                blocked = True
                break
        if blocked:
            continue

        connected = False
        for edge_id in state.board.vertex_edges[vertex]:
            if edge_id in player.roads:
                connected = True
                break

        if connected:
            score += 0.6 * vertex_production_score(state, vertex)

    return score


def settlement_progress_score(player) -> float:
    brick = player.resources[HexResource.BRICK]
    lumber = player.resources[HexResource.LUMBER]
    wool = player.resources[HexResource.WOOL]
    grain = player.resources[HexResource.GRAIN]

    return (
        min(brick, 1) +
        min(lumber, 1) +
        min(wool, 1) +
        min(grain, 1)
    )


def city_progress_score(player) -> float:
    grain = player.resources[HexResource.GRAIN]
    ore = player.resources[HexResource.ORE]
    return min(grain, 2) + min(ore, 3)


def trade_power_score(player) -> float:
    """
    Premia za nadmiar zasobów, które można wymienić 4:1.
    """
    score = 0.0
    for amount in player.resources.values():
        if amount >= 4:
            score += 1.5 + 0.5 * (amount - 4)
    return score


def robber_hex_score(state, hex_id: int, root_player_id: int) -> float:
    if hex_id == state.robber_hex:
        return -999.0

    score = 0.0
    touched = players_touching_hex(state, hex_id)
    resource = state.board.hex_resources[hex_id]
    number = state.board.hex_numbers[hex_id]

    score += 2.0 * DICE_WEIGHT[number]

    # premia za blokowanie przeciwników
    for pid in touched:
        if pid == root_player_id:
            score -= 6.0
        else:
            score += 8.0
            opp = state.players[pid]
            if sum(opp.resources.values()) > 0:
                score += 5.0

    if resource == HexResource.DESERT:
        score -= 3.0

    return score


def choose_robber_action(actions: list[Action], state, root_player_id: int) -> Action:
    robber_actions = [a for a in actions if a.type == ActionType.MOVE_ROBBER]
    if not robber_actions:
        return weighted_action_choice(actions, state, root_player_id)

    return max(
        robber_actions,
        key=lambda a: robber_hex_score(state, a.target, root_player_id)
    )


def weighted_action_choice(actions: list[Action], state=None, root_player_id: int | None = None) -> Action:
    if state is not None and root_player_id is not None:
        robber_actions = [a for a in actions if a.type == ActionType.MOVE_ROBBER]
        if robber_actions:
            return choose_robber_action(actions, state, root_player_id)

        # twardy priorytet w rolloutach też
        city_actions = [a for a in actions if a.type == ActionType.BUILD_CITY]
        if city_actions:
            return max(city_actions, key=lambda a: immediate_action_score(state, a, root_player_id))

        settlement_actions = [a for a in actions if a.type == ActionType.BUILD_SETTLEMENT]
        if settlement_actions:
            return max(settlement_actions, key=lambda a: immediate_action_score(state, a, root_player_id))

    weighted = []
    for action in actions:
        w = action_priority(action)

        if state is not None:
            w += int(immediate_action_score(state, action, state.current_player) * 0.1)

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
    me = state.players[root_player_id]
    my_vp = state.victory_points(root_player_id)

    other_ids = [pid for pid in range(len(state.players)) if pid != root_player_id]
    others = [state.players[pid] for pid in other_ids]

    best_other_vp = max(state.victory_points(pid) for pid in other_ids) if other_ids else 0
    best_other_resources = max(sum(p.resources.values()) for p in others) if others else 0
    best_other_roads = max(len(p.roads) for p in others) if others else 0
    best_other_settlements = max(len(p.settlements) for p in others) if others else 0
    best_other_cities = max(len(p.cities) for p in others) if others else 0
    best_other_prod = max(controlled_production_score(state, pid) for pid in other_ids) if other_ids else 0.0
    best_other_open_spots = max(open_settlement_spots_score(state, pid) for pid in other_ids) if other_ids else 0.0
    best_other_settlement_ready = max(settlement_progress_score(state.players[pid]) for pid in other_ids) if other_ids else 0.0
    best_other_city_ready = max(city_progress_score(state.players[pid]) for pid in other_ids) if other_ids else 0.0
    best_other_trade = max(trade_power_score(state.players[pid]) for pid in other_ids) if other_ids else 0.0

    my_resources = sum(me.resources.values())
    my_roads = len(me.roads)
    my_settlements = len(me.settlements)
    my_cities = len(me.cities)
    my_prod = controlled_production_score(state, root_player_id)
    my_open_spots = open_settlement_spots_score(state, root_player_id)
    my_settlement_ready = settlement_progress_score(me)
    my_city_ready = city_progress_score(me)
    my_trade = trade_power_score(me)

    score = 0.0
    score += 18.0 * (my_vp - best_other_vp)
    score += 4.5 * (my_cities - best_other_cities)
    score += 3.2 * (my_settlements - best_other_settlements)
    score += 0.04 * (my_roads - best_other_roads)
    score += 0.16 * (my_resources - best_other_resources)
    score += 0.55 * (my_prod - best_other_prod)
    score += 0.10 * (my_open_spots - best_other_open_spots)
    score += 0.95 * (my_settlement_ready - best_other_settlement_ready)
    score += 0.80 * (my_city_ready - best_other_city_ready)
    score += 0.22 * (my_trade - best_other_trade)

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

        action = weighted_action_choice(actions, current_state, root_player_id)
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
    # Najpierw twarda polityka taktyczna
    forced_action = tactical_priority_action(root_state, player_id)
    if forced_action is not None:
        return forced_action

    root = Node(state=root_state)
    root.untried_actions = list(root_state.legal_actions())

    if not root.untried_actions:
        raise ValueError("Brak legalnych akcji w stanie początkowym.")

    for _ in range(iterations):
        node = root
        state = root_state

        # Selection
        while node.is_fully_expanded() and node.children and not state.is_terminal():
            node = select_child(node, exploration)
            state = state.apply(node.action_from_parent)

        # Expansion
        if not state.is_terminal() and node.untried_actions:
            action = weighted_action_choice(node.untried_actions, state, player_id)
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

        # Simulation
        value = rollout(state, root_player_id=player_id)

        # Backpropagation
        backpropagate(node, value)

    best_child = max(root.children.values(), key=lambda child: child.visits)
    return best_child.action_from_parent