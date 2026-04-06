from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set
import random
from enum import Enum
from .board import Board, HexResource
from .actions import Action, ActionType
from . import rules


@dataclass
class PlayerState:
    roads: Set[int] = field(default_factory=set)
    settlements: Set[int] = field(default_factory=set)
    cities: Set[int] = field(default_factory=set)
    development_cards: List[DevelopmentCard] = field(default_factory=list)
    new_development_cards: List[DevelopmentCard] = field(default_factory=list)
    played_knights: int = 0
    resources: Dict[HexResource, int] = field(default_factory=lambda: {
        HexResource.BRICK: 0,
        HexResource.LUMBER: 0,
        HexResource.WOOL: 0,
        HexResource.GRAIN: 0,
        HexResource.ORE: 0,
    })

class DevelopmentCard(Enum):
    KNIGHT = "knight"
    VICTORY_POINT = "victory_point"
    ROAD_BUILDING = "road_building"
    YEAR_OF_PLENTY = "year_of_plenty"
    MONOPOLY = "monopoly"

@dataclass
class GameState:
    board: Board
    players: List[PlayerState]
    current_player: int = 0

    action_log: List[str] = field(default_factory=list)
    development_deck: List[DevelopmentCard] = field(default_factory=list)
    largest_army_owner: int | None = None
    longest_road_owner: int | None = None
    longest_road_length: int = 0
    free_roads_to_build: int = 0

    occupied_vertices: Set[int] = field(default_factory=set)
    occupied_edges: Set[int] = field(default_factory=set)

    phase: str = "SETUP_SETTLEMENT_1"
    last_setup_settlement: int | None = None

    dice_rolled: bool = False
    last_roll: int | None = None

    robber_hex: int = 0

    def clone(self) -> "GameState":
        return GameState(
            board=self.board,
            players=[
                PlayerState(
                    roads=set(p.roads),
                    settlements=set(p.settlements),
                    cities=set(p.cities),
                    development_cards=list(p.development_cards),
                    new_development_cards=list(p.new_development_cards),
                    played_knights=p.played_knights,
                    resources=dict(p.resources),
                )
                for p in self.players
            ],
            current_player=self.current_player,
            development_deck=list(self.development_deck),
            occupied_vertices=set(self.occupied_vertices),
            occupied_edges=set(self.occupied_edges),
            largest_army_owner=self.largest_army_owner,
            free_roads_to_build=self.free_roads_to_build,
            phase=self.phase,
            last_setup_settlement=self.last_setup_settlement,
            longest_road_owner=self.longest_road_owner,
            longest_road_length=self.longest_road_length,
            action_log=list(self.action_log),
            dice_rolled=self.dice_rolled,
            last_roll=self.last_roll,
            robber_hex=self.robber_hex,
        )
    
    def log(self, text: str) -> None:
        self.action_log.append(text)

        # trzymaj tylko ostatnie 30 wpisów
        if len(self.action_log) > 30:
            self.action_log = self.action_log[-30:]

    @staticmethod
    def default_development_deck() -> List[DevelopmentCard]:
        deck = (
            [DevelopmentCard.KNIGHT] * 14 +
            [DevelopmentCard.VICTORY_POINT] * 5 +
            [DevelopmentCard.ROAD_BUILDING] * 2 +
            [DevelopmentCard.YEAR_OF_PLENTY] * 2 +
            [DevelopmentCard.MONOPOLY] * 2
        )
        random.shuffle(deck)
        return deck

    def _is_vertex_blocked_for_road(self, vertex: int, player_id: int) -> bool:
        """
        Cudza osada/miasto na vertexie blokuje przejście drogi.
        Własna nie blokuje.
        """
        for pid, player in enumerate(self.players):
            if pid == player_id:
                continue
            if vertex in player.settlements or vertex in player.cities:
                return True
        return False

    def update_largest_army(self) -> None:
        """
        Przyznaje Najwyższą Władzę Rycerską graczowi,
        który ma co najmniej 3 zagranych rycerzy i więcej
        niż każdy inny gracz.
        """
        best_player = None
        best_count = 2  # trzeba mieć co najmniej 3

        for player_id, player in enumerate(self.players):
            if player.played_knights > best_count:
                best_count = player.played_knights
                best_player = player_id

        if best_player is None:
            return

        # sprawdź, czy remis na best_count
        num_with_best = sum(
            1 for p in self.players if p.played_knights == best_count
        )

        if num_with_best == 1:
            self.largest_army_owner = best_player

    def longest_road_for_player(self, player_id: int) -> int:
        player = self.players[player_id]
        player_roads = set(player.roads)

        if not player_roads:
            return 0

        # adjacency tylko z dróg gracza
        road_graph = {v: [] for v in range(len(self.board.vertex_positions))}
        for edge_id in player_roads:
            a, b = self.board.edges[edge_id]
            road_graph[a].append((b, edge_id))
            road_graph[b].append((a, edge_id))

        best = 0

        def dfs(vertex: int, used_edges: set[int]) -> int:
            nonlocal best
            max_len = 0

            # jeśli vertex jest zablokowany przez przeciwnika,
            # nie można iść dalej przez ten vertex
            if self._is_vertex_blocked_for_road(vertex, player_id) and used_edges:
                return 0

            for next_vertex, edge_id in road_graph[vertex]:
                if edge_id in used_edges:
                    continue

                used_edges.add(edge_id)
                length = 1 + dfs(next_vertex, used_edges)
                used_edges.remove(edge_id)

                if length > max_len:
                    max_len = length

            if max_len > best:
                best = max_len

            return max_len

        for vertex in road_graph:
            dfs(vertex, set())

        return best

    def update_longest_road(self) -> None:
        lengths = [self.longest_road_for_player(i) for i in range(len(self.players))]
        best_length = max(lengths)

        if best_length < 5:
            return

        candidates = [i for i, length in enumerate(lengths) if length == best_length]

        if len(candidates) == 1:
            owner = candidates[0]

            if self.longest_road_owner is None:
                self.longest_road_owner = owner
                self.longest_road_length = best_length
                return

            if self.longest_road_owner == owner:
                self.longest_road_length = best_length
                return

            # przejęcie tylko jeśli nowy właściciel ma więcej niż poprzedni właściciel
            previous_length = lengths[self.longest_road_owner]
            if best_length > previous_length:
                self.longest_road_owner = owner
                self.longest_road_length = best_length

    def legal_actions(self) -> List[Action]:
        actions: List[Action] = []

        if self.phase == "ROAD_BUILDING":
            for eid in range(len(self.board.edges)):
                if rules.can_build_road(self, eid):
                    actions.append(Action(ActionType.BUILD_ROAD, eid))

            if self.free_roads_to_build <= 0:
                actions.append(Action(ActionType.PASS))

            return actions
        
        # setup: osada
        if self.phase in ("SETUP_SETTLEMENT_1", "SETUP_SETTLEMENT_2"):
            for v in range(len(self.board.vertex_positions)):
                if rules.can_build_settlement(self, v):
                    actions.append(Action(ActionType.BUILD_SETTLEMENT, v))
            return actions

        # setup: droga
        if self.phase in ("SETUP_ROAD_1", "SETUP_ROAD_2"):
            for eid in range(len(self.board.edges)):
                if rules.can_build_road(self, eid):
                    actions.append(Action(ActionType.BUILD_ROAD, eid))
            return actions

        # faza złodzieja
        if self.phase in ("ROBBER", "ROBBER_FROM_KNIGHT"):
            for hex_id in range(len(self.board.hex_vertices)):
                if rules.can_move_robber(self, hex_id):
                    actions.append(Action(ActionType.MOVE_ROBBER, hex_id))
            return actions

        # główna faza: najpierw rzut
        if self.phase == "MAIN" and not self.dice_rolled:
            return [Action(ActionType.ROLL_DICE)]

        # główna faza po rzucie
        player = self.players[self.current_player]

        for v in range(len(self.board.vertex_positions)):
            if rules.can_build_settlement(self, v):
                actions.append(Action(ActionType.BUILD_SETTLEMENT, v))

        for eid in range(len(self.board.edges)):
            if rules.can_build_road(self, eid):
                actions.append(Action(ActionType.BUILD_ROAD, eid))

        for v in range(len(self.board.vertex_positions)):
            if rules.can_build_city(self, v):
                actions.append(Action(ActionType.BUILD_CITY, v))

        if rules.can_buy_development_card(self):
            actions.append(Action(ActionType.BUY_DEVELOPMENT_CARD))

        if DevelopmentCard.KNIGHT in player.development_cards:
            actions.append(Action(ActionType.PLAY_KNIGHT))

        if DevelopmentCard.ROAD_BUILDING in player.development_cards:
            actions.append(Action(ActionType.PLAY_ROAD_BUILDING))

        if DevelopmentCard.YEAR_OF_PLENTY in player.development_cards:
            actions.append(Action(ActionType.PLAY_YEAR_OF_PLENTY))

        if DevelopmentCard.MONOPOLY in player.development_cards:
            actions.append(Action(ActionType.PLAY_MONOPOLY))

        trade_resources = [
            HexResource.BRICK,
            HexResource.LUMBER,
            HexResource.WOOL,
            HexResource.GRAIN,
            HexResource.ORE,
        ]

        for give_resource in trade_resources:
            for get_resource in trade_resources:
                if rules.can_trade_bank(self, give_resource, get_resource):
                    actions.append(
                        Action(
                            ActionType.TRADE_BANK,
                            resource_give=give_resource,
                            resource_get=get_resource,
                        )
                    )

        actions.append(Action(ActionType.END_TURN))
        return actions

    def apply(self, action: Action) -> "GameState":
        s = self.clone()
        s._apply_inplace(action)
        return s

    def roll_dice(self) -> int:
        return random.randint(1, 6) + random.randint(1, 6)

    def _advance_setup_turn(self) -> None:
        num_players = len(self.players)

        if self.phase == "SETUP_ROAD_1":
            if self.current_player < num_players - 1:
                self.current_player += 1
                self.phase = "SETUP_SETTLEMENT_1"
            else:
                self.phase = "SETUP_SETTLEMENT_2"

        elif self.phase == "SETUP_ROAD_2":
            if self.current_player > 0:
                self.current_player -= 1
                self.phase = "SETUP_SETTLEMENT_2"
            else:
                self.phase = "MAIN"
                self.dice_rolled = False
                self.last_roll = None

    def _apply_inplace(self, action: Action) -> None:
        player = self.players[self.current_player]

        # rzut kośćmi
        if action.type == ActionType.ROLL_DICE and self.phase == "MAIN" and not self.dice_rolled:
            roll = self.roll_dice()
            self.last_roll = roll
            self.dice_rolled = True
            self.log(f"Gracz {self.current_player}: rzut {roll}")

            if roll == 7:
                self.log(f"Gracz {self.current_player}: aktywował złodzieja")
                self.phase = "ROBBER"
            else:
                self.produce_resources(roll)
            return

        # zagranie rycerza
        if action.type == ActionType.PLAY_KNIGHT and self.phase == "MAIN":
            if DevelopmentCard.KNIGHT in player.development_cards:
                player.development_cards.remove(DevelopmentCard.KNIGHT)
                player.played_knights += 1
                self.update_largest_army()
                self.phase = "ROBBER_FROM_KNIGHT"
                self.log(f"Gracz {self.current_player}: zagrał Rycerza")
            return

        if action.type == ActionType.PLAY_ROAD_BUILDING and self.phase == "MAIN":
            if DevelopmentCard.ROAD_BUILDING in player.development_cards:
                player.development_cards.remove(DevelopmentCard.ROAD_BUILDING)
                self.phase = "ROAD_BUILDING"
                self.free_roads_to_build = 2
                self.log(f"Gracz {self.current_player}: zagrał kartę Budowa Dróg")
            return

        if action.type == ActionType.PLAY_YEAR_OF_PLENTY and self.phase == "MAIN":
            if DevelopmentCard.YEAR_OF_PLENTY in player.development_cards:
                chosen = list(action.chosen_resources)

                if len(chosen) == 2:
                    player.development_cards.remove(DevelopmentCard.YEAR_OF_PLENTY)
                    chosen_names = ", ".join(r.value for r in chosen)
                    self.log(f"Gracz {self.current_player}: zagrał Wynalazek ({chosen_names})")

                    for resource in chosen:
                        player.resources[resource] += 1
            return

        if action.type == ActionType.PLAY_MONOPOLY and self.phase == "MAIN":
            if DevelopmentCard.MONOPOLY in player.development_cards:
                resource = action.resource_get
                if resource is not None:
                    player.development_cards.remove(DevelopmentCard.MONOPOLY)
                    self.log(f"Gracz {self.current_player}: zagrał Monopol ({resource.value})")

                    total_taken = 0
                    for pid, other in enumerate(self.players):
                        if pid == self.current_player:
                            continue
                        amount = other.resources[resource]
                        if amount > 0:
                            other.resources[resource] -= amount
                            total_taken += amount

                    player.resources[resource] += total_taken
            return

        # przesunięcie złodzieja
        if action.type == ActionType.MOVE_ROBBER and self.phase in ("ROBBER", "ROBBER_FROM_KNIGHT"):
            hex_id = action.target
            
            if hex_id is not None and rules.can_move_robber(self, hex_id):
                self.robber_hex = hex_id
                self.log(f"Gracz {self.current_player}: przesunął złodzieja na heks {hex_id}")

                candidates = [
                    pid for pid in self._players_touching_hex(hex_id)
                    if pid != self.current_player
                ]

                if candidates:
                    victim_id = candidates[0]
                    self._steal_one_resource(victim_id)

                self.phase = "MAIN"
            return

        # budowa osady
        if action.type == ActionType.BUILD_SETTLEMENT:
            v = action.target
            if v is not None and rules.can_build_settlement(self, v):
                if self.phase == "MAIN":
                    rules.pay_cost(player, rules.SETTLEMENT_COST)
                    self.log(f"Gracz {self.current_player}: zbudował osadę")

                player.settlements.add(v)
                self.occupied_vertices.add(v)

                if self.phase in ("SETUP_SETTLEMENT_1", "SETUP_SETTLEMENT_2"):
                    self.last_setup_settlement = v

                if self.phase == "SETUP_SETTLEMENT_2":
                    self._grant_setup_resources(v)

                if self.phase == "SETUP_SETTLEMENT_1":
                    self.phase = "SETUP_ROAD_1"
                elif self.phase == "SETUP_SETTLEMENT_2":
                    self.phase = "SETUP_ROAD_2"
            return

        # budowa drogi
        if action.type == ActionType.BUILD_ROAD:
            eid = action.target
            if eid is not None and rules.can_build_road(self, eid):
                if self.phase == "MAIN":
                    rules.pay_cost(player, rules.ROAD_COST)
                    self.log(f"Gracz {self.current_player}: zbudował drogę")

                player.roads.add(eid)
                self.occupied_edges.add(eid)
                self.update_longest_road()

                if self.phase == "ROAD_BUILDING":
                    self.free_roads_to_build -= 1
                    if self.free_roads_to_build <= 0:
                        self.phase = "MAIN"

                if self.phase in ("SETUP_ROAD_1", "SETUP_ROAD_2"):
                    self.last_setup_settlement = None
                    self._advance_setup_turn()
            return
        
        if action.type == ActionType.PLAY_ROAD_BUILDING and self.phase == "MAIN":
            if DevelopmentCard.ROAD_BUILDING in player.development_cards:
                player.development_cards.remove(DevelopmentCard.ROAD_BUILDING)
                self.phase = "ROAD_BUILDING"
                self.free_roads_to_build = 2
            return
        
        # budowa miasta
        if action.type == ActionType.BUILD_CITY:
            v = action.target
            if v is not None and rules.can_build_city(self, v):
                rules.pay_cost(player, rules.CITY_COST)
                player.settlements.remove(v)
                player.cities.add(v)
                self.log(f"Gracz {self.current_player}: zbudował miasto")
            return

        # handel z bankiem
        if action.type == ActionType.TRADE_BANK:
            give_resource = action.resource_give
            get_resource = action.resource_get

            if rules.can_trade_bank(self, give_resource, get_resource):
                ratio = rules.get_player_trade_ratio(self, self.current_player, give_resource)
                player.resources[give_resource] -= ratio
                player.resources[get_resource] += 1
                self.log(
                    f"Gracz {self.current_player}: handel {give_resource.value} → {get_resource.value}"
                )
            return

        if action.type == ActionType.BUY_DEVELOPMENT_CARD:
            if rules.can_buy_development_card(self):
                rules.pay_cost(player, rules.DEVELOPMENT_CARD_COST)
                drawn = self.development_deck.pop()
                player.new_development_cards.append(drawn)
                self.log(f"Gracz {self.current_player}: kupił kartę rozwoju")
            return

        # koniec tury
        if action.type == ActionType.END_TURN:
            ending_player = self.current_player
            player.development_cards.extend(player.new_development_cards)
            player.new_development_cards.clear()
            self.log(f"Gracz {ending_player}: zakończył turę")

            self.current_player = 1 - self.current_player
            self.dice_rolled = False
            self.last_roll = None
            return

        if action.type == ActionType.PASS:
            if self.phase == "ROAD_BUILDING":
                self.free_roads_to_build = 0
                self.phase = "MAIN"
            return

    def _grant_setup_resources(self, vertex: int) -> None:
        """
        Przy drugiej osadzie setupowej gracz dostaje po 1 surowcu
        z każdego sąsiedniego heksa (oprócz pustyni).
        """
        player = self.players[self.current_player]

        for hex_id, hex_verts in enumerate(self.board.hex_vertices):
            if vertex not in hex_verts:
                continue

            resource = self.board.hex_resources[hex_id]
            if resource == HexResource.DESERT:
                continue

            player.resources[resource] += 1


    def _players_touching_hex(self, hex_id: int) -> list[int]:
        """
        Zwraca listę ID graczy, którzy mają osadę lub miasto
        na dowolnym wierzchołku danego heksa.
        """
        touched_vertices = set(self.board.hex_vertices[hex_id])
        result = []

        for player_id, player in enumerate(self.players):
            if any(v in touched_vertices for v in player.settlements) or \
               any(v in touched_vertices for v in player.cities):
                result.append(player_id)

        return result

    def _steal_one_resource(self, victim_id: int) -> None:
        """
        Bieżący gracz kradnie 1 losowy surowiec od victim_id,
        jeśli ofiara ma jakiekolwiek zasoby.
        """
        thief = self.players[self.current_player]
        victim = self.players[victim_id]

        available = []
        for resource, amount in victim.resources.items():
            if amount > 0:
                available.append(resource)

        if not available:
            return

        stolen_resource = random.choice(available)
        victim.resources[stolen_resource] -= 1
        thief.resources[stolen_resource] += 1

    def produce_resources(self, dice_roll: int) -> None:
        """
        Rozdaj surowce za heksy z numerem == dice_roll.
        Hex z rabusiem nie produkuje.
        Osada = 1 surowiec
        Miasto = 2 surowce
        """
        for hex_id, number in enumerate(self.board.hex_numbers):
            if number != dice_roll:
                continue

            if hex_id == self.robber_hex:
                continue

            resource = self.board.hex_resources[hex_id]
            if resource == HexResource.DESERT:
                continue

            touched_vertices = self.board.hex_vertices[hex_id]

            for player in self.players:
                for vertex in player.settlements:
                    if vertex in touched_vertices:
                        player.resources[resource] += 1

                for vertex in player.cities:
                    if vertex in touched_vertices:
                        player.resources[resource] += 2

    def victory_points(self, player_id: int) -> int:
        player = self.players[player_id]

        vp_cards = sum(
            1 for card in player.development_cards
            if card == DevelopmentCard.VICTORY_POINT
        )
        vp_cards += sum(
            1 for card in player.new_development_cards
            if card == DevelopmentCard.VICTORY_POINT
        )

        total = len(player.settlements) + 2 * len(player.cities) + vp_cards

        if self.largest_army_owner == player_id:
            total += 2

        if self.longest_road_owner == player_id:
            total += 2

        return total

    def is_terminal(self) -> bool:
        return any(self.victory_points(i) >= 10 for i in range(len(self.players)))

    def reward(self, player_id: int) -> float:
        my_vp = self.victory_points(player_id)
        opp_vp = max(
            self.victory_points(i)
            for i in range(len(self.players))
            if i != player_id
        )

        if my_vp >= 10 and my_vp > opp_vp:
            return 1.0
        if opp_vp >= 10 and opp_vp > my_vp:
            return 0.0
        return 0.5