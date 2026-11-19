import contextlib
import io
import json
import os
import tempfile
import unittest

from quoridor import cli
from quoridor.board import Board
from quoridor.history import FORFEIT, MOVE, PASS, WALL, Action, GameRecord
from quoridor.models import Direction, Orientation, Wall
from quoridor.replay import apply_action, replay
from quoridor.report import format_summary, headline, player_stats

H = Orientation.HORIZONTAL


def sample_record():
    return GameRecord(
        num_players=2,
        minutes_per_player=5,
        actions=[
            Action(0, MOVE, direction=Direction.DOWN, seconds=3.5),
            Action(1, WALL, wall=Wall(H, 2, 4), seconds=8.25),
            Action(0, MOVE, direction=Direction.DOWN, seconds=1.0),
            Action(1, MOVE, direction=Direction.UP, seconds=2.0),
        ],
        outcome="abandoned",
    )


class RecordFileTests(unittest.TestCase):
    def test_round_trip_through_a_file(self):
        record = sample_record()
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "game.json")
            record.save(path)
            loaded = GameRecord.load(path)
        self.assertEqual(loaded, record)

    def test_pass_and_forfeit_survive_a_round_trip(self):
        record = GameRecord(4, None, [Action(2, PASS), Action(3, FORFEIT, seconds=301.0)])
        self.assertEqual(GameRecord.from_dict(record.to_dict()), record)

    def test_bad_files_raise_value_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "bad.json")
            for content in ("not json", "[]", json.dumps({"version": 99}),
                            json.dumps({"version": 1, "num_players": 3, "actions": []}),
                            json.dumps({"version": 1, "num_players": 2}),
                            json.dumps({"version": 1, "num_players": 2,
                                        "actions": [{"player": 5, "kind": "pass"}]})):
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(content)
                with self.assertRaises(ValueError, msg=content):
                    GameRecord.load(path)

    def test_missing_file_raises_os_error(self):
        with self.assertRaises(OSError):
            GameRecord.load("/no/such/file.json")


class ReplayTests(unittest.TestCase):
    def test_replay_prints_the_board_after_every_action(self):
        out = []
        replay(sample_record(), output=out.append, delay=0, sleep=lambda s: None)
        text = "\n".join(out)
        self.assertIn("Turn 1 of 4: Player A moves down", text)
        self.assertIn("Turn 2 of 4: Player B places a horizontal wall at row 3, column 5", text)
        self.assertIn("End of replay.", text)
        self.assertEqual(text.count("┌"), 5)  # start position plus one board per action

    def test_replaying_reaches_the_same_final_position(self):
        board = Board(2)
        for action in sample_record().actions:
            apply_action(board, action)
        self.assertEqual(board.positions, [(2, 4), (7, 4)])
        self.assertEqual(board.walls, {Wall(H, 2, 4)})
        self.assertEqual(board.walls_left, [10, 9])

    def test_step_mode_waits_for_enter(self):
        prompts = []
        replay(sample_record(), output=lambda s: None, step=True,
               input_fn=lambda p: prompts.append(p) or "")
        self.assertEqual(len(prompts), 4)

    def test_an_illegal_recording_is_reported(self):
        record = GameRecord(2, None, [Action(0, MOVE, direction=Direction.UP)])
        with self.assertRaises(ValueError):
            replay(record, output=lambda s: None, delay=0, sleep=lambda s: None)


class ReportTests(unittest.TestCase):
    def test_stats_count_steps_walls_and_time(self):
        a, b = player_stats(sample_record())
        self.assertEqual((a.steps, a.walls_placed, a.turns), (2, 0, 2))
        self.assertEqual((b.steps, b.walls_placed, b.turns), (1, 1, 2))
        self.assertEqual((a.walls_left, b.walls_left), (10, 9))
        self.assertAlmostEqual(a.seconds_used, 4.5)

    def test_headlines(self):
        record = sample_record()
        record.outcome, record.winner = "win", 0
        self.assertEqual(
            headline(record),
            "Player A wins by reaching the bottom edge after 2 turns "
            "(2 steps and 0 walls placed).",
        )
        record.outcome, record.winner = "draw", None
        self.assertIn("draw", headline(record))
        record.outcome = "abandoned"
        self.assertIn("abandoned", headline(record))
        record.actions.append(Action(1, FORFEIT))
        record.outcome, record.winner = "timeout", 0
        self.assertIn("Player A wins on time", headline(record))

    def test_summary_contains_a_table_and_totals(self):
        text = format_summary(sample_record())
        self.assertIn("Walls placed", text)
        self.assertIn("Total turns: 4", text)
        self.assertIn("Game time: 0:15", text)  # 14.75 seconds rounds up


class CommandLineTests(unittest.TestCase):
    def test_replay_command(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "game.json")
            sample_record().save(path)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = cli.main(["--replay", path, "--delay", "0"])
        self.assertEqual(code, 0)
        self.assertIn("End of replay.", buffer.getvalue())

    def test_replay_of_a_missing_file_fails_politely(self):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            code = cli.main(["--replay", "/no/such/file.json"])
        self.assertEqual(code, 1)
        self.assertIn("Couldn't replay", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
