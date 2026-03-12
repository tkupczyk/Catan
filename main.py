from core.board import create_full_board
from core.state import GameState, PlayerState
from core.actions import Action, ActionType


def print_state(state, label):
    print(f"\n--- {label} ---")
    print("Phase:", state.phase)
    print("Current player:", state.current_player)
    print("P0 settlements:", state.players[0].settlements)
    print("P0 roads:", state.players[0].roads)
    print("P1 settlements:", state.players[1].settlements)
    print("P1 roads:", state.players[1].roads)
    print("Legal actions:", len(state.legal_actions()))


def first_action_of_type(state, action_type):
    return next(a for a in state.legal_actions() if a.type == action_type)


def main():
    board = create_full_board()
    state = GameState(board=board, players=[PlayerState(), PlayerState()])

    print_state(state, "Start")

    # P0 settlement 1
    state = state.apply(first_action_of_type(state, ActionType.BUILD_SETTLEMENT))
    print_state(state, "After P0 settlement 1")

    # P0 road 1
    state = state.apply(first_action_of_type(state, ActionType.BUILD_ROAD))
    print_state(state, "After P0 road 1")

    # P1 settlement 1
    state = state.apply(first_action_of_type(state, ActionType.BUILD_SETTLEMENT))
    print_state(state, "After P1 settlement 1")

    # P1 road 1
    state = state.apply(first_action_of_type(state, ActionType.BUILD_ROAD))
    print_state(state, "After P1 road 1")

    # P1 settlement 2
    state = state.apply(first_action_of_type(state, ActionType.BUILD_SETTLEMENT))
    print_state(state, "After P1 settlement 2")

    # P1 road 2
    state = state.apply(first_action_of_type(state, ActionType.BUILD_ROAD))
    print_state(state, "After P1 road 2")

    # P0 settlement 2
    state = state.apply(first_action_of_type(state, ActionType.BUILD_SETTLEMENT))
    print_state(state, "After P0 settlement 2")

    # P0 road 2
    state = state.apply(first_action_of_type(state, ActionType.BUILD_ROAD))
    print_state(state, "After P0 road 2")

    print("\nSetup finished?")
    print("Phase:", state.phase)
    print("Current player:", state.current_player)


if __name__ == "__main__":
    main()