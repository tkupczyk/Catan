import pygame

from core.board import create_full_board, HexResource
from core.state import GameState, PlayerState, DevelopmentCard
from core.actions import Action, ActionType
from ui.pygame_view import PygameView
from ai.mcts import mcts_search

# =========================
# DEBUG FLAGS
# =========================
DEBUG_START_RESOURCES = False
DEBUG_START_DEV_CARDS_HUMAN = False
DEBUG_START_DEV_CARDS_AI = False

DEBUG_RESOURCE_AMOUNT = 999

DEBUG_HUMAN_DEV_CARDS = [
    DevelopmentCard.KNIGHT,
    DevelopmentCard.KNIGHT,
    DevelopmentCard.KNIGHT,
    DevelopmentCard.ROAD_BUILDING,
    DevelopmentCard.YEAR_OF_PLENTY,
    DevelopmentCard.MONOPOLY,
    DevelopmentCard.VICTORY_POINT,
]

DEBUG_AI_DEV_CARDS = [
    DevelopmentCard.KNIGHT,
    DevelopmentCard.ROAD_BUILDING,
]

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
    game_board = state.board
    touching_hexes = vertex_hexes(game_board, vertex)

    score = 0.0
    distinct_resources = set()

    for hex_id in touching_hexes:
        resource = game_board.hex_resources[hex_id]
        number = game_board.hex_numbers[hex_id]

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


def apply_debug_resources(state):
    for player in state.players:
        player.resources[HexResource.BRICK] = DEBUG_RESOURCE_AMOUNT
        player.resources[HexResource.LUMBER] = DEBUG_RESOURCE_AMOUNT
        player.resources[HexResource.WOOL] = DEBUG_RESOURCE_AMOUNT
        player.resources[HexResource.GRAIN] = DEBUG_RESOURCE_AMOUNT
        player.resources[HexResource.ORE] = DEBUG_RESOURCE_AMOUNT


def apply_debug_dev_cards(state):
    if DEBUG_START_DEV_CARDS_HUMAN and len(state.players) > 0:
        state.players[0].development_cards.extend(DEBUG_HUMAN_DEV_CARDS)

    if DEBUG_START_DEV_CARDS_AI and len(state.players) > 1:
        state.players[1].development_cards.extend(DEBUG_AI_DEV_CARDS)


def create_new_game(human_player=0, num_players=3):
    game_board = create_full_board(randomize=True)
    desert_hex = next(i for i, r in enumerate(game_board.hex_resources) if r == HexResource.DESERT)

    print("\n=== DEBUG: 6/8 positions ===")
    for i, num in enumerate(game_board.hex_numbers):
        if num in (6, 8):
            print(f"Hex {i}: {num}")

    state = GameState(
        board=game_board,
        players=[PlayerState() for _ in range(num_players)],
        robber_hex=desert_hex,
        development_deck=GameState.default_development_deck(),
    )


    if DEBUG_START_RESOURCES:
        apply_debug_resources(state)

    if DEBUG_START_DEV_CARDS_HUMAN or DEBUG_START_DEV_CARDS_AI:
        apply_debug_dev_cards(state)

    print("After setup:")
    print("Current player:", state.current_player)
    print("Phase:", state.phase)
    print("Dice rolled:", state.dice_rolled)
    print("Legal actions:", state.legal_actions())

    if DEBUG_START_RESOURCES:
        print("\n[DEBUG] Start resources enabled")
        for pid, player in enumerate(state.players):
            print(
                f"P{pid} resources:",
                {
                    "brick": player.resources[HexResource.BRICK],
                    "lumber": player.resources[HexResource.LUMBER],
                    "wool": player.resources[HexResource.WOOL],
                    "grain": player.resources[HexResource.GRAIN],
                    "ore": player.resources[HexResource.ORE],
                }
            )

    if DEBUG_START_DEV_CARDS_HUMAN or DEBUG_START_DEV_CARDS_AI:
        print("\n[DEBUG] Start development cards enabled")
        for pid, player in enumerate(state.players):
            print(f"P{pid} dev cards:", [card.value for card in player.development_cards])

    return state


def main():
    HUMAN_PLAYER = 0
    mode = "menu"   # "menu" albo "game"
    state = None

    view = PygameView()
    running = True

    ai_thinking = False
    mouse_pressed_on_ui = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if mode == "menu":
                if event.type == pygame.MOUSEMOTION:
                    view.update_hover(event.pos)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    view.begin_ui_press(event.pos)

                if event.type == pygame.MOUSEBUTTONUP:
                    menu_action = view.end_ui_press(None, event.pos)

                    if menu_action == "START_HUMAN":
                        HUMAN_PLAYER = 0
                        state = create_new_game(
                            human_player=0,
                            num_players=view.menu_selected_players,
                        )
                        mode = "game"
                        view.in_menu = False
                        ai_thinking = False
                        mouse_pressed_on_ui = False
                        view.close_modal()
                        view.pending_card_action = None
                        view.pressed_button = None

                    elif menu_action == "START_AI":
                        HUMAN_PLAYER = None
                        state = create_new_game(
                            human_player=None,
                            num_players=view.menu_selected_players,
                        )
                        mode = "game"
                        view.in_menu = False
                        ai_thinking = False
                        mouse_pressed_on_ui = False
                        view.close_modal()
                        view.pending_card_action = None
                        view.pressed_button = None

                    elif menu_action == "QUIT":
                        running = False

            elif mode == "game":
                human_turn = (HUMAN_PLAYER is not None and state.current_player == HUMAN_PLAYER)

                if human_turn:
                    if event.type == pygame.MOUSEMOTION:
                        view.update_hover(event.pos)

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pressed_on_ui = view.begin_ui_press(event.pos)

                    if event.type == pygame.MOUSEBUTTONUP:
                        # 1. modal
                        if view.active_modal is not None:
                            modal_result = view.handle_modal_click(event.pos)

                            if isinstance(modal_result, dict):
                                if (
                                    modal_result["type"] == "confirmed_two_resources"
                                    and view.pending_card_action == "year_of_plenty"
                                ):
                                    state = state.apply(
                                        Action(
                                            ActionType.PLAY_YEAR_OF_PLENTY,
                                            chosen_resources=tuple(modal_result["resources"]),
                                        )
                                    )

                                elif (
                                    modal_result["type"] == "confirmed_one_resource"
                                    and view.pending_card_action == "monopoly"
                                ):
                                    state = state.apply(
                                        Action(
                                            ActionType.PLAY_MONOPOLY,
                                            resource_get=modal_result["resource"],
                                        )
                                    )

                                elif modal_result["type"] == "confirmed_steal_target":
                                    state = state.apply(
                                        Action(
                                            ActionType.STEAL_FROM_PLAYER,
                                            target=modal_result["target_player"],
                                        )
                                    )

                                view.pending_card_action = None
                                view.close_modal()

                            elif modal_result == "closed":
                                view.pending_card_action = None

                            mouse_pressed_on_ui = False
                            continue

                        # 2. zwykłe UI
                        new_state = view.end_ui_press(state, event.pos)

                        if new_state is not None:
                            if new_state == "RESTART":
                                if HUMAN_PLAYER is None:
                                    state = create_new_game(
                                        human_player=None,
                                        num_players=view.menu_selected_players,
                                    )
                                else:
                                    state = create_new_game(
                                        human_player=HUMAN_PLAYER,
                                        num_players=view.menu_selected_players,
                                    )

                                view.close_modal()
                                view.pending_card_action = None
                                view.pressed_button = None
                                ai_thinking = False
                                mouse_pressed_on_ui = False
                            
                            elif new_state == "MENU":
                                mode = "menu"
                                state = None
                                view.in_menu = True
                                view.pressed_button = None
                                view.hovered_button = None
                                view.close_modal()
                                ai_thinking = False
                                mouse_pressed_on_ui = False
                            else:
                                state = new_state
                        else:
                            trade_state = view.handle_trade_selection_click(state, event.pos)
                            if trade_state is not None:
                                state = trade_state
                            elif not mouse_pressed_on_ui:
                                state = view.handle_click(state, event.pos)

                        mouse_pressed_on_ui = False

                else:
                    # pozwól kliknąć restart/help także gdy gra AI
                    if event.type == pygame.MOUSEMOTION:
                        view.update_hover(event.pos)

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pressed_on_ui = view.begin_ui_press(event.pos)

                    if event.type == pygame.MOUSEBUTTONUP:
                        new_state = view.end_ui_press(state, event.pos)

                        if new_state == "RESTART":
                            if HUMAN_PLAYER is None:
                                state = create_new_game(
                                    human_player=None,
                                    num_players=view.menu_selected_players,
                                )
                            else:
                                state = create_new_game(
                                    human_player=HUMAN_PLAYER,
                                    num_players=view.menu_selected_players,
                                )

                            view.close_modal()
                            view.pending_card_action = None
                            view.pressed_button = None
                            ai_thinking = False
                            mouse_pressed_on_ui = False

                        elif new_state == "MENU":
                            mode = "menu"
                            state = None
                            view.in_menu = True
                            view.pressed_button = None
                            view.hovered_button = None
                            view.close_modal()
                            ai_thinking = False
                            mouse_pressed_on_ui = False

                        mouse_pressed_on_ui = False

        # ruch AI - poza pętlą eventów
        if mode == "game" and state is not None:
            ai_turn = (HUMAN_PLAYER is None or state.current_player != HUMAN_PLAYER)

            if not state.is_terminal() and ai_turn and not ai_thinking:
                ai_thinking = True

                actions = state.legal_actions()
                if actions:
                    action = mcts_search(
                        state,
                        player_id=state.current_player,
                        iterations=250,
                    )
                    state = state.apply(action)

                ai_thinking = False

        if (
            mode == "game"
            and state is not None
            and state.phase == "STEAL_PLAYER"
            and state.current_player == 0
            and view.active_modal is None
            and not view.steal_modal_opened_for_phase
        ):
            view.open_modal(
                "choose_steal_target",
                steal_targets=list(state.steal_targets),
                selected_target=None,
            )
            view.steal_modal_opened_for_phase = True

        if state is not None and state.phase != "STEAL_PLAYER":
            view.steal_modal_opened_for_phase = False

        # rysowanie - poza pętlą eventów
        if mode == "menu":
            view.draw_menu()
        else:
            view.draw(state)

        view.tick(30)

    view.quit()


if __name__ == "__main__":
    main()