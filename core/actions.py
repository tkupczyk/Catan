from dataclasses import dataclass
from enum import Enum, auto


class ActionType(Enum):
    ROLL_DICE = auto()
    MOVE_ROBBER = auto()
    TRADE_BANK = auto()
    BUY_DEVELOPMENT_CARD = auto()
    PLAY_KNIGHT = auto()
    BUILD_ROAD = auto()
    BUILD_SETTLEMENT = auto()
    BUILD_CITY = auto()
    END_TURN = auto()
    PASS = auto()


@dataclass(frozen=True)
class Action:
    type: ActionType
    target: int | None = None
    resource_give: object | None = None
    resource_get: object | None = None