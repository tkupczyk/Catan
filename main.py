from core.board import create_test_board
from core.state import GameState, PlayerState
from core.actions import Action, ActionType


def print_actions(state, label):
    print(f"\n{label}")
    for a in state.legal_actions():
        print(a)


def main():
    board = create_test_board()
    state = GameState(board=board, players=[PlayerState(), PlayerState()])

    print_actions(state, "Legal actions at start:")

    # Gracz 0 buduje pierwszą osadę
    state = state.apply(Action(ActionType.BUILD_SETTLEMENT, 0))
    print("\nAfter P0 settlement at 0:")
    print("P0 settlements:", state.players[0].settlements)

    print_actions(state, "Legal actions after first settlement:")

    # Gracz 0 buduje drogę wychodzącą z osady
    state = state.apply(Action(ActionType.BUILD_ROAD, 0))
    print("\nAfter P0 road at edge 0:")
    print("P0 roads:", state.players[0].roads)

    print_actions(state, "Legal actions after first road:")

    # Koniec tury
    state = state.apply(Action(ActionType.END_TURN, None))
    print("\nCurrent player after end turn:", state.current_player)

    print_actions(state, "Legal actions for P1:")
    

if __name__ == "__main__":
    main()