import unittest

from quoridor.clock import ChessClock, format_time


class FakeTime:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class FormatTimeTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(format_time(300), "5:00")
        self.assertEqual(format_time(65), "1:05")
        self.assertEqual(format_time(59.2), "1:00")  # rounds up, so 0:00 means out
        self.assertEqual(format_time(0), "0:00")
        self.assertEqual(format_time(-5), "0:00")
        self.assertEqual(format_time(None), "no limit")


class ChessClockTests(unittest.TestCase):
    def setUp(self):
        self.time = FakeTime()

    def test_time_only_runs_for_the_player_on_turn(self):
        clock = ChessClock(2, 300, self.time)
        clock.start(0)
        self.time.t = 40
        self.assertEqual(clock.time_left(0), 260)
        self.assertEqual(clock.time_left(1), 300)
        self.assertEqual(clock.stop(), 40)
        self.time.t = 100  # nobody's turn: nothing runs
        self.assertEqual(clock.time_left(0), 260)

    def test_time_accumulates_across_turns(self):
        clock = ChessClock(2, 300, self.time)
        for player, length in ((0, 30), (1, 10), (0, 20)):
            clock.start(player)
            self.time.t += length
            clock.stop()
        self.assertEqual(clock.time_left(0), 250)
        self.assertEqual(clock.time_left(1), 290)
        self.assertEqual(clock.used, [50, 10])

    def test_running_out_of_time(self):
        clock = ChessClock(2, 60, self.time)
        clock.start(1)
        self.time.t = 59
        self.assertFalse(clock.out_of_time(1))
        self.time.t = 60
        self.assertTrue(clock.out_of_time(1))
        self.assertFalse(clock.out_of_time(0))

    def test_unlimited_clock_still_measures_time_used(self):
        clock = ChessClock(2, None, self.time)
        clock.start(0)
        self.time.t = 1000
        self.assertIsNone(clock.time_left(0))
        self.assertFalse(clock.out_of_time(0))
        clock.stop()
        self.assertEqual(clock.used[0], 1000)
        self.assertFalse(clock.enabled)


if __name__ == "__main__":
    unittest.main()
