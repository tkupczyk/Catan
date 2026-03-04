from core.board import create_test_board
from core.state import GameState, PlayerState
from core.rules import apply_action
from core.actions import Action, ActionType


def main():

    board = create_test_board()

    players = [PlayerState(), PlayerState()]

    state = GameState(board, players)

    apply_action(state, Action(ActionType.BUILD_SETTLEMENT, 0))
    apply_action(state, Action(ActionType.BUILD_ROAD, 0))

    apply_action(state, Action(ActionType.END_TURN))

    apply_action(state, Action(ActionType.BUILD_SETTLEMENT, 2))

    print("Player 0 settlements:", state.players[0].settlements)
    print("Player 1 settlements:", state.players[1].settlements)


if __name__ == "__main__":
    main()