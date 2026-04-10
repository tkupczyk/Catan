from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple
from .board import HexResource

class ActionType(Enum):
    ROLL_DICE = auto()
    MOVE_ROBBER = auto()
    TRADE_BANK = auto()
    BUY_DEVELOPMENT_CARD = auto()
    PLAY_KNIGHT = auto()
    PLAY_ROAD_BUILDING = auto()
    PLAY_YEAR_OF_PLENTY = auto()
    STEAL_FROM_PLAYER = auto()
    PLAY_MONOPOLY = auto()
    BUILD_ROAD = auto()
    BUILD_SETTLEMENT = auto()
    BUILD_CITY = auto()
    END_TURN = auto()
    PASS = auto()

@dataclass(frozen=True)
class Action:
    type: ActionType
    target: int | None = None
    resource_give: HexResource | None = None
    resource_get: HexResource | None = None
    chosen_resources: Tuple[HexResource, ...] = ()
    