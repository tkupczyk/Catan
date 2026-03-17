import random

from core.board import create_full_board, HexResource
from core.state import GameState, PlayerState
from core.actions import Action, ActionType
from ai.mcts import mcts_search


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

RESOURCE_WEIGHT = {
    HexResource.BRICK: 2.0,
    HexResource.LUMBER: 2.2,
    HexResource.WOOL: 1.0,
    HexResource.GRAIN: 1.5,
    HexResource.ORE: 1.5,
    HexResource.DESERT: 0.0,
}


def print_player_summary(state, player_id):
    p = state.players[player_id]
    print(
        f"P{player_id}: "
        f"VP={state.victory_points(player_id)}, "
        f"settlements={len(p.settlements)}, "
        f"cities={len(p.cities)}, "
        f"roads={len(p.roads)}, "
        f"resources={{"
        f"brick:{p.resources[HexResource.BRICK]}, "
        f"lumber:{p.resources[HexResource.LUMBER]}, "
        f"wool:{p.resources[HexResource.WOOL]}, "
        f"grain:{p.resources[HexResource.GRAIN]}, "
        f"ore:{p.resources[HexResource.ORE]}}}"
    )


def vertex_hexes(board, vertex):
    result = []
    for hex_id, verts in enumerate(board.hex_vertices):
        if vertex in verts:
            result.append(hex_id)
    return result


def score_setup_vertex(state, vertex):
    board = state.board
    touching_hexes = vertex_hexes(board, vertex)

    score = 0.0
    distinct_resources = set()

    for hex_id in touching_hexes:
        resource = board.hex_resources[hex_id]
        number = board.hex_numbers[hex_id]

        score += DICE_WEIGHT[number]
        score += RESOURCE_WEIGHT[resource]

        if resource != HexResource.DESERT:
            distinct_resources.add(resource)

        # lekka premia za szczególnie dobre pola
        if number in (6, 8):
            score += 2.0

    # premia za różnorodność zasobów
    score += 1.5 * len(distinct_resources)

    # mocna premia za dostęp do lumber i brick
    if HexResource.LUMBER in distinct_resources:
        score += 2.5
    if HexResource.BRICK in distinct_resources:
        score += 2.0

    return score


def choose_best_setup_settlement(state):
    actions = state.legal_actions()
    settlement_actions = [a for a in actions if a.type == ActionType.BUILD_SETTLEMENT]

    best_action = max(
        settlement_actions,
        key=lambda a: score_setup_vertex(state, a.target)
    )
    return best_action


def choose_best_setup_road(state):
    actions = state.legal_actions()
    road_actions = [a for a in actions if a.type == ActionType.BUILD_ROAD]

    # prosta heurystyka:
    # wybierz drogę prowadzącą do wierzchołka o najlepszym potencjale przyszłej osady
    best_action = None
    best_score = float("-inf")

    current_player = state.players[state.current_player]

    for action in road_actions:
        edge_id = action.target
        a, b = state.board.edges[edge_id]

        candidates = []
        if a not in current_player.settlements and a not in current_player.cities:
            candidates.append(a)
        if b not in current_player.settlements and b not in current_player.cities:
            candidates.append(b)

        if not candidates:
            score = 0.0
        else:
            score = max(score_setup_vertex(state, v) for v in candidates)

        if score > best_score:
            best_score = score
            best_action = action

    return best_action if best_action is not None else road_actions[0]


def run_auto_setup(state):
    while state.phase != "MAIN":
        if state.phase in ("SETUP_SETTLEMENT_1", "SETUP_SETTLEMENT_2"):
            action = choose_best_setup_settlement(state)
        elif state.phase in ("SETUP_ROAD_1", "SETUP_ROAD_2"):
            action = choose_best_setup_road(state)
        else:
            action = state.legal_actions()[0]

        state = state.apply(action)

    return state


def main():
    random.seed(42)

    board = create_full_board()
    desert_hex = next(i for i, r in enumerate(board.hex_resources) if r == HexResource.DESERT)

    state = GameState(
        board=board,
        players=[PlayerState(), PlayerState()],
        robber_hex=desert_hex,
    )

    print("=== AUTO SETUP ===")
    state = run_auto_setup(state)
    print("Setup finished.")
    print_player_summary(state, 0)
    print_player_summary(state, 1)
    print()

    max_turns = 20

    for turn in range(max_turns):
        if state.is_terminal():
            break

        print(f"=== TURN {turn + 1} | PLAYER {state.current_player} ===")

        step = 0
        while True:
            if state.is_terminal():
                break

            actions = state.legal_actions()
            if not actions:
                print("No legal actions.")
                break

            current_player = state.current_player
            action = mcts_search(
                state,
                player_id=current_player,
                iterations=200,
            )

            print(f"Step {step}: {action}")
            state = state.apply(action)
            step += 1

            if action.type == ActionType.END_TURN:
                break

        print_player_summary(state, 0)
        print_player_summary(state, 1)
        print(f"Last roll: {state.last_roll}")
        print(f"Phase: {state.phase}")
        print(f"Robber hex: {state.robber_hex}")
        print()

    print("=== FINAL STATE ===")
    print_player_summary(state, 0)
    print_player_summary(state, 1)

    if state.victory_points(0) > state.victory_points(1):
        print("Winner: Player 0")
    elif state.victory_points(1) > state.victory_points(0):
        print("Winner: Player 1")
    else:
        print("Draw")


if __name__ == "__main__":
    main()