import math
import pygame
import os
from core.actions import Action, ActionType
from core.board import HexResource
from core.board import HexResource, PortType
from core import rules, state

BACKGROUND = (245, 240, 220)
EDGE_COLOR = (80, 80, 80)
VERTEX_COLOR = (120, 120, 120)
TEXT_COLOR = (20, 20, 20)
ROBBER_COLOR = (30, 30, 30)
HIGHLIGHT_VERTEX = (255, 255, 0)
HIGHLIGHT_EDGE = (255, 255, 0)
HIGHLIGHT_HEX = (255, 200, 0)
BUTTON_BG = (220, 220, 220)
BUTTON_BORDER = (80, 80, 80)
BUTTON_TEXT = (20, 20, 20)
BUTTON_DISABLED = (180, 180, 180)
BUTTON_HOVER_BG = (235, 235, 235)
BUTTON_PRESSED_BG = (180, 180, 180)
BUTTON_SHADOW = (120, 120, 120)
PANEL_BG = (238, 233, 214)
PANEL_BORDER = (90, 90, 90)
SPECIAL_ICON_COLOR = (70, 70, 70)

PLAYER_COLORS = [
    (200, 50, 50),   # gracz 0
    (50, 90, 200),   # gracz 1
    (50, 160, 80),   # zapas
    (180, 120, 30),  # zapas
]


HEX_COLORS = {
    HexResource.BRICK: (178, 92, 70),
    HexResource.LUMBER: (70, 140, 80),
    HexResource.WOOL: (150, 200, 120),
    HexResource.GRAIN: (220, 200, 90),
    HexResource.ORE: (130, 130, 140),
    HexResource.DESERT: (220, 195, 140),
    
}

TRADE_RESOURCES = [
    HexResource.BRICK,
    HexResource.LUMBER,
    HexResource.WOOL,
    HexResource.GRAIN,
    HexResource.ORE,
]

class PygameView:
    def __init__(self, width: int = 1400, height: int = 1080):
        pygame.init()
        pygame.font.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Catan - Debug View")

        self.info_button_rect = pygame.Rect(self.width - 60, 20, 40, 40)

        self.font_small = pygame.font.SysFont("arial", 18)
        self.font_medium = pygame.font.SysFont("arial", 24, bold=True)
        self.font_large = pygame.font.SysFont("arial", 30, bold=True)

        self.play_cards_panel_rect = pygame.Rect(840, 820, 170, 220)
        self.play_knight_card_rect = pygame.Rect(850, 855, 132, 32)
        self.play_road_building_rect = pygame.Rect(850, 890, 132, 32)
        self.play_year_of_plenty_rect = pygame.Rect(850, 925, 132, 32)
        self.play_monopoly_rect = pygame.Rect(850, 960, 132, 32)
        self.vp_card_rect = pygame.Rect(850, 995, 132, 32)

        self.roll_button_rect = pygame.Rect(1030, 705, 140, 42)
        self.end_turn_button_rect = pygame.Rect(1190, 705, 140, 42)
        self.buy_dev_card_rect = pygame.Rect(1110, 752, 140, 42)

        self.resource_icons = self.load_resource_icons()
        self.ui_icons = self.load_ui_icons()
        self.hovered_button = None
        self.pressed_button = None
        self.selected_give_resource = None
        self.selected_get_resource = None
        self.pending_card_action = None

        self.trade_give_rects = {}
        self.trade_get_rects = {}

        # --- TRADE PANEL ---
        start_x = 1035
        give_y = 880
        get_y = 935

        trade_button_w = 40
        trade_button_h = 40
        trade_gap = 8

        # --- MODAL ---
        self.active_modal = None
        self.modal_data = {}
        self.pending_card_action = None

        # mały modal do kart
        self.card_modal_rect = pygame.Rect(470, 300, 460, 300)
        self.card_modal_close_rect = pygame.Rect(870, 315, 40, 30)

        # duży modal do pomocy
        self.help_modal_rect = pygame.Rect(170, 80, 1060, 860)
        self.help_modal_close_rect = pygame.Rect(1165, 95, 40, 30)

        self.help_tab = "ui"
        self.help_page = 0

        self.help_tab_ui_rect = pygame.Rect(230, 145, 170, 40)
        self.help_tab_rules_rect = pygame.Rect(410, 145, 170, 40)

        self.help_prev_rect = pygame.Rect(1030, 145, 40, 40)
        self.help_next_rect = pygame.Rect(1080, 145, 40, 40)


        self.modal_resource_rects_row1 = {}
        self.modal_resource_rects_row2 = {}

        modal_start_x = 550
        modal_y1 = 395
        modal_y2 = 465
        modal_button_w = 48
        modal_button_h = 48
        modal_gap = 14

        for i, resource in enumerate(TRADE_RESOURCES):
            x = modal_start_x + i * (modal_button_w + modal_gap)
            self.modal_resource_rects_row1[resource] = pygame.Rect(
                x, modal_y1, modal_button_w, modal_button_h
            )
            self.modal_resource_rects_row2[resource] = pygame.Rect(
                x, modal_y2, modal_button_w, modal_button_h
            )

        self.modal_confirm_rect = pygame.Rect(610, 535, 180, 42)

        for i, resource in enumerate(TRADE_RESOURCES):
            x = start_x + 72 + i * (trade_button_w + trade_gap)
            self.trade_give_rects[resource] = pygame.Rect(
                x, give_y, trade_button_w, trade_button_h
            )
            self.trade_get_rects[resource] = pygame.Rect(
                x, get_y, trade_button_w, trade_button_h
            )

        self.trade_execute_rect = pygame.Rect(1110, 992, 150, 42)


        self.clock = pygame.time.Clock()


    def load_ui_icons(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        pictures_dir = os.path.join(base_dir, "pictures")

        file_map = {
            "settlement": "settlement.png",
            "city": "city.png",
            "road": "road.png",
            "card": "card.png",
            "knight": "knight.png",
            "nwr": "nwr.png",
            "ndh": "ndh.png",
        }

        icons = {}

        for name, filename in file_map.items():
            path = os.path.join(pictures_dir, filename)
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.smoothscale(image, (28, 28))
            icons[name] = image

        return icons

    def current_modal_rect(self):
        if self.active_modal == "help":
            return self.help_modal_rect
        return self.card_modal_rect

    def current_modal_close_rect(self):
        if self.active_modal == "help":
            return self.help_modal_close_rect
        return self.card_modal_close_rect

    def load_resource_icons(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        pictures_dir = os.path.join(base_dir, "pictures")

        file_map = {
            HexResource.BRICK: "brick.png",
            HexResource.LUMBER: "lumber.png",
            HexResource.WOOL: "wool.png",
            HexResource.GRAIN: "grain.png",
            HexResource.ORE: "ore.png",
            HexResource.DESERT: "desert.png",
        }

        icons = {}

        for resource, filename in file_map.items():
            path = os.path.join(pictures_dir, filename)

            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.smoothscale(image, (34, 34))
            icons[resource] = image

        return icons

    def open_modal(self, modal_type, **data):
        self.active_modal = modal_type
        self.modal_data = dict(data)

    def close_modal(self):
        self.active_modal = None
        self.modal_data = {}

    def port_label(self, port_type):
        if port_type == PortType.THREE_TO_ONE:
            return "3:1"
        if port_type == PortType.BRICK:
            return "2:1 B"
        if port_type == PortType.LUMBER:
            return "2:1 D"
        if port_type == PortType.WOOL:
            return "2:1 W"
        if port_type == PortType.GRAIN:
            return "2:1 Z"
        if port_type == PortType.ORE:
            return "2:1 R"
        return "?"

    def has_action_type(self, state, action_type):
        return any(a.type == action_type for a in state.legal_actions())

    def resource_short_name(self, resource):
        return {
            HexResource.BRICK: "B",
            HexResource.LUMBER: "L",
            HexResource.WOOL: "W",
            HexResource.GRAIN: "G",
            HexResource.ORE: "O",
        }[resource]

    def count_dev_cards(self, state, player_id, card_type_name: str) -> int:
        player = state.players[player_id]

        old_count = sum(
            1 for card in player.development_cards
            if card.value == card_type_name
        )
        new_count = sum(
            1 for card in player.new_development_cards
            if card.value == card_type_name
        )

        return old_count + new_count

    def button_at_pos(self, mouse_pos):
        if self.active_modal is not None:
            if self.modal_confirm_rect.collidepoint(mouse_pos):
                return "modal_confirm"
            if self.current_modal_close_rect().collidepoint(mouse_pos):
                return "modal_close"
            return None
        if self.info_button_rect.collidepoint(mouse_pos):
            return "info"        
        if self.roll_button_rect.collidepoint(mouse_pos):
            return "roll"
        if self.end_turn_button_rect.collidepoint(mouse_pos):
            return "end_turn"
        if self.trade_execute_rect.collidepoint(mouse_pos):
            return "trade"
        if self.play_knight_card_rect.collidepoint(mouse_pos):
            return "play_knight"
        if self.buy_dev_card_rect.collidepoint(mouse_pos):
            return "buy_dev"
        if self.play_road_building_rect.collidepoint(mouse_pos):
            return "play_road_building"
        if self.play_year_of_plenty_rect.collidepoint(mouse_pos):
            return "play_year_of_plenty"
        if self.play_monopoly_rect.collidepoint(mouse_pos):
            return "play_monopoly"
        return None

    def legal_targets(self, state, action_type):
        result = []
        for action in state.legal_actions():
            if action.type == action_type:
                result.append(action.target)
        return result
    
    def begin_ui_press(self, mouse_pos):
        self.pressed_button = self.button_at_pos(mouse_pos)
        return self.pressed_button is not None

    def end_ui_press(self, state, mouse_pos):
        released_on = self.button_at_pos(mouse_pos)
        pressed = self.pressed_button
        self.pressed_button = None

        if pressed is None or released_on != pressed:
            return None

        if pressed == "info":
            self.help_tab = "ui"
            self.open_modal("help")
            return state

        if pressed == "roll":
            if self.has_action_type(state, ActionType.ROLL_DICE):
                return state.apply(Action(ActionType.ROLL_DICE))
            return state

        if pressed == "buy_dev":
            if self.has_action_type(state, ActionType.BUY_DEVELOPMENT_CARD):
                return state.apply(Action(ActionType.BUY_DEVELOPMENT_CARD))
            return state

        if pressed == "play_knight":
            if self.has_action_type(state, ActionType.PLAY_KNIGHT):
                return state.apply(Action(ActionType.PLAY_KNIGHT))
            return state

        if pressed == "end_turn":
            if self.has_action_type(state, ActionType.END_TURN):
                return state.apply(Action(ActionType.END_TURN))
            return state

        if pressed == "play_road_building":
            if self.has_action_type(state, ActionType.PLAY_ROAD_BUILDING):
                return state.apply(Action(ActionType.PLAY_ROAD_BUILDING))
            return state

        if pressed == "play_year_of_plenty":
            if self.has_action_type(state, ActionType.PLAY_YEAR_OF_PLENTY):
                self.pending_card_action = "year_of_plenty"
                self.open_modal(
                    "choose_two_resources",
                    selected_resource_1=None,
                    selected_resource_2=None,
                )
            return state

        if pressed == "play_monopoly":
            if self.has_action_type(state, ActionType.PLAY_MONOPOLY):
                self.pending_card_action = "monopoly"
                self.open_modal("choose_one_resource", selected_resource=None)
            return state

        if pressed == "trade":
            if (
                self.selected_give_resource is not None
                and self.selected_get_resource is not None
                and self.selected_give_resource != self.selected_get_resource
            ):
                action = Action(
                    ActionType.TRADE_BANK,
                    resource_give=self.selected_give_resource,
                    resource_get=self.selected_get_resource,
                )

                if action in state.legal_actions():
                    return state.apply(action)

            return state

        return None

    def update_hover(self, mouse_pos):
        self.hovered_button = self.button_at_pos(mouse_pos)

    def get_clicked_hex(self, state, mouse_pos, radius=55):
        mx, my = mouse_pos

        for hex_id, center in enumerate(state.board.hex_centers):
            sx, sy = self.world_to_screen(center)
            dist_sq = (sx - mx) ** 2 + (sy - my) ** 2

            if dist_sq <= radius ** 2:
                return hex_id

        return None

    def get_clicked_vertex(self, state, mouse_pos, radius=18):
        mx, my = mouse_pos

        for vertex_id, pos in enumerate(state.board.vertex_positions):
            sx, sy = self.world_to_screen(pos)
            dist_sq = (sx - mx) ** 2 + (sy - my) ** 2

            if dist_sq <= radius ** 2:
                return vertex_id

        return None

    def point_line_distance(self, p, a, b):
        # odległość punktu p od odcinka ab
        px, py = p
        ax, ay = a
        bx, by = b

        dx = bx - ax
        dy = by - ay

        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)

        t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))

        proj_x = ax + t * dx
        proj_y = ay + t * dy

        return math.hypot(px - proj_x, py - proj_y)


    def get_clicked_edge(self, state, mouse_pos, threshold=14):
        mx, my = mouse_pos

        for edge_id, (a, b) in enumerate(state.board.edges):
            pa = self.world_to_screen(state.board.vertex_positions[a])
            pb = self.world_to_screen(state.board.vertex_positions[b])

            dist = self.point_line_distance((mx, my), pa, pb)

            if dist <= threshold:
                return edge_id

        return None
    
    def get_status_text(self, state):
        if state.is_terminal():
            p0 = state.victory_points(0)
            p1 = state.victory_points(1)

            if p0 > p1:
                return "Koniec gry - Gracz 0 Wygrywa"
            elif p1 > p0:
                return "Koniec gry - Gracz 1 Wygrywa"
            else:
                return "Koniec gry - Remis"

        if state.current_player == 1:
            return "AI Myśli..." 

        # gracz
        if state.phase in ("ROBBER", "ROBBER_FROM_KNIGHT"):
            return "Przesuń złodzieja"

        if not state.dice_rolled:
            return "Rzuć kośćmi"

        return "Akcja lub koniec tury"

    def handle_modal_click(self, mouse_pos):
        if self.active_modal is None:
            return None

        if self.active_modal == "help":
            if self.help_tab_ui_rect.collidepoint(mouse_pos):
                self.help_tab = "ui"
                return "updated"

            if self.help_tab_rules_rect.collidepoint(mouse_pos):
                self.help_tab = "rules"
                return "updated"
            
        close_rect = self.current_modal_close_rect()

        if close_rect.collidepoint(mouse_pos):
            self.close_modal()
            return "closed"

        if self.active_modal == "help":
            if self.help_tab_ui_rect.collidepoint(mouse_pos):
                self.help_tab = "ui"
                self.help_page = 0
                return "updated"

            if self.help_tab_rules_rect.collidepoint(mouse_pos):
                self.help_tab = "rules"
                self.help_page = 0
                return "updated"

            if self.help_prev_rect.collidepoint(mouse_pos):
                self.help_page = max(0, self.help_page - 1)
                return "updated"

            if self.help_next_rect.collidepoint(mouse_pos):
                self.help_page = min(1, self.help_page + 1)
                return "updated"

        if self.modal_confirm_rect.collidepoint(mouse_pos):
            if self.active_modal == "choose_one_resource":
                if self.modal_data.get("selected_resource") is not None:
                    return {
                        "type": "confirmed_one_resource",
                        "resource": self.modal_data["selected_resource"],
                    }

            elif self.active_modal == "choose_two_resources":
                r1 = self.modal_data.get("selected_resource_1")
                r2 = self.modal_data.get("selected_resource_2")
                if r1 is not None and r2 is not None:
                    return {
                        "type": "confirmed_two_resources",
                        "resources": [r1, r2],
                    }

        for resource, rect in self.modal_resource_rects_row1.items():
            if rect.collidepoint(mouse_pos):
                if self.active_modal == "choose_one_resource":
                    self.modal_data["selected_resource"] = resource
                    return "updated"

                elif self.active_modal == "choose_two_resources":
                    self.modal_data["selected_resource_1"] = resource
                    return "updated"

        for resource, rect in self.modal_resource_rects_row2.items():
            if rect.collidepoint(mouse_pos):
                if self.active_modal == "choose_two_resources":
                    self.modal_data["selected_resource_2"] = resource
                    return "updated"

        return "modal_open"

    def handle_click(self, state, mouse_pos):
        print("handle_click called")

        if self.active_modal is not None:
            return state

        # 1. Obsługa złodzieja: klik w hex
        if state.phase in ("ROBBER", "ROBBER_FROM_KNIGHT"):
            hex_id = self.get_clicked_hex(state, mouse_pos)
            if hex_id is not None:
                print("Clicked hex:", hex_id)

                action = Action(ActionType.MOVE_ROBBER, hex_id)
                if action in state.legal_actions():
                    print("MOVE_ROBBER applied")
                    return state.apply(action)

            return state

        # 2. Normalne budowanie
        vertex = self.get_clicked_vertex(state, mouse_pos)
        if vertex is not None:
            print("Clicked vertex:", vertex)

            action = Action(ActionType.BUILD_CITY, vertex)
            if action in state.legal_actions():
                print("BUILD_CITY applied")
                return state.apply(action)

            action = Action(ActionType.BUILD_SETTLEMENT, vertex)
            if action in state.legal_actions():
                print("BUILD_SETTLEMENT applied")
                return state.apply(action)

        edge = self.get_clicked_edge(state, mouse_pos)
        if edge is not None:
            print("Clicked edge:", edge)

            action = Action(ActionType.BUILD_ROAD, edge)
            if action in state.legal_actions():
                print("BUILD_ROAD applied")
                return state.apply(action)

        return state
    
    def handle_trade_selection_click(self, state, mouse_pos):
        for resource, rect in self.trade_give_rects.items():
            if rect.collidepoint(mouse_pos):
                self.selected_give_resource = resource
                return state

        for resource, rect in self.trade_get_rects.items():
            if rect.collidepoint(mouse_pos):
                self.selected_get_resource = resource
                return state

        return None

    def is_button_pressed(self, name):
        now = pygame.time.get_ticks()
        return self.button_pressed_until.get(name, 0) > now


    def world_to_screen(self, point, scale=85, offset_x=700, offset_y=380):
        x, y = point
        sx = int(offset_x + x * scale)
        sy = int(offset_y + y * scale)
        return sx, sy

    def hex_polygon(self, center, size_px=70):
        cx, cy = center
        points = []
        for i in range(6):
            angle_deg = -90 + i * 60
            angle_rad = math.radians(angle_deg)
            px = cx + size_px * math.cos(angle_rad)
            py = cy + size_px * math.sin(angle_rad)
            points.append((int(px), int(py)))
        return points



    def draw_resource_icon(self, center, resource):
        icon = self.resource_icons.get(resource)
        if icon is None:
            return

        rect = icon.get_rect(center=(center[0], center[1] - 34))
        self.screen.blit(icon, rect)

    def draw_icon_cost_row(self, rect, left_icon, costs):
        """
        left_icon: nazwa z ui_icons albo HexResource
        costs: lista tuple (HexResource, amount)
        """
        x = rect.x + 12
        y = rect.y + 6

        # lewa ikona (co budujemy)
        if isinstance(left_icon, HexResource):
            icon = self.resource_icons.get(left_icon)
        else:
            icon = self.ui_icons.get(left_icon)

        if icon is not None:
            self.screen.blit(icon, icon.get_rect(topleft=(x, y)))

        x += 40

        eq = self.font_small.render("=", True, TEXT_COLOR)
        self.screen.blit(eq, (x, y + 6))
        x += 24

        for idx, (resource, amount) in enumerate(costs):
            icon = self.resource_icons.get(resource)
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(topleft=(x, y)))

            txt = self.font_small.render(str(amount), True, TEXT_COLOR)
            self.screen.blit(txt, (x + 36, y + 6))
            x += 62

            if idx < len(costs) - 1:
                plus = self.font_small.render("+", True, TEXT_COLOR)
                self.screen.blit(plus, (x - 10, y + 6))

    def draw_modal(self):
        if self.active_modal is None:
            return

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        self.screen.blit(overlay, (0, 0))

        modal_rect = self.current_modal_rect()
        close_rect = self.current_modal_close_rect()

        self.draw_panel(modal_rect)

        pygame.draw.rect(self.screen, BUTTON_BG, close_rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, close_rect, 2, border_radius=8)
        close_txt = self.font_small.render("X", True, TEXT_COLOR)
        close_txt_rect = close_txt.get_rect(center=close_rect.center)
        self.screen.blit(close_txt, close_txt_rect)

        if self.active_modal == "choose_one_resource":
            self.draw_choose_one_resource_modal()

        elif self.active_modal == "choose_two_resources":
            self.draw_choose_two_resources_modal()

        elif self.active_modal == "help":
            self.draw_help_modal()

    def draw_help_modal(self):
        modal_rect = self.help_modal_rect

        title = self.font_large.render("Pomoc", True, TEXT_COLOR)
        self.screen.blit(title, (modal_rect.x + 25, modal_rect.y + 20))

        self.draw_tab(self.help_tab_ui_rect, "Interfejs", self.help_tab == "ui")
        self.draw_tab(self.help_tab_rules_rect, "Zasady", self.help_tab == "rules")

        # nawigacja stron
        pygame.draw.rect(self.screen, BUTTON_BG, self.help_prev_rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, self.help_prev_rect, 2, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BG, self.help_next_rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, self.help_next_rect, 2, border_radius=8)

        prev_txt = self.font_medium.render("←", True, TEXT_COLOR)
        next_txt = self.font_medium.render("→", True, TEXT_COLOR)
        self.screen.blit(prev_txt, prev_txt.get_rect(center=self.help_prev_rect.center))
        self.screen.blit(next_txt, next_txt.get_rect(center=self.help_next_rect.center))

        page_txt = self.font_small.render(f"Strona {self.help_page + 1}/2", True, TEXT_COLOR)
        self.screen.blit(page_txt, (modal_rect.x + 860, modal_rect.y + 155))

        if self.help_tab == "ui":
            if self.help_page == 0:
                self.draw_help_ui_page_1()
            else:
                self.draw_help_ui_page_2()
        else:
            if self.help_page == 0:
                self.draw_help_rules_page_1()
            else:
                self.draw_help_rules_page_2()

    def draw_tab(self, rect, text, active):
        color = PANEL_BG if active else BUTTON_BG

        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, rect, 2, border_radius=8)

        txt = self.font_small.render(text, True, TEXT_COLOR)
        txt_rect = txt.get_rect(center=rect.center)
        self.screen.blit(txt, txt_rect)

    def draw_help_ui_page_1(self):
        modal_rect = self.help_modal_rect

        guide_rect = pygame.Rect(modal_rect.x + 30, modal_rect.y + 210, 980, 470)
        pygame.draw.rect(self.screen, (245, 242, 230), guide_rect, border_radius=12)
        pygame.draw.rect(self.screen, PANEL_BORDER, guide_rect, 2, border_radius=12)

        boxes = [
            (pygame.Rect(guide_rect.x + 710, guide_rect.y + 20, 230, 80), "Status gry",
             ["Pokazuje fazę gry,", "aktywną turę i możliwe ruchy"]),
            (pygame.Rect(guide_rect.x + 710, guide_rect.y + 150, 230, 100), "Koszty",
             ["Ściągawka kosztów", "budowy dróg, osad,", "miast i kart rozwoju."]),
            (pygame.Rect(guide_rect.x + 710, guide_rect.y + 260, 230, 90), "Przyciski tury",
             ["Rzut kośćmi,", "zakup karty rozwoju", "i zakończenie tury."]),
            (pygame.Rect(guide_rect.x + 510, guide_rect.y + 290, 175, 170), "Karty do zagrania",
             ["Tutaj zagrywasz", "rycerza, monopol,", "wynalazek i budowę dróg."]),
            (pygame.Rect(guide_rect.x + 710, guide_rect.y + 365, 230, 95), "Handel",
             ["Wybierz co oddajesz", "i co otrzymujesz", "z banku lub portu."]),
            (pygame.Rect(guide_rect.x + 240, guide_rect.y + 380, 230, 60), "Ekwipunek",
             ["Aktualne zasoby gracza."]),
            (pygame.Rect(guide_rect.x + 20, guide_rect.y + 330, 200, 120), "Panel gracza",
             ["Punkty zwycięstwa,", "budowle, rycerze", "i bonusy specjalne."]),
             (pygame.Rect(guide_rect.x + 20, guide_rect.y + 20, 200, 120), "Panel przeciwnika",
             ["Punkty zwycięstwa,", "budowle, rycerze", "i bonusy specjalne."]),
        ]

        for rect, title, lines in boxes:
            pygame.draw.rect(self.screen, (230, 226, 210), rect, border_radius=10)
            pygame.draw.rect(self.screen, PANEL_BORDER, rect, 2, border_radius=10)

            title_txt = self.font_small.render(title, True, TEXT_COLOR)
            self.screen.blit(title_txt, (rect.x + 10, rect.y + 8))

            y = rect.y + 32
            for line in lines:
                txt = self.font_small.render(line, True, TEXT_COLOR)
                self.screen.blit(txt, (rect.x + 10, y))
                y += 18

    def draw_help_ui_page_2(self):
        modal_rect = self.help_modal_rect

        title = self.font_medium.render("Kolory, ikony i kliknięcia", True, TEXT_COLOR)
        self.screen.blit(title, (modal_rect.x + 30, modal_rect.y + 220))

        lines = [
            "Kolorowe linie oznaczają drogi graczy.",
            "Kolorowe kółka oznaczają osady.",
            "Kolorowe kwadraty oznaczają miasta.",
            "Żółte podświetlenie pokazuje legalne miejsca budowy lub ruch złodzieja.",
            "Czarne kółko oznacza pozycje złodzieja.",
            "",
            "Jak budować:",
            "- aby wybudować drogę, kliknij podświetloną krawędź",
            "- aby wybudować osadę, kliknij podświetlony wierzchołek",
            "- aby ulepszyć osadę do miasta, kliknij własną podświetloną osadę",
            "- aby przesunąć złodzieja, kliknij podświetlony heks",
            "",
            "Porty:",
            "- znacznik 3:1 oznacza port ogólny",
            "- znacznik 2:1 z ikoną zasobu oznacza port specjalny",
        ]

        y = modal_rect.y + 270
        for line in lines:
            txt = self.font_small.render(line, True, TEXT_COLOR)
            self.screen.blit(txt, (modal_rect.x + 30, y))
            y += 24

        legend_items = [
            ("settlement", "Osada"),
            ("city", "Miasto"),
            ("road", "Droga"),
            ("knight", "Rycerz"),
            ("nwr", "Najwyższa władza rycerska"),
            ("ndh", "Najdłuższa droga handlowa"),
            ("card", "Karta rozwoju"),
        ]

        x = modal_rect.x + 620
        y = modal_rect.y + 260
        for icon_name, label in legend_items:
            icon = self.ui_icons.get(icon_name)
            if icon:
                self.screen.blit(icon, icon.get_rect(topleft=(x, y)))
            txt = self.font_small.render(label, True, TEXT_COLOR)
            self.screen.blit(txt, (x + 40, y + 5))
            y += 42

    def draw_help_rules_page_1(self):
        modal_rect = self.help_modal_rect

        lines = [
            "Cel gry",
            "Zdobądź 10 punktów zwycięstwa szybciej niż przeciwnik.",
            "",
            "Punkty zwycięstwa",
            "- osada = 1",
            "- miasto = 2",
            "- najdłuższa droga handlowa = 2",
            "- najwyższa władza rycerska = 2",
            "- karta Punkt Zwycięstwa = 1",
            "",
            "Przebieg tury",
            "1. Rzuć kośćmi.",
            "2. Odbierz surowce z odpowiednich pól.",
            "3. Buduj, handluj i zagrywaj karty.",
            "4. Zakończ turę.",
            "",
            "Produkcja",
            "Każda budowla przy polu z wylosowanym numerem produkuje surowce.",
            "Osada daje 1 surowiec, miasto daje 2 surowce.",
            "Pole zablokowane przez złodzieja nie produkuje.",
        ]

        self.draw_help_text_block(lines, start_x=modal_rect.x + 30, start_y=modal_rect.y + 220)

        # ikonki po prawej
        icon_x = modal_rect.x + 700
        icon_y = modal_rect.y + 230
        items = [
            ("settlement", "1 punkt"),
            ("city", "2 punkty"),
            ("ndh", "bonus +2"),
            ("nwr", "bonus +2"),
            ("card", "PZ = 1"),
        ]

        for icon_name, label in items:
            icon = self.ui_icons.get(icon_name)
            if icon:
                self.screen.blit(icon, icon.get_rect(topleft=(icon_x, icon_y)))
            txt = self.font_small.render(label, True, TEXT_COLOR)
            self.screen.blit(txt, (icon_x + 40, icon_y + 5))
            icon_y += 45


    def draw_help_rules_page_2(self):
        modal_rect = self.help_modal_rect

        lines = [
            "Złodziej",
            "Przy rzucie 7 lub po zagraniu rycerza przesuwasz złodzieja.",
            "Pole ze złodziejem nie produkuje surowców,",
            "a ty zabierasz 1 losowy surowiec od przeciwnika, jeśli ma budowlę przy tym polu.",
            "",
            "Budowa",
            "- droga = cegła + drewno",
            "- osada = cegła + drewno + wełna + zboże",
            "- miasto = 2 zboże + 3 ruda",
            "- karta rozwoju = wełna + zboże + ruda",
            "",
            "Handel",
            "Bank: 4:1 - oddajesz 4 surowce jednego rodzaju, dostajesz 1 dowolny surowiec.",
            "Port ogólny: 3:1 - oddajesz 3 surowce jednego rodzaju, dostajesz 1 dowolny surowiec.",
            "Port specjalny: 2:1 dla wskazanego surowca - oddajesz 2 surowce tego rodzaju, dostajesz 1 dowolny surowiec.",
            "",
            "Karty rozwoju",
            "- Rycerz: przesuwa złodzieja",
            "- Budowa dróg: budujesz 2 darmowe drogi",
            "- Wynalazek: bierzesz 2 dowolne surowce",
            "- Monopol: przejmujesz od innych cały zapas wybranego surowca",
            "- Punkt Zwycięstwa: daje 1 punkt zwycięstwa",
        ]

        self.draw_help_text_block(lines, start_x=modal_rect.x + 30, start_y=modal_rect.y + 220)

        icon_x = modal_rect.x + 700
        icon_y = modal_rect.y + 230
        resource_items = [
            (HexResource.BRICK, "cegła"),
            (HexResource.LUMBER, "drewno"),
            (HexResource.WOOL, "wełna"),
            (HexResource.GRAIN, "zboże"),
            (HexResource.ORE, "ruda"),
        ]

        for resource, label in resource_items:
            icon = self.resource_icons.get(resource)
            if icon:
                self.screen.blit(icon, icon.get_rect(topleft=(icon_x, icon_y)))
            txt = self.font_small.render(label, True, TEXT_COLOR)
            self.screen.blit(txt, (icon_x + 40, icon_y + 5))
            icon_y += 45

    def draw_help_text_block(self, lines, start_x, start_y):
        y = start_y

        headers = {
            "Cel gry",
            "Punkty zwycięstwa",
            "Przebieg tury",
            "Produkcja",
            "Złodziej",
            "Budowa",
            "Handel",
            "Karty rozwoju",
        }

        for line in lines:
            if line == "":
                y += 10
                continue

            if line in headers:
                txt = self.font_medium.render(line, True, TEXT_COLOR)
                self.screen.blit(txt, (start_x, y))
                y += 28
            else:
                txt = self.font_small.render(line, True, TEXT_COLOR)
                self.screen.blit(txt, (start_x, y))
                y += 22

    def draw_help_callout(self, box_pos, target_pos, title, body):
        bx, by = box_pos
        tx, ty = target_pos

        bubble_rect = pygame.Rect(bx, by, 140, 58)
        pygame.draw.rect(self.screen, (255, 248, 240), bubble_rect, border_radius=10)
        pygame.draw.rect(self.screen, (180, 60, 60), bubble_rect, 2, border_radius=10)

        pygame.draw.line(self.screen, (200, 40, 40), (bubble_rect.right, bubble_rect.centery), (tx, ty), 3)

        title_txt = self.font_small.render(title, True, (160, 20, 20))
        self.screen.blit(title_txt, (bubble_rect.x + 8, bubble_rect.y + 6))

        lines = body.split("\n")
        y = bubble_rect.y + 26
        for line in lines[:2]:
            txt = self.font_small.render(line, True, TEXT_COLOR)
            self.screen.blit(txt, (bubble_rect.x + 8, y))
            y += 16

    def draw_help_rules(self):
        lines = [
            "Cel gry",
            "Zdobądź 10 punktów zwycięstwa szybciej niż przeciwnik.",
            "",
            "Jak zdobywa się punkty",
            "- osada = 1 punkt",
            "- miasto = 2 punkty",
            "- najdłuższa droga handlowa = 2 punkty",
            "- najwyższa władza rycerska = 2 punkty",
            "- karta Punkt Zwycięstwa = 1 punkt",
            "",
            "Przebieg tury",
            "1. Rzuć kośćmi.",
            "2. Odbierz surowce z pól z wylosowanym numerem.",
            "3. Buduj, handluj i zagrywaj karty rozwoju.",
            "4. Zakończ turę.",
            "",
            "Produkcja surowców",
            "Jeśli numer pola zgadza się z wynikiem rzutu, budowle przy tym polu produkują:",
            "- osada = 1 surowiec",
            "- miasto = 2 surowce",
            "Pole zablokowane przez złodzieja nie produkuje.",
            "",
            "Złodziej",
            "Przy rzucie 7 albo po zagraniu rycerza przesuwasz złodzieja na wybrane pole.",
            "Pole z złodziejem nie produkuje. Jeśli na polu stoi przeciwnik, kradniesz 1 losowy surowiec.",
            "",
            "Budowa",
            "- droga: cegła + drewno",
            "- osada: cegła + drewno + wełna + zboże",
            "- miasto: 2 zboże + 3 ruda",
            "- karta rozwoju: wełna + zboże + ruda",
            "",
            "Handel",
            "Standardowo bank handluje 4:1.",
            "Port ogólny daje kurs 3:1.",
            "Port specjalny daje kurs 2:1 dla danego surowca.",
            "",
            "Karty rozwoju",
            "- Rycerz: przesuwa złodzieja",
            "- Budowa dróg: budujesz 2 darmowe drogi",
            "- Wynalazek: bierzesz 2 dowolne surowce z banku",
            "- Monopol: wybierasz surowiec, inni gracze oddają Ci cały jego zapas",
            "- Punkt Zwycięstwa: daje ukryty punkt zwycięstwa",
        ]

        self.draw_help_text_block(lines)

    def draw_help_text_block(self, lines, start_x, start_y):
        y = start_y

        headers = {
            "Cel gry",
            "Punkty zwycięstwa",
            "Przebieg tury",
            "Produkcja",
            "Produkcja surowców",
            "Złodziej",
            "Budowa",
            "Handel",
            "Karty rozwoju",
            "Jak zdobywa się punkty",
        }

        for line in lines:
            if line == "":
                y += 10
                continue

            if line in headers:
                txt = self.font_medium.render(line, True, TEXT_COLOR)
                self.screen.blit(txt, (start_x, y))
                y += 28
            else:
                txt = self.font_small.render(line, True, TEXT_COLOR)
                self.screen.blit(txt, (start_x, y))
                y += 22

    def draw_help_text(self, lines, start_x, start_y):
        y = start_y

        for line in lines:
            txt = self.font_small.render(line, True, TEXT_COLOR)
            self.screen.blit(txt, (start_x, y))
            y += 22

    def draw_choose_one_resource_modal(self):
        modal_rect = self.card_modal_rect
        title = self.font_medium.render("Wybierz surowiec", True, TEXT_COLOR)
        self.screen.blit(title, (modal_rect.x + 20, modal_rect.y + 20))

        subtitle = self.font_small.render("Kliknij jeden surowiec.", True, TEXT_COLOR)
        self.screen.blit(subtitle, (modal_rect.x + 20, modal_rect.y + 60))

        selected = self.modal_data.get("selected_resource")

        for resource, rect in self.modal_resource_rects_row1.items():
            self.draw_resource_button(
                rect,
                resource,
                selected=(selected == resource),
                enabled=True,
            )

        confirm_enabled = selected is not None

        self.draw_primary_button(
            self.modal_confirm_rect,
            "Potwierdź",
            enabled=confirm_enabled,
            hovered=(self.hovered_button == "modal_confirm"),
            pressed=(self.pressed_button == "modal_confirm"),
        )

    def draw_choose_two_resources_modal(self):
        modal_rect = self.card_modal_rect
        title = self.font_medium.render("Wybierz 2 surowce", True, TEXT_COLOR)
        self.screen.blit(title, (modal_rect.x + 20, modal_rect.y + 20))

        selected_1 = self.modal_data.get("selected_resource_1")
        selected_2 = self.modal_data.get("selected_resource_2")

        subtitle1 = self.font_small.render("Wybór 1:", True, TEXT_COLOR)
        self.screen.blit(subtitle1, (modal_rect.x + 20, modal_rect.y + 95))

        subtitle2 = self.font_small.render("Wybór 2:", True, TEXT_COLOR)
        self.screen.blit(subtitle2, (modal_rect.x + 20, modal_rect.y + 165))

        for resource, rect in self.modal_resource_rects_row1.items():
            self.draw_resource_button(
                rect,
                resource,
                selected=(selected_1 == resource),
                enabled=True,
            )

        for resource, rect in self.modal_resource_rects_row2.items():
            self.draw_resource_button(
                rect,
                resource,
                selected=(selected_2 == resource),
                enabled=True,
            )

        confirm_enabled = (selected_1 is not None and selected_2 is not None)

        self.draw_primary_button(
            self.modal_confirm_rect,
            "Potwierdź",
            enabled=confirm_enabled,
            hovered=(self.hovered_button == "modal_confirm"),
            pressed=(self.pressed_button == "modal_confirm"),
        )

    def draw_play_cards_panel(self, state):
        rect = self.play_cards_panel_rect
        self.draw_panel(rect, "Karty do zagrania")

        human_player_id = 0

        knight = self.count_dev_cards(state, human_player_id, "knight")
        road = self.count_dev_cards(state, human_player_id, "road_building")
        plenty = self.count_dev_cards(state, human_player_id, "year_of_plenty")
        monopoly = self.count_dev_cards(state, human_player_id, "monopoly")
        vp = self.count_dev_cards(state, human_player_id, "victory_point")

        is_my_turn = state.current_player == human_player_id
        legal = state.legal_actions()

        def has(type_):
            return any(a.type == type_ for a in legal)

        self.draw_button(self.play_knight_card_rect,
            f"Rycerz x{knight}",
            enabled=is_my_turn and has(ActionType.PLAY_KNIGHT) and knight > 0,
            hovered=(self.hovered_button == "play_knight"),
            pressed=(self.pressed_button == "play_knight"),
        )

        self.draw_button(self.play_road_building_rect,
            f"Budowa dróg x{road}",
            enabled=is_my_turn and has(ActionType.PLAY_ROAD_BUILDING) and road > 0,
            hovered=(self.hovered_button == "play_road_building"),
            pressed=(self.pressed_button == "play_road_building"),
        )

        self.draw_button(self.play_year_of_plenty_rect,
            f"Wynalazek x{plenty}",
            enabled=is_my_turn and has(ActionType.PLAY_YEAR_OF_PLENTY) and plenty > 0,
            hovered=(self.hovered_button == "play_year_of_plenty"),
            pressed=(self.pressed_button == "play_year_of_plenty"),
        )

        self.draw_button(self.play_monopoly_rect,
            f"Monopol x{monopoly}",
            enabled=is_my_turn and has(ActionType.PLAY_MONOPOLY) and monopoly > 0,
            hovered=(self.hovered_button == "play_monopoly"),
            pressed=(self.pressed_button == "play_monopoly"),
        )

        self.draw_button(self.vp_card_rect,
            f"PZ x{vp}",
            enabled=False,
            hovered=False,
            pressed=False,
        )

    def draw_port_badge(self, center, port_type):
        cx, cy = center

        # mniejsze koło
        radius = 18
        pygame.draw.circle(self.screen, (240, 234, 214), (cx, cy), radius)
        pygame.draw.circle(self.screen, (80, 80, 80), (cx, cy), radius, 2)

        # bold font dla liczb
        bold_font = pygame.font.SysFont("arial", 15, bold=True)

        if port_type == PortType.THREE_TO_ONE:
            txt = bold_font.render("3:1", True, TEXT_COLOR)
            txt_rect = txt.get_rect(center=(cx, cy))
            self.screen.blit(txt, txt_rect)
            return

        resource_map = {
            PortType.BRICK: HexResource.BRICK,
            PortType.LUMBER: HexResource.LUMBER,
            PortType.WOOL: HexResource.WOOL,
            PortType.GRAIN: HexResource.GRAIN,
            PortType.ORE: HexResource.ORE,
        }

        resource = resource_map.get(port_type)
        if resource is None:
            txt = bold_font.render("?", True, TEXT_COLOR)
            txt_rect = txt.get_rect(center=(cx, cy))
            self.screen.blit(txt, txt_rect)
            return

        icon = self.resource_icons.get(resource)
        if icon is not None:
            # mniejsza ikona
            small_icon = pygame.transform.smoothscale(icon, (16, 16))
            # troszkę wyżej
            icon_rect = small_icon.get_rect(center=(cx, cy - 6))
            self.screen.blit(small_icon, icon_rect)

        txt = bold_font.render("2:1", True, TEXT_COLOR)
        txt_rect = txt.get_rect(center=(cx, cy + 8))
        self.screen.blit(txt, txt_rect)

    def draw_icon_with_count(self, icon_name, x, y, count):
        icon = self.ui_icons.get(icon_name)
        if icon is not None:
            self.screen.blit(icon, icon.get_rect(topleft=(x, y)))

        amount_txt = self.font_small.render(str(count), True, TEXT_COLOR)
        self.screen.blit(amount_txt, (x + 34, y + 2))

    def draw_ports(self, state):
        board_center_x = 620
        board_center_y = 380

        for (v1, v2), port_type in state.board.ports:
            p1 = self.world_to_screen(state.board.vertex_positions[v1])
            p2 = self.world_to_screen(state.board.vertex_positions[v2])

            # środek krawędzi
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2

            # wektor krawędzi
            ex = p2[0] - p1[0]
            ey = p2[1] - p1[1]

            # wektor prostopadły
            nx = -ey
            ny = ex

            length = (nx * nx + ny * ny) ** 0.5
            if length == 0:
                continue

            nx /= length
            ny /= length

            # wybierz stronę "na zewnątrz" planszy
            test1x = mx + nx * 18
            test1y = my + ny * 18
            test2x = mx - nx * 18
            test2y = my - ny * 18

            d1 = (test1x - board_center_x) ** 2 + (test1y - board_center_y) ** 2
            d2 = (test2x - board_center_x) ** 2 + (test2y - board_center_y) ** 2

            if d2 > d1:
                nx = -nx
                ny = -ny

            radius = 18
            bx = int(mx + nx * radius)
            by = int(my + ny * radius)

            self.draw_port_badge((bx, by), port_type)

    def draw_info_button(self):
        pygame.draw.rect(self.screen, BUTTON_BG, self.info_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, BUTTON_BORDER, self.info_button_rect, 2, border_radius=10)

        txt = self.font_medium.render("i", True, TEXT_COLOR)
        rect = txt.get_rect(center=self.info_button_rect.center)
        self.screen.blit(txt, rect)

    def draw_trade_panel(self, state):
        rect = pygame.Rect(1030, 820, 330, 220)
        self.draw_panel(rect, "Handel z bankiem")

        if self.selected_give_resource is not None:
            ratio = rules.get_player_trade_ratio(state, state.current_player, self.selected_give_resource)
            ratio_txt = self.font_small.render(f"Aktualny kurs: {ratio}:1", True, TEXT_COLOR)
            self.screen.blit(ratio_txt, (rect.x + 14, rect.y + 28))

        give_label = self.font_small.render("Oddaj :", True, TEXT_COLOR)
        self.screen.blit(give_label, (rect.x + 14, rect.y + 55))

        take_label = self.font_small.render("  Weź :", True, TEXT_COLOR)
        self.screen.blit(take_label, (rect.x + 14, rect.y + 110))

        current_player = state.players[state.current_player]

        for resource, button_rect in self.trade_give_rects.items():
            selected = (self.selected_give_resource == resource)
            enabled = current_player.resources[resource] >= 4 and self.has_action_type(state, ActionType.END_TURN)

            self.draw_resource_button(
                button_rect,
                resource,
                selected=selected,
                enabled=enabled,
            )

        for resource, button_rect in self.trade_get_rects.items():
            selected = (self.selected_get_resource == resource)
            enabled = self.has_action_type(state, ActionType.END_TURN)

            self.draw_resource_button(
                button_rect,
                resource,
                selected=selected,
                enabled=enabled,
            )

        trade_enabled = False
        if self.selected_give_resource is not None and self.selected_get_resource is not None:
            if self.selected_give_resource != self.selected_get_resource:
                trade_enabled = any(
                    a.type == ActionType.TRADE_BANK
                    and a.resource_give == self.selected_give_resource
                    and a.resource_get == self.selected_get_resource
                    for a in state.legal_actions()
                )

        self.draw_primary_button(
            self.trade_execute_rect,
            "Handluj",
            enabled=trade_enabled,
            hovered=(self.hovered_button == "trade"),
            pressed=(self.pressed_button == "trade"),
        )

    def draw_placeholder_badge(self, x, y, label, value):
        badge_rect = pygame.Rect(x, y, 56, 28)
        pygame.draw.rect(self.screen, (220, 215, 195), badge_rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, badge_rect, 2, border_radius=8)

        txt = self.font_small.render(f"{label}:{value}", True, TEXT_COLOR)
        txt_rect = txt.get_rect(center=badge_rect.center)
        self.screen.blit(txt, txt_rect)

    def draw_inventory_bar(self, state):
        player = state.players[0]

        bar_rect = pygame.Rect(320, 980, 510, 60)
        self.draw_panel(bar_rect)

        items = [
            (HexResource.BRICK, player.resources[HexResource.BRICK]),
            (HexResource.ORE, player.resources[HexResource.ORE]),
            (HexResource.LUMBER, player.resources[HexResource.LUMBER]),
            (HexResource.WOOL, player.resources[HexResource.WOOL]),
            (HexResource.GRAIN, player.resources[HexResource.GRAIN]),
        ]

        x = bar_rect.x + 22
        y = bar_rect.y + 18

        for item, amount in items:
            icon = self.resource_icons.get(item)
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(topleft=(x, y - 4)))

            txt = self.font_small.render(str(amount), True, TEXT_COLOR)
            self.screen.blit(txt, (x + 40, y + 3))

            x += 104

    def draw_primary_button(self, rect, text, enabled=True, hovered=False, pressed=False):
        if not enabled:
            bg = (170, 170, 170)
        elif pressed:
            bg = (120, 180, 120)
        elif hovered:
            bg = (150, 210, 150)
        else:
            bg = (135, 195, 135)

        draw_rect = rect.copy()
        shadow_rect = rect.copy()

        if pressed and enabled:
            draw_rect.y += 3
        else:
            shadow_rect.y += 4
            pygame.draw.rect(self.screen, BUTTON_SHADOW, shadow_rect, border_radius=8)

        pygame.draw.rect(self.screen, bg, draw_rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, draw_rect, width=3, border_radius=8)

        label = self.font_small.render(text, True, BUTTON_TEXT)
        label_rect = label.get_rect(center=draw_rect.center)
        self.screen.blit(label, label_rect)

    def draw_resource_button(self, rect, resource, selected=False, enabled=True):
        base_color = HEX_COLORS[resource]

        if not enabled:
            color = (170, 170, 170)
        elif selected:
            color = tuple(min(255, c + 35) for c in base_color)
        else:
            color = base_color

        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, rect, width=3 if selected else 2, border_radius=8)

        icon = self.resource_icons.get(resource)
        if icon is not None:
            icon_rect = icon.get_rect(center=rect.center)
            self.screen.blit(icon, icon_rect)

    def draw_button(self, rect, text, enabled=True, hovered=False, pressed=False):
        if not enabled:
            bg = BUTTON_DISABLED
        elif pressed:
            bg = BUTTON_PRESSED_BG
        elif hovered:
            bg = BUTTON_HOVER_BG
        else:
            bg = BUTTON_BG

        draw_rect = rect.copy()
        shadow_rect = rect.copy()

        if pressed and enabled:
            draw_rect.y += 3
        else:
            shadow_rect.y += 4
            pygame.draw.rect(self.screen, BUTTON_SHADOW, shadow_rect, border_radius=8)

        pygame.draw.rect(self.screen, bg, draw_rect, border_radius=8)
        pygame.draw.rect(
            self.screen,
            BUTTON_BORDER,
            draw_rect,
            width=3 if hovered or pressed else 2,
            border_radius=8,
        )

        label = self.font_small.render(text, True, BUTTON_TEXT)
        label_rect = label.get_rect(center=draw_rect.center)
        self.screen.blit(label, label_rect)

    def draw_buttons(self, state):
        roll_enabled = self.has_action_type(state, ActionType.ROLL_DICE)
        end_enabled = self.has_action_type(state, ActionType.END_TURN)
        buy_dev_enabled = self.has_action_type(state, ActionType.BUY_DEVELOPMENT_CARD)

        self.draw_button(
            self.buy_dev_card_rect,
            "Kup kartę",
            enabled=buy_dev_enabled,
            hovered=(self.hovered_button == "buy_dev"),
            pressed=(self.pressed_button == "buy_dev"),
        )

        self.draw_button(
            self.roll_button_rect,
            "Rzuć Kośćmi",
            enabled=roll_enabled,
            hovered=(self.hovered_button == "roll"),
            pressed=(self.pressed_button == "roll"),
        )

        self.draw_button(
            self.end_turn_button_rect,
            "Zakończ Turę",
            enabled=end_enabled,
            hovered=(self.hovered_button == "end_turn"),
            pressed=(self.pressed_button == "end_turn"),
        )

    def draw_hexes(self, state):
        board = state.board

        for hex_id, center in enumerate(board.hex_centers):
            resource = board.hex_resources[hex_id]
            number = board.hex_numbers[hex_id]

            screen_center = self.world_to_screen(center)
            polygon = self.hex_polygon(screen_center)

            pygame.draw.polygon(self.screen, HEX_COLORS[resource], polygon)
            pygame.draw.polygon(self.screen, EDGE_COLOR, polygon, 2)

            self.draw_resource_icon(screen_center, resource)

            if number is not None:
                label = self.font_medium.render(str(number), True, TEXT_COLOR)
                rect = label.get_rect(center=screen_center)

                pygame.draw.circle(self.screen, (245, 235, 210), screen_center, 18)
                pygame.draw.circle(self.screen, EDGE_COLOR, screen_center, 18, 2)
                self.screen.blit(label, rect)

            if hex_id == state.robber_hex:
                rx, ry = screen_center
                pygame.draw.circle(self.screen, ROBBER_COLOR, (rx, ry + 28), 10)

    def draw_edges(self, state):
        board = state.board

        for edge_id, (a, b) in enumerate(board.edges):
            pa = self.world_to_screen(board.vertex_positions[a])
            pb = self.world_to_screen(board.vertex_positions[b])

            owner = None
            for player_id, player in enumerate(state.players):
                if edge_id in player.roads:
                    owner = player_id
                    break

            if owner is None:
                pygame.draw.line(self.screen, (140, 140, 140), pa, pb, 2)
            else:
                pygame.draw.line(self.screen, PLAYER_COLORS[owner], pa, pb, 6)

    def draw_vertices(self, state):
        board = state.board

        for vertex_id, pos in enumerate(board.vertex_positions):
            p = self.world_to_screen(pos)

            owner = None
            is_city = False

            for player_id, player in enumerate(state.players):
                if vertex_id in player.settlements:
                    owner = player_id
                    is_city = False
                    break
                if vertex_id in player.cities:
                    owner = player_id
                    is_city = True
                    break

            if owner is None:
                pygame.draw.circle(self.screen, VERTEX_COLOR, p, 4)
            else:
                color = PLAYER_COLORS[owner]
                if is_city:
                    rect = pygame.Rect(0, 0, 20, 20)
                    rect.center = p
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, EDGE_COLOR, rect, 2)
                else:
                    pygame.draw.circle(self.screen, color, p, 9)
                    pygame.draw.circle(self.screen, EDGE_COLOR, p, 9, 2)

    def draw_panel(self, rect, title=None):
        pygame.draw.rect(self.screen, PANEL_BG, rect, border_radius=14)
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, width=2, border_radius=14)

        if title:
            label = self.font_small.render(title, True, TEXT_COLOR)
            self.screen.blit(label, (rect.x + 14, rect.y + 10))

    def draw_status_panel(self, state):
        rect = pygame.Rect(1030, 30, 320, 130)
        self.draw_panel(rect)

        status = self.get_status_text(state)
        status_label = self.font_medium.render(status, True, TEXT_COLOR)
        self.screen.blit(status_label, (rect.x + 14, rect.y + 16))

        info_lines = [
            f"Faza: {state.phase}",
            f"Aktywny gracz: {state.current_player}",
            f"Ostatni rzut: {state.last_roll}",
        ]

        y = rect.y + 56
        for line in info_lines:
            txt = self.font_small.render(line, True, TEXT_COLOR)
            self.screen.blit(txt, (rect.x + 14, y))
            y += 22

    def draw_costs_panel(self):
        rect = pygame.Rect(1030, 470, 330, 220)
        self.draw_panel(rect, "Koszty")

        rows = [
            ("road", [(HexResource.BRICK, 1), (HexResource.LUMBER, 1)]),
            ("settlement", [(HexResource.BRICK, 1), (HexResource.LUMBER, 1), (HexResource.WOOL, 1), (HexResource.GRAIN, 1)]),
            ("city", [(HexResource.GRAIN, 2), (HexResource.ORE, 3)]),
            ("card", [(HexResource.WOOL, 1), (HexResource.GRAIN, 1), (HexResource.ORE, 1)]),
        ]

        y = rect.y + 38
        for left_icon, costs in rows:
            row_rect = pygame.Rect(rect.x + 8, y, rect.width - 16, 34)
            self.draw_icon_cost_row(row_rect, left_icon, costs)
            y += 40

    def draw_players_panel(self, state):
        # ---------- AI / Gracz 1 ----------
        ai_rect = pygame.Rect(30, 30, 250, 150)
        self.draw_panel(ai_rect, "Gracz 1")

        ai_color = PLAYER_COLORS[1]
        pygame.draw.circle(self.screen, ai_color, (ai_rect.x + 210, ai_rect.y + 20), 8)

        ai_player = state.players[1]
        ai_vp = state.victory_points(1)

        x0 = ai_rect.x + 14
        y0 = ai_rect.y + 42

        vp_txt = self.font_small.render(f"PZ: {ai_vp}", True, TEXT_COLOR)
        self.screen.blit(vp_txt, (x0, y0))

        # rząd 2: osady / miasta / drogi
        y_icons_1 = y0 + 30
        x = x0
        row1 = [
            ("settlement", len(ai_player.settlements)),
            ("city", len(ai_player.cities)),
            ("road", len(ai_player.roads)),
        ]
        for item, amount in row1:
            self.draw_icon_with_count(item, x, y_icons_1, amount)
            x += 72

        # rząd 3: rycerze / władza / droga handlowa
        y_icons_2 = y_icons_1 + 40
        x = x0
        row2 = [
            ("knight", ai_player.played_knights),
            ("nwr", 1 if state.largest_army_owner == 1 else 0),
            ("ndh", state.longest_road_length if state.longest_road_owner == 1 else 0),
        ]
        for item, amount in row2:
            self.draw_icon_with_count(item, x, y_icons_2, amount)
            x += 72

        # ---------- Człowiek / Gracz 0 ----------
        human_rect = pygame.Rect(30, 900, 250, 150)
        self.draw_panel(human_rect, "Gracz 0")

        human_color = PLAYER_COLORS[0]
        pygame.draw.circle(self.screen, human_color, (human_rect.x + 210, human_rect.y + 20), 8)

        human_player = state.players[0]
        human_vp = state.victory_points(0)

        x0 = human_rect.x + 14
        y0 = human_rect.y + 42

        vp_txt = self.font_small.render(f"PZ: {human_vp}", True, TEXT_COLOR)
        self.screen.blit(vp_txt, (x0, y0))

        # rząd 2: osady / miasta / drogi
        y_icons_1 = y0 + 30
        x = x0
        row1 = [
            ("settlement", len(human_player.settlements)),
            ("city", len(human_player.cities)),
            ("road", len(human_player.roads)),
        ]
        for item, amount in row1:
            self.draw_icon_with_count(item, x, y_icons_1, amount)
            x += 72

        # rząd 3: rycerze / władza / droga handlowa
        y_icons_2 = y_icons_1 + 40
        x = x0
        row2 = [
            ("knight", human_player.played_knights),
            ("nwr", 1 if state.largest_army_owner == 0 else 0),
            ("ndh", state.longest_road_length if state.longest_road_owner == 0 else 0),
        ]
        
        for item, amount in row2:
            self.draw_icon_with_count(item, x, y_icons_2, amount)
            x += 72

    def draw_icon_with_count(self, icon_name, x, y, count):
        icon = self.ui_icons.get(icon_name)
        if icon is not None:
            self.screen.blit(icon, icon.get_rect(topleft=(x, y)))

        amount_txt = self.font_small.render(str(count), True, TEXT_COLOR)
        self.screen.blit(amount_txt, (x + 34, y + 2))

    def draw_highlights(self, state):
        legal_actions = state.legal_actions()
        action_types = {a.type for a in legal_actions}

        # --- HEX (ROBBER) ---
        if ActionType.MOVE_ROBBER in action_types:
            hex_ids = self.legal_targets(state, ActionType.MOVE_ROBBER)

            for hex_id in hex_ids:
                center = self.world_to_screen(state.board.hex_centers[hex_id])

                # półprzezroczyste wypełnienie
                surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 200, 0, 80), (60, 60), 50)
                self.screen.blit(surf, (center[0] - 60, center[1] - 60))

                # obrys
                pygame.draw.circle(self.screen, HIGHLIGHT_HEX, center, 50, 4)

        # --- VERTEX ---
        vertex_targets = set()

        if ActionType.BUILD_SETTLEMENT in action_types:
            vertex_targets.update(self.legal_targets(state, ActionType.BUILD_SETTLEMENT))

        if ActionType.BUILD_CITY in action_types:
            vertex_targets.update(self.legal_targets(state, ActionType.BUILD_CITY))

        for vertex_id in vertex_targets:
            p = self.world_to_screen(state.board.vertex_positions[vertex_id])

            # glow (półprzezroczyste)
            surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 0, 90), (30, 30), 18)
            self.screen.blit(surf, (p[0] - 30, p[1] - 30))

            # mocny obrys
            pygame.draw.circle(self.screen, HIGHLIGHT_VERTEX, p, 18, 4)

        # --- EDGE ---
        if ActionType.BUILD_ROAD in action_types:
            edge_ids = self.legal_targets(state, ActionType.BUILD_ROAD)

            for edge_id in edge_ids:
                a, b = state.board.edges[edge_id]
                pa = self.world_to_screen(state.board.vertex_positions[a])
                pb = self.world_to_screen(state.board.vertex_positions[b])

                # glow linia
                pygame.draw.line(self.screen, (255, 255, 0, 120), pa, pb, 8)

                # właściwa linia
                pygame.draw.line(self.screen, HIGHLIGHT_EDGE, pa, pb, 4)

    def draw_action_log(self, state):
        rect = pygame.Rect(30, 690, 250, 200)
        self.draw_panel(rect, "Historia akcji")

        log_lines = state.action_log[-7:]  # ostatnie 7 wpisów

        y = rect.y + 40
        for line in log_lines:
            txt = self.font_small.render(line, True, TEXT_COLOR)
            self.screen.blit(txt, (rect.x + 10, y))
            y += 22

    def draw_game_over(self, state):
        if not state.is_terminal():
            return

        p0 = state.victory_points(0)
        p1 = state.victory_points(1)

        if p0 > p1:
            text = "Koniec gry - Player 0 wins"
        elif p1 > p0:
            text = "Koniec gry - Player 1 wins"
        else:
            text = "Koniec gry - Draw"

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        self.screen.blit(overlay, (0, 0))

        label = self.font_large.render(text, True, (255, 255, 255))
        rect = label.get_rect(center=(self.width // 2, 60))
        self.screen.blit(label, rect)

    def draw(self, state):
        self.screen.fill(BACKGROUND)
        self.draw_hexes(state)
        self.draw_highlights(state)
        self.draw_edges(state)
        self.draw_vertices(state)

        self.draw_play_cards_panel(state)
        self.draw_players_panel(state)
        self.draw_status_panel(state)
        self.draw_costs_panel()
        self.draw_buttons(state)
        self.draw_trade_panel(state)
        self.draw_inventory_bar(state)
        self.draw_ports(state)
        self.draw_info_button()
        self.draw_action_log(state)

        self.draw_game_over(state)
        self.draw_modal()
        pygame.display.flip()

    def tick(self, fps=60):
        self.clock.tick(fps)

    def quit(self):
        pygame.quit()