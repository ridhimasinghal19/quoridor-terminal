"""A chess-style clock: each player has a time bank that only runs on their turn."""
from __future__ import annotations

import time
from typing import Callable, List, Optional, Tuple


def format_time(seconds: Optional[float]) -> str:
    """Format as m:ss, or 'no limit' when the clock is switched off."""
    if seconds is None:
        return "no limit"
    seconds = max(0, int(seconds + 0.999))  # round up so 0:00 really means out of time
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}:{secs:02d}"


class ChessClock:
    """Tracks time per player.

    ``seconds_per_player=None`` disables the limit; time used is still measured
    so it can be reported in the game summary. ``now`` is injectable for tests.
    """

    def __init__(
        self,
        num_players: int,
        seconds_per_player: Optional[float] = None,
        now: Callable[[], float] = time.monotonic,
    ):
        self.enabled = seconds_per_player is not None
        self._left: List[Optional[float]] = [seconds_per_player] * num_players
        self.used: List[float] = [0.0] * num_players
        self._now = now
        self._running: Optional[Tuple[int, float]] = None

    def start(self, player: int) -> None:
        self._running = (player, self._now())

    def elapsed(self) -> float:
        """Seconds since the current turn started."""
        if self._running is None:
            return 0.0
        return self._now() - self._running[1]

    def time_left(self, player: int) -> Optional[float]:
        """Seconds remaining (including the turn in progress), or None if unlimited."""
        left = self._left[player]
        if left is None:
            return None
        if self._running is not None and self._running[0] == player:
            left -= self.elapsed()
        return left

    def out_of_time(self, player: int) -> bool:
        left = self.time_left(player)
        return left is not None and left <= 0

    def stop(self) -> float:
        """End the running turn, charge it to the player, return its length."""
        if self._running is None:
            return 0.0
        player, _ = self._running
        spent = self.elapsed()
        self.used[player] += spent
        if self._left[player] is not None:
            self._left[player] -= spent
        self._running = None
        return spent
