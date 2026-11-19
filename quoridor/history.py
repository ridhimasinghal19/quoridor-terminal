"""A record of a whole game: every action, plus how it ended. Saved as JSON."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import LETTERS, Direction, Orientation, Wall

FORMAT_VERSION = 1

MOVE = "move"
WALL = "wall"
PASS = "pass"
FORFEIT = "forfeit"  # the player ran out of time and left the game


@dataclass
class Action:
    player: int
    kind: str
    direction: Optional[Direction] = None
    wall: Optional[Wall] = None
    seconds: float = 0.0  # time the player spent on this turn

    def describe(self) -> str:
        who = f"Player {LETTERS[self.player]}"
        if self.kind == MOVE and self.direction:
            return f"{who} moves {self.direction.name.lower()}"
        if self.kind == WALL and self.wall:
            w = self.wall
            kind = "horizontal" if w.orientation is Orientation.HORIZONTAL else "vertical"
            return f"{who} places a {kind} wall at row {w.row + 1}, column {w.col + 1}"
        if self.kind == PASS:
            return f"{who} cannot move and has no walls left, so the turn is skipped"
        if self.kind == FORFEIT:
            return f"{who} runs out of time and is out of the game"
        return f"{who}: {self.kind}"

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "player": self.player,
            "kind": self.kind,
            "seconds": round(self.seconds, 3),
        }
        if self.direction is not None:
            data["direction"] = self.direction.name
        if self.wall is not None:
            data["wall"] = {
                "orientation": self.wall.orientation.value,
                "row": self.wall.row,
                "col": self.wall.col,
            }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        kind = data["kind"]
        if kind not in (MOVE, WALL, PASS, FORFEIT):
            raise ValueError(f"unknown action kind: {kind!r}")
        direction = Direction[data["direction"]] if "direction" in data else None
        wall = None
        if "wall" in data:
            raw = data["wall"]
            wall = Wall(Orientation(raw["orientation"]), int(raw["row"]), int(raw["col"]))
        return cls(
            player=int(data["player"]),
            kind=kind,
            direction=direction,
            wall=wall,
            seconds=float(data.get("seconds", 0.0)),
        )


@dataclass
class GameRecord:
    num_players: int
    minutes_per_player: Optional[float] = None
    actions: List[Action] = field(default_factory=list)
    outcome: str = "in_progress"  # win | timeout | draw | abandoned
    winner: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": FORMAT_VERSION,
            "num_players": self.num_players,
            "minutes_per_player": self.minutes_per_player,
            "outcome": self.outcome,
            "winner": self.winner,
            "actions": [a.to_dict() for a in self.actions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameRecord":
        if data.get("version") != FORMAT_VERSION:
            raise ValueError("this file isn't a supported Quoridor game record")
        num_players = int(data["num_players"])
        if num_players not in (2, 4):
            raise ValueError("a game record must have 2 or 4 players")
        actions = [Action.from_dict(a) for a in data["actions"]]
        if any(not 0 <= a.player < num_players for a in actions):
            raise ValueError("a game record refers to a player that doesn't exist")
        return cls(
            num_players=num_players,
            minutes_per_player=data.get("minutes_per_player"),
            actions=actions,
            outcome=data.get("outcome", "in_progress"),
            winner=data.get("winner"),
        )

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)

    @classmethod
    def load(cls, path: str) -> "GameRecord":
        with open(path, "r", encoding="utf-8") as handle:
            try:
                data = json.load(handle)
            except json.JSONDecodeError as err:
                raise ValueError(f"not valid JSON: {err}") from err
        if not isinstance(data, dict):
            raise ValueError("this file isn't a supported Quoridor game record")
        try:
            return cls.from_dict(data)
        except KeyError as err:
            raise ValueError(f"damaged game record (missing {err})") from err
        except TypeError as err:
            raise ValueError(f"damaged game record ({err})") from err
