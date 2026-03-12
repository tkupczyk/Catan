def can_build_settlement(state, vertex: int) -> bool:
    if vertex in state.occupied_vertices:
        return False

    for n in state.board.vertex_neighbors[vertex]:
        if n in state.occupied_vertices:
            return False

    if state.phase in ("SETUP_SETTLEMENT_1", "SETUP_SETTLEMENT_2"):
        return True

    player = state.players[state.current_player]

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

    if a in player.settlements or b in player.settlements:
        return True

    for vertex in (a, b):
        for other_edge in state.board.vertex_edges[vertex]:
            if other_edge in player.roads:
                return True

    return False