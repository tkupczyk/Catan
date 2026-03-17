from .board import HexResource


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
    return player.resources[give_resource] >= 4


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