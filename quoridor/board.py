"""The board: pawn positions, walls, and every rule about legal actions."""
from __future__ import annotations

from typing import List, Optional, Set

from .models import (
    BOARD_SIZE,
    WALLS_PER_PLAYER,
    Direction,
    Orientation,
    Position,
    Wall,
    player_specs,
)
from .pathfinding import distance_to_goal, in_bounds, is_blocked

H = Orientation.HORIZONTAL
V = Orientation.VERTICAL


class InvalidMove(Exception):
    """A pawn move that breaks the rules."""


class InvalidWall(Exception):
    """A wall placement that breaks the rules."""


class Board:
    """Game state for 2 or 4 players. Players are identified by index 0..n-1."""

    def __init__(self, num_players: int = 2):
        self.specs = player_specs(num_players)
        self.positions: List[Position] = [spec.start for spec in self.specs]
        self.walls: Set[Wall] = set()
        self.walls_left: List[int] = [WALLS_PER_PLAYER[num_players]] * num_players
        self.eliminated: Set[int] = set()

    # ------------------------------------------------------------------ state
    @property
    def num_players(self) -> int:
        return len(self.specs)

    def active_players(self) -> List[int]:
        return [i for i in range(self.num_players) if i not in self.eliminated]

    def eliminate(self, player: int) -> None:
        """Remove a player from the game (their pawn leaves the board)."""
        self.eliminated.add(player)

    def has_won(self, player: int) -> bool:
        return player not in self.eliminated and self.specs[player].is_goal(
            self.positions[player]
        )

    def distance_to_goal(self, player: int) -> Optional[int]:
        """Shortest route to the player's goal edge, ignoring other pawns."""
        spec = self.specs[player]
        return distance_to_goal(self.walls, self.positions[player], spec.is_goal)

    # ----------------------------------------------------------------- moving
    def _occupied(self, pos: Position) -> bool:
        return any(
            self.positions[i] == pos for i in self.active_players()
        )

    def move_error(self, player: int, direction: Direction) -> Optional[str]:
        """Why this move is illegal, or None if it is fine."""
        pos = self.positions[player]
        target = direction.step(pos)
        if not in_bounds(target):
            return "You can't move off the board."
        if is_blocked(self.walls, pos, direction):
            return "There's a wall in the way."
        if self._occupied(target):
            return "That cell is occupied by another player."
        return None

    def legal_moves(self, player: int) -> List[Direction]:
        return [d for d in Direction if self.move_error(player, d) is None]

    def move(self, player: int, direction: Direction) -> None:
        error = self.move_error(player, direction)
        if error:
            raise InvalidMove(error)
        self.positions[player] = direction.step(self.positions[player])

    # ----------------------------------------------------------------- walls
    def wall_error(self, player: int, wall: Wall) -> Optional[str]:
        """Why this wall can't be placed, or None if it can."""
        if self.walls_left[player] <= 0:
            return "You have no walls left."

        limit = BOARD_SIZE - 1
        if not (0 <= wall.row < limit and 0 <= wall.col < limit):
            return "That wall doesn't fit on the board."

        r, c = wall.row, wall.col
        if wall.orientation is H:
            same_line = (Wall(H, r, c - 1), Wall(H, r, c), Wall(H, r, c + 1))
            crossing = Wall(V, r, c)
        else:
            same_line = (Wall(V, r - 1, c), Wall(V, r, c), Wall(V, r + 1, c))
            crossing = Wall(H, r, c)
        if any(other in self.walls for other in same_line):
            return "That wall overlaps an existing wall."
        if crossing in self.walls:
            return "That wall would cross an existing wall."

        trial = self.walls | {wall}
        for other in self.active_players():
            spec = self.specs[other]
            if distance_to_goal(trial, self.positions[other], spec.is_goal) is None:
                return (
                    f"That wall would leave player {spec.letter} "
                    "with no route to their goal."
                )
        return None

    def place_wall(self, player: int, wall: Wall) -> None:
        error = self.wall_error(player, wall)
        if error:
            raise InvalidWall(error)
        self.walls.add(wall)
        self.walls_left[player] -= 1

    # -------------------------------------------------------------- rendering
    def render(self) -> str:
        """The board as text, with row/column numbers (1-9) around the edge."""
        cells = {
            self.positions[i]: self.specs[i].letter for i in self.active_players()
        }

        def wall_corner(r: int, c: int) -> str:
            # The junction where four cells meet, below-right of cell (r, c).
            if Wall(H, r, c) in self.walls:
                return "═"
            if Wall(V, r, c) in self.walls:
                return "║"
            return "┼"

        margin = "   "
        header = " " * (len(margin) + 2) + "   ".join(
            str(c + 1) for c in range(BOARD_SIZE)
        )
        lines = [header, margin + "┌" + "┬".join(["───"] * BOARD_SIZE) + "┐"]

        for r in range(BOARD_SIZE):
            row = f"{r + 1:>2} │"
            for c in range(BOARD_SIZE):
                row += f" {cells.get((r, c), ' ')} "
                if c < BOARD_SIZE - 1:
                    blocked = is_blocked(self.walls, (r, c), Direction.RIGHT)
                    row += "║" if blocked else "│"
            lines.append(row + "│")

            if r < BOARD_SIZE - 1:
                sep = margin + "├"
                for c in range(BOARD_SIZE):
                    blocked = is_blocked(self.walls, (r, c), Direction.DOWN)
                    sep += "═══" if blocked else "───"
                    if c < BOARD_SIZE - 1:
                        sep += wall_corner(r, c)
                lines.append(sep + "┤")

        lines.append(margin + "└" + "┴".join(["───"] * BOARD_SIZE) + "┘")
        return "\n".join(lines)
