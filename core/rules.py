def can_build_settlement(state, vertex: int) -> bool:
    if vertex in state.occupied_vertices:
        return False

    for n in state.board.vertex_neighbors[vertex]:
        if n in state.occupied_vertices:
            return False

    player = state.players[state.current_player]

    # Uproszczony setup:
    # jeśli gracz nie ma jeszcze żadnej osady, może postawić pierwszą bez drogi
    if len(player.settlements) == 0:
        return True

    # Poza setupem osada musi stykać się z drogą gracza
    for edge_id in state.board.vertex_edges[vertex]:
        if edge_id in player.roads:
            return True

    return False


def can_build_road(state, edge_id: int) -> bool:
    if edge_id in state.occupied_edges:
        return False

    a, b = state.board.edges[edge_id]
    player = state.players[state.current_player]

    # Droga może dotykać osady gracza
    if a in player.settlements or b in player.settlements:
        return True

    # Albo innej drogi gracza
    for vertex in (a, b):
        for neighbor_edge in state.board.vertex_edges[vertex]:
            if neighbor_edge in player.roads:
                return True

    return False