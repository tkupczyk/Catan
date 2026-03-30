import math
import pygame
import os
from core.actions import Action, ActionType
from core.board import HexResource


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

        self.font_small = pygame.font.SysFont("arial", 18)
        self.font_medium = pygame.font.SysFont("arial", 24, bold=True)
        self.font_large = pygame.font.SysFont("arial", 30, bold=True)
        self.roll_button_rect = pygame.Rect(1030, 760, 140, 42)
        self.end_turn_button_rect = pygame.Rect(1190, 760, 140, 42)
        self.resource_icons = self.load_resource_icons()
        self.ui_icons = self.load_ui_icons()
        self.hovered_button = None
        self.pressed_button = None
        self.selected_give_resource = None
        self.selected_get_resource = None
        self.trade_give_rects = {}
        self.trade_get_rects = {}

        start_x = 1140
        give_y = 860
        get_y = 920
        button_w = 42
        button_h = 42
        gap = 8

        for i, resource in enumerate(TRADE_RESOURCES):
            x = start_x + i * (button_w + gap)
            self.trade_give_rects[resource] = pygame.Rect(x, give_y, button_w, button_h)
            self.trade_get_rects[resource] = pygame.Rect(x, get_y, button_w, button_h)

        self.trade_execute_rect = pygame.Rect(1030, 990, 140, 42)


        self.clock = pygame.time.Clock()


    def load_ui_icons(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        pictures_dir = os.path.join(base_dir, "pictures")

        file_map = {
            "settlement": "settlement.png",
            "city": "city.png",
            "road": "road.png",
            "card": "card.png",
        }

        icons = {}

        for name, filename in file_map.items():
            path = os.path.join(pictures_dir, filename)
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.smoothscale(image, (28, 28))
            icons[name] = image

        return icons

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

    def button_at_pos(self, mouse_pos):
        if self.roll_button_rect.collidepoint(mouse_pos):
            return "roll"
        if self.end_turn_button_rect.collidepoint(mouse_pos):
            return "end_turn"
        if self.trade_execute_rect.collidepoint(mouse_pos):
            return "trade"
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

        if pressed == "roll":
            if self.has_action_type(state, ActionType.ROLL_DICE):
                return state.apply(Action(ActionType.ROLL_DICE))
            return state

        if pressed == "end_turn":
            if self.has_action_type(state, ActionType.END_TURN):
                return state.apply(Action(ActionType.END_TURN))
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
        if state.phase == "ROBBER":
            return "Przesuń złodzieja"

        if not state.dice_rolled:
            return "Rzuć kośćmi"

        return "Buduj, handluj, lub zakończ turę"

    def handle_click(self, state, mouse_pos):
        print("handle_click called")

        # 1. Obsługa złodzieja: klik w hex
        if state.phase == "ROBBER":
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



    def draw_trade_panel(self, state):
        rect = pygame.Rect(1030, 820, 320, 230)
        self.draw_panel(rect, "Handel z bankiem")

        give_label = self.font_small.render("Oddaj 4:", True, TEXT_COLOR)
        self.screen.blit(give_label, (rect.x + 14, rect.y + 42))

        take_label = self.font_small.render("Otrzymaj 1:", True, TEXT_COLOR)
        self.screen.blit(take_label, (rect.x + 14, rect.y + 102))

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

    def draw_inventory_bar(self, state):
        player = state.players[0]  # człowiek

        bar_rect = pygame.Rect(210, 970, 630, 68)
        self.draw_panel(bar_rect)

        items = [
            ("settlement", len(player.settlements)),
            ("city", len(player.cities)),
            ("road", len(player.roads)),
            (HexResource.BRICK, player.resources[HexResource.BRICK]),
            (HexResource.ORE, player.resources[HexResource.ORE]),
            (HexResource.LUMBER, player.resources[HexResource.LUMBER]),
            (HexResource.WOOL, player.resources[HexResource.WOOL]),
            (HexResource.GRAIN, player.resources[HexResource.GRAIN]),
        ]

        x = bar_rect.x + 16
        y = bar_rect.y + 18

        for item, amount in items:
            if isinstance(item, HexResource):
                icon = self.resource_icons.get(item)
            else:
                icon = self.ui_icons.get(item)

            if icon is not None:
                icon_rect = icon.get_rect(topleft=(x, y - 4))
                self.screen.blit(icon, icon_rect)

            txt = self.font_small.render(str(amount), True, TEXT_COLOR)
            self.screen.blit(txt, (x + 40, y + 3))

            x += 76

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
        rect = pygame.Rect(1030, 155, 320, 170)
        self.draw_panel(rect, "Koszty")

        rows = [
            ("Droga", [("road", None), (HexResource.BRICK, 1), (HexResource.LUMBER, 1)]),
            ("Osada", [("settlement", None), (HexResource.BRICK, 1), (HexResource.LUMBER, 1), (HexResource.WOOL, 1), (HexResource.GRAIN, 1)]),
            ("Miasto", [("city", None), (HexResource.GRAIN, 2), (HexResource.ORE, 3)]),
            ("Rozwój", [("card", None), (HexResource.WOOL, 1), (HexResource.GRAIN, 1), (HexResource.ORE, 1)]),
        ]

        y = rect.y + 38
        for label, items in rows:
            txt = self.font_small.render(label, True, TEXT_COLOR)
            self.screen.blit(txt, (rect.x + 14, y + 6))

            x = rect.x + 90
            for item, amount in items:
                if isinstance(item, HexResource):
                    icon = self.resource_icons.get(item)
                else:
                    icon = self.ui_icons.get(item)

                if icon is not None:
                    icon_rect = icon.get_rect(topleft=(x, y))
                    self.screen.blit(icon, icon_rect)

                if amount is not None:
                    amount_txt = self.font_small.render(str(amount), True, TEXT_COLOR)
                    self.screen.blit(amount_txt, (x + 30, y + 6))
                    x += 52
                else:
                    x += 38

            y += 32

    def draw_players_panel(self, state):
        positions = [
            pygame.Rect(30, 30, 250, 130),
            pygame.Rect(30, 175, 250, 130),
        ]

        for player_id, rect in enumerate(positions):
            self.draw_panel(rect, f"Gracz {player_id}")

            color = PLAYER_COLORS[player_id]
            pygame.draw.circle(self.screen, color, (rect.x + 210, rect.y + 20), 8)

            player = state.players[player_id]
            vp = state.victory_points(player_id)

            items = [
                ("settlement", len(player.settlements)),
                ("city", len(player.cities)),
                ("road", len(player.roads)),
            ]

            x = rect.x + 14
            y = rect.y + 42

            # PV
            vp_txt = self.font_small.render(f"PZ: {vp}", True, TEXT_COLOR)
            self.screen.blit(vp_txt, (x, y))
            y += 28

            for item, amount in items:
                icon = self.ui_icons.get(item)
                if icon is not None:
                    icon_rect = icon.get_rect(topleft=(x, y - 4))
                    self.screen.blit(icon, icon_rect)

                amount_txt = self.font_small.render(str(amount), True, TEXT_COLOR)
                self.screen.blit(amount_txt, (x + 34, y + 2))
                x += 70

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

        self.draw_players_panel(state)
        self.draw_status_panel(state)
        self.draw_costs_panel()
        self.draw_trade_panel(state)
        self.draw_inventory_bar(state)

        self.draw_buttons(state)
        self.draw_game_over(state)
        pygame.display.flip()

    def tick(self, fps=60):
        self.clock.tick(fps)

    def quit(self):
        pygame.quit()