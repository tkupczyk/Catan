from dataclasses import dataclass, field
from typing import List, Set
from .board import Board


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

    def next_player(self):
        self.current_player = (self.current_player + 1) % len(self.players)