"""Command-line entry point."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .game import Game
from .history import GameRecord
from .replay import replay

DEFAULT_MINUTES = 5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quoridor",
        description="Play Quoridor in the terminal, or replay a saved game.",
    )
    parser.add_argument("--players", type=int, choices=(2, 4), help="number of players")
    parser.add_argument(
        "--minutes",
        type=float,
        help=f"clock time per player in minutes (0 = no clock; default {DEFAULT_MINUTES})",
    )
    parser.add_argument("--replay", metavar="FILE", help="replay a saved game and exit")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="seconds between turns in a replay"
    )
    parser.add_argument(
        "--step", action="store_true", help="press Enter between turns in a replay"
    )
    return parser


def _ask_players() -> int:
    while True:
        answer = input("How many players? (2 or 4): ").strip()
        if answer in ("2", "4"):
            return int(answer)
        print("Please enter 2 or 4.")


def _ask_minutes() -> float:
    while True:
        answer = input(
            f"Minutes per player (Enter for {DEFAULT_MINUTES}, 0 for no clock): "
        ).strip()
        if not answer:
            return DEFAULT_MINUTES
        try:
            minutes = float(answer)
        except ValueError:
            minutes = -1
        if minutes >= 0:
            return minutes
        print("Please enter a number such as 5, 2.5 or 0.")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # box-drawing characters on Windows
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass

    if args.replay:
        try:
            record = GameRecord.load(args.replay)
            replay(record, delay=args.delay, step=args.step)
        except (OSError, ValueError) as err:
            print(f"Couldn't replay {args.replay}: {err}", file=sys.stderr)
            return 1
        return 0

    try:
        players = args.players or _ask_players()
        minutes = args.minutes if args.minutes is not None else _ask_minutes()
    except (EOFError, KeyboardInterrupt):
        print()
        return 0
    Game(players, minutes).play()
    return 0
