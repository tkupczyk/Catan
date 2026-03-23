import random

from core.board import create_full_board, HexResource
from core.state import GameState, PlayerState
from ai.mcts import mcts_search


def print_resources(state):
    for i, p in enumerate(state.players):
        print(
            f"P{i}: "
            f"brick={p.resources[HexResource.BRICK]}, "
            f"lumber={p.resources[HexResource.LUMBER]}, "
            f"wool={p.resources[HexResource.WOOL]}, "
            f"grain={p.resources[HexResource.GRAIN]}, "
            f"ore={p.resources[HexResource.ORE]}"
        )


def main():
    random.seed(42)

    board = create_full_board()
    desert_hex = next(i for i, r in enumerate(board.hex_resources) if r == HexResource.DESERT)

    state = GameState(
        board=board,
        players=[PlayerState(), PlayerState()],
        current_player=0,
        phase="ROBBER",
        robber_hex=desert_hex,
        dice_rolled=True,
        last_roll=7,
    )

    # P0 ma swoją osadę gdzieś indziej
    state.players[0].settlements.update({10})
    state.occupied_vertices.update({10})

    # P1 ma osady przy Hex 0
    # Hex 0: vertices [0, 1, 2, 3, 4, 5]
    state.players[1].settlements.update({0, 3})
    state.occupied_vertices.update({0, 3})

    # P1 ma zasoby do kradzieży
    state.players[1].resources[HexResource.BRICK] = 2
    state.players[1].resources[HexResource.WOOL] = 1
    state.players[1].resources[HexResource.GRAIN] = 1

    print("=== BEFORE ROBBER TEST ===")
    print("Current player:", state.current_player)
    print("Phase:", state.phase)
    print("Robber hex:", state.robber_hex)
    print("Legal actions:", len(state.legal_actions()))
    print_resources(state)

    best_action = mcts_search(state, player_id=0, iterations=200)

    print("\n=== MCTS ROBBER CHOICE ===")
    print("Chosen action:", best_action)

    next_state = state.apply(best_action)

    print("\n=== AFTER ROBBER MOVE ===")
    print("Current player:", next_state.current_player)
    print("Phase:", next_state.phase)
    print("Robber hex:", next_state.robber_hex)
    print_resources(next_state)


if __name__ == "__main__":
    main()