"""Basic value types and the fixed layout of the game."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

BOARD_SIZE = 9
Position = Tuple[int, int]  # (row, col); (0, 0) is the top-left cell

WALLS_PER_PLAYER = {2: 10, 4: 5}
LETTERS = "ABCD"


class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

    def step(self, pos: Position) -> Position:
        """The cell one step from ``pos`` in this direction (may be off the board)."""
        d_row, d_col = self.value
        return pos[0] + d_row, pos[1] + d_col


class Orientation(Enum):
    HORIZONTAL = "h"
    VERTICAL = "v"


@dataclass(frozen=True)
class Wall:
    """A wall two cells long, anchored at the cell (row, col).

    * A horizontal wall sits directly *below* the anchor cell and the cell to
      its right.
    * A vertical wall sits directly to the *right* of the anchor cell and the
      cell below it.

    Both anchors range over 0..7, which keeps every wall inside the board and
    off the outer edge.
    """

    orientation: Orientation
    row: int
    col: int


@dataclass(frozen=True)
class PlayerSpec:
    """Where a player starts and which edge they are racing to."""

    index: int
    start: Position
    start_side: str
    goal_side: str

    @property
    def letter(self) -> str:
        return LETTERS[self.index]

    def is_goal(self, pos: Position) -> bool:
        row, col = pos
        if self.goal_side == "top":
            return row == 0
        if self.goal_side == "bottom":
            return row == BOARD_SIZE - 1
        if self.goal_side == "left":
            return col == 0
        return col == BOARD_SIZE - 1


_MID = BOARD_SIZE // 2
_LAST = BOARD_SIZE - 1


def player_specs(num_players: int) -> Tuple[PlayerSpec, ...]:
    """Starting layout, clockwise from the top edge."""
    if num_players == 2:
        layout = [
            ((0, _MID), "top", "bottom"),
            ((_LAST, _MID), "bottom", "top"),
        ]
    elif num_players == 4:
        layout = [
            ((0, _MID), "top", "bottom"),
            ((_MID, _LAST), "right", "left"),
            ((_LAST, _MID), "bottom", "top"),
            ((_MID, 0), "left", "right"),
        ]
    else:
        raise ValueError("Quoridor is played by 2 or 4 players")
    return tuple(
        PlayerSpec(i, start, start_side, goal_side)
        for i, (start, start_side, goal_side) in enumerate(layout)
    )
