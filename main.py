import random
import pygame

from core import board
from core.board import create_full_board, HexResource
from core.state import GameState, PlayerState
from core.actions import Action, ActionType
from ui.pygame_view import PygameView
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

        if number in (6, 8):
            score += 2.0

    score += 1.5 * len(distinct_resources)

    if HexResource.LUMBER in distinct_resources:
        score += 2.5
    if HexResource.BRICK in distinct_resources:
        score += 2.0

    return score


def choose_best_setup_settlement(state):
    actions = state.legal_actions()
    settlement_actions = [a for a in actions if a.type == ActionType.BUILD_SETTLEMENT]

    return max(settlement_actions, key=lambda a: score_setup_vertex(state, a.target))


def choose_best_setup_road(state):
    actions = state.legal_actions()
    road_actions = [a for a in actions if a.type == ActionType.BUILD_ROAD]

    current_player = state.players[state.current_player]

    best_action = None
    best_score = float("-inf")

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
    HUMAN_PLAYER = 0
    AI_PLAYER = 1

    board = create_full_board(randomize=True)
    desert_hex = next(i for i, r in enumerate(board.hex_resources) if r == HexResource.DESERT)

    print("\n=== DEBUG: 6/8 positions ===")
    for i, num in enumerate(board.hex_numbers):
        if num in (6, 8):
            print(f"Hex {i}: {num}")

    state = GameState(
        board=board,
        players=[PlayerState(), PlayerState()],
        robber_hex=desert_hex,
        development_deck=GameState.default_development_deck(),
    )

    state = run_auto_setup(state)

    state.current_player = HUMAN_PLAYER
    state.phase = "MAIN"
    state.dice_rolled = False
    state.last_roll = None

    print("After setup:")
    print("Current player:", state.current_player)
    print("Phase:", state.phase)
    print("Dice rolled:", state.dice_rolled)
    print("Legal actions:", state.legal_actions())

    view = PygameView()
    running = True

    ai_thinking = False
    mouse_pressed_on_ui = False


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if state.is_terminal():
                continue

            # ruchy człowieka tylko w jego turze
            if state.current_player == HUMAN_PLAYER:
                if event.type == pygame.MOUSEMOTION:
                    view.update_hover(event.pos)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pressed_on_ui = view.begin_ui_press(event.pos)

                if event.type == pygame.MOUSEBUTTONUP:
                    new_state = view.end_ui_press(state, event.pos)

                    if new_state is not None:
                        state = new_state
                    else:
                        trade_state = view.handle_trade_selection_click(state, event.pos)
                        if trade_state is not None:
                            state = trade_state
                        elif not mouse_pressed_on_ui:
                            state = view.handle_click(state, event.pos)

                    mouse_pressed_on_ui = False

        # ruch AI
        if state.current_player == AI_PLAYER and not ai_thinking:
            ai_thinking = True

            if not state.is_terminal():
                actions = state.legal_actions()
                if actions:
                    action = mcts_search(
                        state,
                        player_id=AI_PLAYER,
                        iterations=250,
                    )
                    state = state.apply(action)

            ai_thinking = False

        view.draw(state)
        view.tick(30)

    view.quit()


if __name__ == "__main__":
    main()