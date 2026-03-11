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

    # --- MCTS-friendly API ---

    def clone(self) -> "GameState":
        # Board jest niezmienny (traktujemy jako read-only), więc można współdzielić
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
        )

    def legal_actions(self) -> List[Action]:
        actions: List[Action] = []

        # Osady: wszystkie wierzchołki, które spełniają warunki
        for v in range(len(self.board.vertex_neighbors)):
            if rules.can_build_settlement(self, v):
                actions.append(Action(ActionType.BUILD_SETTLEMENT, v))

        # Drogi: wszystkie krawędzie, które spełniają warunki
        for eid in range(len(self.board.edges)):
            if rules.can_build_road(self, eid):
                actions.append(Action(ActionType.BUILD_ROAD, eid))

        # Zawsze można zakończyć turę (na razie)
        actions.append(Action(ActionType.END_TURN))

        # Bezpiecznik: jakby kiedyś END_TURN był zablokowany fazą, to PASS ratuje rollout
        if not actions:
            actions.append(Action(ActionType.PASS))

        return actions

    def apply(self, action: Action) -> "GameState":
        s = self.clone()
        s._apply_inplace(action)
        return s

    def _apply_inplace(self, action: Action) -> None:
        player = self.players[self.current_player]

        if action.type == ActionType.BUILD_SETTLEMENT:
            v = action.target
            if v is None:
                return
            if rules.can_build_settlement(self, v):
                player.settlements.add(v)
                self.occupied_vertices.add(v)
            return

        if action.type == ActionType.BUILD_ROAD:
            eid = action.target
            if eid is None:
                return
            if rules.can_build_road(self, eid):
                player.roads.add(eid)
                self.occupied_edges.add(eid)
            return

        if action.type == ActionType.END_TURN:
            self.current_player = (self.current_player + 1) % len(self.players)
            return

        if action.type == ActionType.PASS:
            return

    # --- na razie proste zakończenie gry (pod MCTS) ---

    def is_terminal(self) -> bool:
        # MVP: kończymy, gdy któryś gracz ma >= 2 osady (tylko do testów MCTS)
        return any(len(p.settlements) >= 2 for p in self.players)

    def reward(self, player_id: int) -> float:
        # MVP: wygrana jeśli masz 2 osady jako pierwszy (upraszczamy)
        my = len(self.players[player_id].settlements)
        opp = max(len(p.settlements) for i, p in enumerate(self.players) if i != player_id)
        if my >= 2 and my > opp:
            return 1.0
        if opp >= 2 and opp > my:
            return 0.0
        return 0.5