from .board import HexResource
from .board import HexResource, PortType

ROAD_COST = {
    HexResource.BRICK: 1,
    HexResource.LUMBER: 1,
}

SETTLEMENT_COST = {
    HexResource.BRICK: 1,
    HexResource.LUMBER: 1,
    HexResource.WOOL: 1,
    HexResource.GRAIN: 1,
}

CITY_COST = {
    HexResource.GRAIN: 2,
    HexResource.ORE: 3,
}


def has_resources(player, cost: dict[HexResource, int]) -> bool:
    for resource, amount in cost.items():
        if player.resources[resource] < amount:
            return False
    return True

def get_player_trade_ratio(state, player_id: int, give_resource: HexResource) -> int:
    """
    Zwraca najlepszy dostępny kurs handlu dla danego gracza i surowca:
    - 2:1 jeśli ma port specjalny dla tego surowca
    - 3:1 jeśli ma port ogólny
    - 4:1 domyślnie
    """
    player = state.players[player_id]
    player_vertices = set(player.settlements) | set(player.cities)

    best_ratio = 4

    for (v1, v2), port_type in state.board.ports:
        if v1 not in player_vertices and v2 not in player_vertices:
            continue

        if port_type == PortType.THREE_TO_ONE:
            best_ratio = min(best_ratio, 3)
        elif port_type == PortType.BRICK and give_resource == HexResource.BRICK:
            best_ratio = min(best_ratio, 2)
        elif port_type == PortType.LUMBER and give_resource == HexResource.LUMBER:
            best_ratio = min(best_ratio, 2)
        elif port_type == PortType.WOOL and give_resource == HexResource.WOOL:
            best_ratio = min(best_ratio, 2)
        elif port_type == PortType.GRAIN and give_resource == HexResource.GRAIN:
            best_ratio = min(best_ratio, 2)
        elif port_type == PortType.ORE and give_resource == HexResource.ORE:
            best_ratio = min(best_ratio, 2)

    return best_ratio

def pay_cost(player, cost: dict[HexResource, int]) -> None:
    for resource, amount in cost.items():
        player.resources[resource] -= amount


def can_move_robber(state, hex_id: int) -> bool:
    if state.phase != "ROBBER":
        return False
    if hex_id < 0 or hex_id >= len(state.board.hex_vertices):
        return False
    return hex_id != state.robber_hex


def can_trade_bank(state, give_resource, get_resource) -> bool:
    if state.phase != "MAIN":
        return False

    if not state.dice_rolled:
        return False

    if give_resource == get_resource:
        return False

    player = state.players[state.current_player]
    ratio = get_player_trade_ratio(state, state.current_player, give_resource)
    return player.resources[give_resource] >= ratio


def can_build_settlement(state, vertex: int) -> bool:
    if vertex in state.occupied_vertices:
        return False

    for n in state.board.vertex_neighbors[vertex]:
        if n in state.occupied_vertices:
            return False

    player = state.players[state.current_player]

    if state.phase in ("SETUP_SETTLEMENT_1", "SETUP_SETTLEMENT_2"):
        return True

    if state.phase != "MAIN":
        return False

    if not state.dice_rolled:
        return False

    if not has_resources(player, SETTLEMENT_COST):
        return False

    for edge_id in state.board.vertex_edges[vertex]:
        if edge_id in player.roads:
            return True

    return False


def can_build_road(state, edge_id: int) -> bool:
    if edge_id in state.occupied_edges:
        return False

    a, b = state.board.edges[edge_id]
    player = state.players[state.current_player]

    if state.phase in ("SETUP_ROAD_1", "SETUP_ROAD_2"):
        if state.last_setup_settlement is None:
            return False
        return a == state.last_setup_settlement or b == state.last_setup_settlement

    if state.phase != "MAIN":
        return False

    if not state.dice_rolled:
        return False

    if not has_resources(player, ROAD_COST):
        return False

    if a in player.settlements or b in player.settlements or a in player.cities or b in player.cities:
        return True

    for vertex in (a, b):
        for other_edge in state.board.vertex_edges[vertex]:
            if other_edge in player.roads:
                return True

    return False


def can_build_city(state, vertex: int) -> bool:
    if state.phase != "MAIN":
        return False

    if not state.dice_rolled:
        return False

    player = state.players[state.current_player]

    if vertex not in player.settlements:
        return False

    return has_resources(player, CITY_COST)