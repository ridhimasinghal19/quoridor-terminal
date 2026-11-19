"""Wall-aware movement helpers and a breadth-first search over the board.

Pawns are deliberately ignored here: they move, so they never permanently
block a route. Only walls matter.
"""
from __future__ import annotations

from collections import deque
from typing import Callable, Iterable, Iterator, Optional, Tuple

from .models import BOARD_SIZE, Direction, Orientation, Position, Wall

H = Orientation.HORIZONTAL
V = Orientation.VERTICAL


def in_bounds(pos: Position) -> bool:
    return 0 <= pos[0] < BOARD_SIZE and 0 <= pos[1] < BOARD_SIZE


def is_blocked(walls: Iterable[Wall], pos: Position, direction: Direction) -> bool:
    """Is there a wall between ``pos`` and its neighbour in ``direction``?"""
    walls = walls if isinstance(walls, (set, frozenset)) else set(walls)
    row, col = pos
    if direction is Direction.UP:
        crossing = (Wall(H, row - 1, col - 1), Wall(H, row - 1, col))
    elif direction is Direction.DOWN:
        crossing = (Wall(H, row, col - 1), Wall(H, row, col))
    elif direction is Direction.LEFT:
        crossing = (Wall(V, row - 1, col - 1), Wall(V, row, col - 1))
    else:
        crossing = (Wall(V, row - 1, col), Wall(V, row, col))
    return any(wall in walls for wall in crossing)


def open_neighbours(walls, pos: Position) -> Iterator[Tuple[Direction, Position]]:
    """Adjacent cells reachable from ``pos`` without crossing a wall."""
    for direction in Direction:
        target = direction.step(pos)
        if in_bounds(target) and not is_blocked(walls, pos, direction):
            yield direction, target


def distance_to_goal(
    walls, start: Position, is_goal: Callable[[Position], bool]
) -> Optional[int]:
    """Fewest steps from ``start`` to any goal cell, or None if unreachable."""
    if is_goal(start):
        return 0
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        pos, dist = queue.popleft()
        for _, nxt in open_neighbours(walls, pos):
            if nxt in seen:
                continue
            if is_goal(nxt):
                return dist + 1
            seen.add(nxt)
            queue.append((nxt, dist + 1))
    return None
