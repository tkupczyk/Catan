from dataclasses import dataclass
from enum import Enum, auto


class ActionType(Enum):
    BUILD_ROAD = auto()
    BUILD_SETTLEMENT = auto()
    END_TURN = auto()


@dataclass(frozen=True)
class Action:
    type: ActionType
    target: int | None = None