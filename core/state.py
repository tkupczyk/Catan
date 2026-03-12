from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set

from .board import Board
from .actions import Action, ActionType
from . import rules


@dataclass
class PlayerState:
    roads: Set[int] = field(default_factory=set)
    settlements: Set[int] = field(default_factory=set)


@dataclass
class GameState:
    board: Board
    players: List[PlayerState]
    current_player: int = 0

    occupied_vertices: Set[int] = field(default_factory=set)
    occupied_edges: Set[int] = field(default_factory=set)

    phase: str = "SETUP_SETTLEMENT_1"
    setup_reverse: bool = False
    last_setup_settlement: int | None = None

    def clone(self) -> "GameState":
        return GameState(
            board=self.board,
            players=[
                PlayerState(
                    roads=set(p.roads),
                    settlements=set(p.settlements),
                )
                for p in self.players
            ],
            current_player=self.current_player,
            occupied_vertices=set(self.occupied_vertices),
            occupied_edges=set(self.occupied_edges),
            phase=self.phase,
            setup_reverse=self.setup_reverse,
            last_setup_settlement=self.last_setup_settlement,
        )

    def legal_actions(self) -> List[Action]:
        actions: List[Action] = []

        if self.phase in ("SETUP_SETTLEMENT_1", "SETUP_SETTLEMENT_2"):
            for v in range(len(self.board.vertex_positions)):
                if rules.can_build_settlement(self, v):
                    actions.append(Action(ActionType.BUILD_SETTLEMENT, v))
            return actions

        if self.phase in ("SETUP_ROAD_1", "SETUP_ROAD_2"):
            for eid in range(len(self.board.edges)):
                if rules.can_build_road(self, eid):
                    actions.append(Action(ActionType.BUILD_ROAD, eid))
            return actions

        for v in range(len(self.board.vertex_positions)):
            if rules.can_build_settlement(self, v):
                actions.append(Action(ActionType.BUILD_SETTLEMENT, v))

        for eid in range(len(self.board.edges)):
            if rules.can_build_road(self, eid):
                actions.append(Action(ActionType.BUILD_ROAD, eid))

        actions.append(Action(ActionType.END_TURN))
        return actions

    def apply(self, action: Action) -> "GameState":
        s = self.clone()
        s._apply_inplace(action)
        return s

    def _advance_setup_turn(self) -> None:
        num_players = len(self.players)

        if self.phase == "SETUP_ROAD_1":
            if self.current_player < num_players - 1:
                self.current_player += 1
                self.phase = "SETUP_SETTLEMENT_1"
            else:
                self.phase = "SETUP_SETTLEMENT_2"
                self.setup_reverse = True

        elif self.phase == "SETUP_ROAD_2":
            if self.current_player > 0:
                self.current_player -= 1
                self.phase = "SETUP_SETTLEMENT_2"
            else:
                self.phase = "MAIN"

    def _apply_inplace(self, action: Action) -> None:
        player = self.players[self.current_player]

        if action.type == ActionType.BUILD_SETTLEMENT:
            v = action.target
            if v is not None and rules.can_build_settlement(self, v):
                player.settlements.add(v)
                self.occupied_vertices.add(v)

                if self.phase in ("SETUP_SETTLEMENT_1", "SETUP_SETTLEMENT_2"):
                    self.last_setup_settlement = v

                if self.phase == "SETUP_SETTLEMENT_1":
                    self.phase = "SETUP_ROAD_1"
                elif self.phase == "SETUP_SETTLEMENT_2":
                    self.phase = "SETUP_ROAD_2"
            return

        if action.type == ActionType.BUILD_ROAD:
            eid = action.target
            if eid is not None and rules.can_build_road(self, eid):
                player.roads.add(eid)
                self.occupied_edges.add(eid)

                if self.phase in ("SETUP_ROAD_1", "SETUP_ROAD_2"):
                    self.last_setup_settlement = None
                    self._advance_setup_turn()
            return

        if action.type == ActionType.END_TURN and self.phase == "MAIN":
            self.current_player = (self.current_player + 1) % len(self.players)
            return

    def is_terminal(self) -> bool:
        return any(len(p.settlements) >= 3 for p in self.players)

    def reward(self, player_id: int) -> float:
        my = len(self.players[player_id].settlements)
        opp = max(len(p.settlements) for i, p in enumerate(self.players) if i != player_id)
        if my >= 3 and my > opp:
            return 1.0
        if opp >= 3 and opp > my:
            return 0.0
        return 0.5