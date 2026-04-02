from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set
import random

from .board import Board, HexResource
from .actions import Action, ActionType
from . import rules


@dataclass
class PlayerState:
    roads: Set[int] = field(default_factory=set)
    settlements: Set[int] = field(default_factory=set)
    cities: Set[int] = field(default_factory=set)

    resources: Dict[HexResource, int] = field(default_factory=lambda: {
        HexResource.BRICK: 0,
        HexResource.LUMBER: 0,
        HexResource.WOOL: 0,
        HexResource.GRAIN: 0,
        HexResource.ORE: 0,
    })


@dataclass
class GameState:
    board: Board
    players: List[PlayerState]
    current_player: int = 0

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
                    resources=dict(p.resources),
                )
                for p in self.players
            ],
            current_player=self.current_player,
            occupied_vertices=set(self.occupied_vertices),
            occupied_edges=set(self.occupied_edges),
            phase=self.phase,
            last_setup_settlement=self.last_setup_settlement,
            dice_rolled=self.dice_rolled,
            last_roll=self.last_roll,
            robber_hex=self.robber_hex,
        )

    def legal_actions(self) -> List[Action]:
        actions: List[Action] = []

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
        if self.phase == "ROBBER":
            for hex_id in range(len(self.board.hex_vertices)):
                if rules.can_move_robber(self, hex_id):
                    actions.append(Action(ActionType.MOVE_ROBBER, hex_id))
            return actions

        # główna faza: najpierw rzut
        if self.phase == "MAIN" and not self.dice_rolled:
            return [Action(ActionType.ROLL_DICE)]

        # główna faza po rzucie
        for v in range(len(self.board.vertex_positions)):
            if rules.can_build_settlement(self, v):
                actions.append(Action(ActionType.BUILD_SETTLEMENT, v))

        for eid in range(len(self.board.edges)):
            if rules.can_build_road(self, eid):
                actions.append(Action(ActionType.BUILD_ROAD, eid))

        for v in range(len(self.board.vertex_positions)):
            if rules.can_build_city(self, v):
                actions.append(Action(ActionType.BUILD_CITY, v))

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

            if roll == 7:
                self.phase = "ROBBER"
            else:
                self.produce_resources(roll)
            return

        # przesunięcie złodzieja
        if action.type == ActionType.MOVE_ROBBER and self.phase == "ROBBER":
            hex_id = action.target
            if hex_id is not None and rules.can_move_robber(self, hex_id):
                self.robber_hex = hex_id

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

                player.roads.add(eid)
                self.occupied_edges.add(eid)

                if self.phase in ("SETUP_ROAD_1", "SETUP_ROAD_2"):
                    self.last_setup_settlement = None
                    self._advance_setup_turn()
            return

        # budowa miasta
        if action.type == ActionType.BUILD_CITY:
            v = action.target
            if v is not None and rules.can_build_city(self, v):
                rules.pay_cost(player, rules.CITY_COST)
                player.settlements.remove(v)
                player.cities.add(v)
            return

        # handel z bankiem
        if action.type == ActionType.TRADE_BANK:
            give_resource = action.resource_give
            get_resource = action.resource_get

            if rules.can_trade_bank(self, give_resource, get_resource):
                ratio = rules.get_player_trade_ratio(self, self.current_player, give_resource)
                player.resources[give_resource] -= ratio
                player.resources[get_resource] += 1
            return

        # koniec tury
        if action.type == ActionType.END_TURN and self.phase == "MAIN" and self.dice_rolled:
            self.current_player = (self.current_player + 1) % len(self.players)
            self.dice_rolled = False
            self.last_roll = None
            return

        if action.type == ActionType.PASS:
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
        return len(player.settlements) + 2 * len(player.cities)

    def is_terminal(self) -> bool:
        return any(self.victory_points(i) >= 10 for i in range(len(self.players)))

    def reward(self, player_id: int) -> float:
        my_vp = self.victory_points(player_id)
        opp_vp = max(
            self.victory_points(i)
            for i in range(len(self.players))
            if i != player_id
        )

        if my_vp >= 5 and my_vp > opp_vp:
            return 1.0
        if opp_vp >= 5 and opp_vp > my_vp:
            return 0.0
        return 0.5