"""Step through a finished game by re-applying its recorded actions."""
from __future__ import annotations

import time
from typing import Callable

from .board import Board, InvalidMove, InvalidWall
from .history import FORFEIT, MOVE, WALL, Action, GameRecord


def apply_action(board: Board, action: Action) -> None:
    """Apply one recorded action to ``board``; raises ValueError if it is illegal."""
    try:
        if action.kind == MOVE and action.direction is not None:
            board.move(action.player, action.direction)
        elif action.kind == WALL and action.wall is not None:
            board.place_wall(action.player, action.wall)
        elif action.kind == FORFEIT:
            board.eliminate(action.player)
    except (InvalidMove, InvalidWall) as err:
        raise ValueError(f"the recording contains an illegal action: {err}") from err


def replay(
    record: GameRecord,
    *,
    output: Callable[[str], None] = print,
    delay: float = 1.0,
    step: bool = False,
    input_fn: Callable[[str], str] = input,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Print the board after every action.

    With ``step=True`` the replay waits for Enter between turns; otherwise it
    pauses ``delay`` seconds.
    """
    board = Board(record.num_players)
    output("Replay: start position")
    output(board.render())

    total = len(record.actions)
    for number, action in enumerate(record.actions, start=1):
        if step:
            try:
                input_fn("\nPress Enter for the next turn... ")
            except EOFError:
                return
        else:
            sleep(delay)
        apply_action(board, action)
        output(f"\nTurn {number} of {total}: {action.describe()}")
        output(board.render())

    output("\nEnd of replay.")
