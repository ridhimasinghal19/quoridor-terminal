"""End-of-game statistics and the summary shown when a game finishes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .clock import format_time
from .history import FORFEIT, MOVE, WALL, GameRecord
from .models import LETTERS, WALLS_PER_PLAYER, player_specs


@dataclass
class PlayerStats:
    letter: str
    steps: int = 0
    walls_placed: int = 0
    walls_left: int = 0
    seconds_used: float = 0.0
    timed_out: bool = False

    @property
    def turns(self) -> int:
        return self.steps + self.walls_placed


def player_stats(record: GameRecord) -> List[PlayerStats]:
    stats = [
        PlayerStats(LETTERS[i], walls_left=WALLS_PER_PLAYER[record.num_players])
        for i in range(record.num_players)
    ]
    for action in record.actions:
        s = stats[action.player]
        s.seconds_used += action.seconds
        if action.kind == MOVE:
            s.steps += 1
        elif action.kind == WALL:
            s.walls_placed += 1
            s.walls_left -= 1
        elif action.kind == FORFEIT:
            s.timed_out = True
    return stats


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def headline(record: GameRecord) -> str:
    stats = player_stats(record)
    if record.outcome == "win" and record.winner is not None:
        s = stats[record.winner]
        goal = player_specs(record.num_players)[record.winner].goal_side
        return (
            f"Player {s.letter} wins by reaching the {goal} edge after "
            f"{_plural(s.turns, 'turn')} ({_plural(s.steps, 'step')} and "
            f"{_plural(s.walls_placed, 'wall')} placed)."
        )
    if record.outcome == "timeout" and record.winner is not None:
        letters = [s.letter for s in stats if s.timed_out]
        return (
            f"Player {stats[record.winner].letter} wins on time: "
            f"{', '.join(letters)} ran out of clock."
        )
    if record.outcome == "draw":
        return "The game is a draw: nobody can move or place a wall."
    return "The game was abandoned before anyone won."


def format_summary(record: GameRecord) -> str:
    stats = player_stats(record)
    rows = [("Player", "Turns", "Steps", "Walls placed", "Walls left", "Time used")]
    for s in stats:
        name = s.letter + (" (out)" if s.timed_out else "")
        rows.append(
            (
                name,
                str(s.turns),
                str(s.steps),
                str(s.walls_placed),
                str(s.walls_left),
                format_time(s.seconds_used),
            )
        )
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    table = [
        "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip()
        for row in rows
    ]
    table.insert(1, "  ".join("-" * w for w in widths))

    total_turns = sum(1 for a in record.actions if a.kind in (MOVE, WALL))
    total_time = sum(a.seconds for a in record.actions)
    lines = [
        "=" * 14 + " GAME OVER " + "=" * 14,
        headline(record),
        "",
        *table,
        "",
        f"Total turns: {total_turns}   Game time: {format_time(total_time)}",
    ]
    return "\n".join(lines)
