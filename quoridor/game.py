"""The interactive game loop: turns, prompts, clock, and the end-of-game flow."""
from __future__ import annotations

import time
from typing import Callable, Optional

from .board import Board, InvalidMove, InvalidWall
from .clock import ChessClock, format_time
from .history import FORFEIT, MOVE, PASS, WALL, Action, GameRecord
from .models import Direction, Orientation, Wall
from .replay import replay
from .report import format_summary

MOVE_KEYS = {
    "1": Direction.UP,
    "2": Direction.DOWN,
    "3": Direction.LEFT,
    "4": Direction.RIGHT,
}

INTRO = """\
Quoridor - terminal edition
Race your pawn to the opposite edge of the board. On your turn, either
step one cell or place one of your walls to slow the others down.

Walls are two cells long. Name one by its orientation (h or v) and the
row and column (1-8) of its anchor cell:
  h 3 5   sits directly below cell (3, 5) and the cell to its right
  v 3 5   sits directly right of cell (3, 5) and the cell below it
Walls can't overlap or cross, and can never cut off every route to a
player's goal edge."""

MENU = (
    "  1) Move up    2) Move down    3) Move left    4) Move right\n"
    "  5) Place a wall    q) Quit"
)


class _Quit(Exception):
    """The player ended the game (or the input stream closed)."""


class _OutOfTime(Exception):
    """The current player's clock ran out."""


def parse_wall(text: str) -> Optional[Wall]:
    """Parse input like ``h 3 5`` (1-based row and column) into a Wall."""
    parts = text.replace(",", " ").split()
    if len(parts) != 3:
        return None
    kind, row, col = parts
    orientation = {
        "h": Orientation.HORIZONTAL,
        "horizontal": Orientation.HORIZONTAL,
        "v": Orientation.VERTICAL,
        "vertical": Orientation.VERTICAL,
    }.get(kind)
    if orientation is None:
        return None
    try:
        return Wall(orientation, int(row) - 1, int(col) - 1)
    except ValueError:
        return None


class Game:
    def __init__(
        self,
        num_players: int,
        minutes: Optional[float] = None,
        *,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
        now: Callable[[], float] = time.monotonic,
        show_intro: bool = True,
        offer_extras: bool = True,
    ):
        minutes = minutes or None  # 0 means "no clock"
        self.board = Board(num_players)
        self.clock = ChessClock(num_players, minutes * 60 if minutes else None, now)
        self.record = GameRecord(num_players, minutes)
        self._input = input_fn
        self._print = output_fn
        self._show_intro = show_intro
        self._offer_extras = offer_extras
        self.turn = 0

    # ------------------------------------------------------------ main loop
    def play(self) -> GameRecord:
        if self._show_intro:
            self._print(INTRO)
        board = self.board
        idle_turns = 0
        try:
            while True:
                player = self.turn
                if player in board.eliminated:
                    self._next_turn()
                    continue

                if not board.legal_moves(player) and board.walls_left[player] == 0:
                    idle_turns += 1
                    letter = board.specs[player].letter
                    self._print(
                        f"\nPlayer {letter} can't move and has no walls left: turn skipped."
                    )
                    self.record.actions.append(Action(player, PASS))
                    if idle_turns >= len(board.active_players()):
                        self._finish("draw", None)
                        break
                    self._next_turn()
                    continue
                idle_turns = 0

                self._show_turn(player)
                self.clock.start(player)
                try:
                    action = self._prompt_action(player)
                except _OutOfTime:
                    self._forfeit(player)
                    survivors = board.active_players()
                    if len(survivors) == 1:
                        self._finish("timeout", survivors[0])
                        break
                    self._next_turn()
                    continue

                action.seconds = self.clock.stop()
                self.record.actions.append(action)
                if board.has_won(player):
                    self._finish("win", player)
                    break
                self._next_turn()
        except _Quit:
            self._print("\nGame ended.")
            self._finish("abandoned", None)

        if self._offer_extras:
            self._after_game()
        return self.record

    def _next_turn(self) -> None:
        self.turn = (self.turn + 1) % self.board.num_players

    # ------------------------------------------------------------ one turn
    def _show_turn(self, player: int) -> None:
        board, spec = self.board, self.board.specs[player]
        self._print("")
        self._print(board.render())
        if self.clock.enabled:
            clocks = "   ".join(
                f"{board.specs[i].letter} {format_time(self.clock.time_left(i))}"
                for i in board.active_players()
            )
            self._print(f"Clocks: {clocks}")

        turns_taken = sum(
            1 for a in self.record.actions if a.player == player and a.kind in (MOVE, WALL)
        )
        details = [
            f"Turn {turns_taken + 1}",
            f"Walls left: {board.walls_left[player]}",
            f"Distance to goal: {board.distance_to_goal(player)}",
        ]
        self._print(
            f"Player {spec.letter}'s turn ({spec.start_side} -> {spec.goal_side})  "
            + " | ".join(details)
        )
        self._print(MENU)

    def _ask(self, prompt: str, player: int) -> str:
        """Read a line, then enforce the clock (it is checked when you press Enter)."""
        try:
            text = self._input(prompt)
        except (EOFError, KeyboardInterrupt):
            raise _Quit()
        if self.clock.out_of_time(player):
            raise _OutOfTime()
        return text.strip().lower()

    def _prompt_action(self, player: int) -> Action:
        """Ask until the player makes a legal move or wall; apply it and return it."""
        while True:
            choice = self._ask("Your choice [1-5, q to quit]: ", player)
            if choice in MOVE_KEYS:
                direction = MOVE_KEYS[choice]
                try:
                    self.board.move(player, direction)
                except InvalidMove as err:
                    self._print(f"  Can't do that: {err}")
                    continue
                return Action(player, MOVE, direction=direction)
            if choice == "5":
                wall = self._prompt_wall(player)
                if wall is not None:
                    return Action(player, WALL, wall=wall)
                continue
            if choice == "q":
                if self._ask("Really quit the game? [y/N]: ", player) == "y":
                    raise _Quit()
                continue
            self._print("  Please enter a number from 1 to 5, or q to quit.")

    def _prompt_wall(self, player: int) -> Optional[Wall]:
        """Ask for a wall; returns None if the player goes back."""
        while True:
            text = self._ask("Wall (e.g. h 3 5), or b to go back: ", player)
            if text in ("b", "back"):
                return None
            wall = parse_wall(text)
            if wall is None:
                self._print(
                    "  Enter orientation, row and column, e.g. 'h 3 5' "
                    "(h or v, then numbers 1-8)."
                )
                continue
            try:
                self.board.place_wall(player, wall)
            except InvalidWall as err:
                self._print(f"  Can't place that wall: {err}")
                continue
            return wall

    # ------------------------------------------------------------- endings
    def _forfeit(self, player: int) -> None:
        spent = self.clock.stop()
        self.record.actions.append(Action(player, FORFEIT, seconds=spent))
        self.board.eliminate(player)
        letter = self.board.specs[player].letter
        self._print(f"\nPlayer {letter} has run out of time and is out of the game.")

    def _finish(self, outcome: str, winner: Optional[int]) -> None:
        self.clock.stop()
        self.record.outcome = outcome
        self.record.winner = winner
        if outcome != "abandoned":
            self._print("")
            self._print(self.board.render())
        self._print("")
        self._print(format_summary(self.record))

    def _after_game(self) -> None:
        if not self.record.actions:
            return
        try:
            self._print("")
            name = self._input(
                "Save this game to a file? Type a file name, or press Enter to skip: "
            ).strip()
            if name:
                self._save(name)
            choice = (
                self._input(
                    "Watch the replay? [s]tep through, [a]utoplay, or Enter to skip: "
                )
                .strip()
                .lower()
            )
            if choice in ("s", "a"):
                replay(
                    self.record,
                    output=self._print,
                    step=choice == "s",
                    input_fn=self._input,
                )
        except (EOFError, KeyboardInterrupt):
            self._print("")

    def _save(self, name: str) -> None:
        if not name.lower().endswith(".json"):
            name += ".json"
        try:
            self.record.save(name)
        except OSError as err:
            self._print(f"Couldn't save the game: {err}")
        else:
            self._print(f"Saved to {name}. Replay it any time with: python main.py --replay {name}")
