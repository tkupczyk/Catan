from .actions import Action, ActionType
from .state import GameState


def can_build_settlement(state: GameState, vertex: int):

    if vertex in state.occupied_vertices:
        return False

    # brak sąsiednich osad
    for n in state.board.vertex_neighbors[vertex]:
        if n in state.occupied_vertices:
            return False

    return True


def can_build_road(state: GameState, edge_id: int):

    if edge_id in state.occupied_edges:
        return False

    a, b = state.board.edges[edge_id]

    player = state.players[state.current_player]

    if a in player.settlements or b in player.settlements:
        return True

    return False


def apply_action(state: GameState, action: Action):

    player = state.players[state.current_player]

    if action.type == ActionType.BUILD_SETTLEMENT:

        v = action.target

        if can_build_settlement(state, v):

            player.settlements.add(v)
            state.occupied_vertices.add(v)

    if action.type == ActionType.BUILD_ROAD:

        e = action.target

        if can_build_road(state, e):

            player.roads.add(e)
            state.occupied_edges.add(e)

    if action.type == ActionType.END_TURN:
        state.next_player()