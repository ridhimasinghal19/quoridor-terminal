import unittest

from quoridor.board import Board
from quoridor.game import Game, parse_wall
from quoridor.history import FORFEIT, MOVE, PASS, WALL
from quoridor.models import Direction, Orientation, Wall


class FakeTime:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def scripted(answers, on_ask=None):
    """An input function that feeds ``answers`` in order."""
    queue = list(answers)

    def ask(prompt):
        if on_ask:
            on_ask()
        if not queue:
            raise AssertionError(f"ran out of scripted input at prompt {prompt!r}")
        return queue.pop(0)

    return ask


def make_game(players, answers, minutes=None, now=None, on_ask=None):
    out = []
    kwargs = {"now": now} if now else {}
    game = Game(
        players,
        minutes,
        input_fn=scripted(answers, on_ask),
        output_fn=out.append,
        show_intro=False,
        offer_extras=False,
        **kwargs,
    )
    return game, out


class ParseWallTests(unittest.TestCase):
    def test_valid_input(self):
        self.assertEqual(parse_wall("h 3 5"), Wall(Orientation.HORIZONTAL, 2, 4))
        self.assertEqual(parse_wall("v 1 8"), Wall(Orientation.VERTICAL, 0, 7))
        self.assertEqual(parse_wall("horizontal 2 2"), Wall(Orientation.HORIZONTAL, 1, 1))
        self.assertEqual(parse_wall("v, 4, 6"), Wall(Orientation.VERTICAL, 3, 5))

    def test_garbage_is_rejected(self):
        for text in ("", "h", "h 3", "x 3 5", "h a b", "h 3 5 7", "3 5 h"):
            self.assertIsNone(parse_wall(text), text)


class TwoPlayerGameTests(unittest.TestCase):
    def test_a_full_game_to_a_win(self):
        # A walks straight down column 5; B steps aside once, then walks up.
        answers = []
        for i in range(8):
            answers.append("2")
            if i < 7:
                answers.append("3" if i == 0 else "1")
        game, out = make_game(2, answers)
        record = game.play()

        self.assertEqual(record.outcome, "win")
        self.assertEqual(record.winner, 0)
        self.assertEqual(len(record.actions), 15)
        text = "\n".join(out)
        self.assertIn("Player A wins by reaching the bottom edge after 8 turns", text)
        self.assertIn("(8 steps and 0 walls placed)", text)

    def test_bad_input_and_illegal_moves_are_reported_and_retried(self):
        answers = ["x", "", "1", "2", "q", "n", "q", "y"]
        game, out = make_game(2, answers)
        record = game.play()
        text = "\n".join(out)
        self.assertIn("Please enter a number from 1 to 5", text)
        self.assertIn("You can't move off the board.", text)
        self.assertEqual(record.outcome, "abandoned")
        self.assertEqual([a.kind for a in record.actions], [MOVE])  # only "2" counted

    def test_walls_are_validated_and_recorded(self):
        # "5" opens the wall prompt; "nonsense" is rejected and "b" goes back.
        # Then a wall off the board is rejected before "h 3 3" is accepted.
        answers = ["5", "nonsense", "b", "5", "h 9 9", "h 3 3", "q", "y"]
        game, out = make_game(2, answers)
        record = game.play()
        text = "\n".join(out)
        self.assertIn("Enter orientation, row and column", text)
        self.assertIn("That wall doesn't fit on the board.", text)
        wall_actions = [a for a in record.actions if a.kind == WALL]
        self.assertEqual(len(wall_actions), 1)
        self.assertEqual(wall_actions[0].wall, Wall(Orientation.HORIZONTAL, 2, 2))
        self.assertEqual(game.board.walls_left[0], 9)

    def test_a_wall_that_traps_someone_is_refused_in_play(self):
        game, out = make_game(2, ["5", "v 8 7", "b", "q", "y"])
        game.board.positions[1] = (8, 8)
        game.board.walls.add(Wall(Orientation.HORIZONTAL, 7, 7))  # roof over B's corner
        game.turn = 1
        record = game.play()
        self.assertIn("no route to their goal", "\n".join(out))
        self.assertFalse([a for a in record.actions if a.kind == WALL])

    def test_running_out_of_time_loses_a_two_player_game(self):
        fake = FakeTime()
        calls = {"n": 0}

        def burn_time():
            calls["n"] += 1
            if calls["n"] == 1:
                fake.t += 400  # more than the 5-minute bank

        game, out = make_game(2, ["2"], minutes=5, now=fake, on_ask=burn_time)
        record = game.play()
        self.assertEqual(record.outcome, "timeout")
        self.assertEqual(record.winner, 1)
        self.assertEqual(record.actions[0].kind, FORFEIT)
        self.assertIn("Player B wins on time", "\n".join(out))
        self.assertEqual(game.board.positions[0], (0, 4))  # the late move never happened

    def test_the_clock_is_shown_when_enabled(self):
        game, out = make_game(2, ["q", "y"], minutes=2.5)
        game.play()
        self.assertIn("Clocks: A 2:30   B 2:30", "\n".join(out))

    def test_no_clock_line_without_a_clock(self):
        game, out = make_game(2, ["q", "y"], minutes=0)
        game.play()
        self.assertNotIn("Clocks:", "\n".join(out))

    def test_stuck_players_are_skipped_and_a_full_deadlock_is_a_draw(self):
        game, out = make_game(2, [])
        board = game.board
        board.positions = [(0, 0), (0, 1)]
        board.walls_left = [0, 0]
        board.walls = {Wall(Orientation.HORIZONTAL, 0, 0), Wall(Orientation.VERTICAL, 0, 1)}
        record = game.play()
        self.assertEqual(record.outcome, "draw")
        self.assertEqual([a.kind for a in record.actions], [PASS, PASS])

    def test_a_stuck_player_passes_while_the_other_can_still_move(self):
        game, out = make_game(2, ["4", "q", "y"])
        board = game.board
        board.positions = [(0, 0), (0, 1)]
        board.walls_left = [0, 0]
        board.walls = {Wall(Orientation.HORIZONTAL, 0, 0)}
        record = game.play()
        self.assertEqual(record.actions[0].kind, PASS)
        self.assertEqual(record.actions[0].player, 0)
        self.assertEqual(record.actions[1].kind, MOVE)
        self.assertEqual(record.actions[1].player, 1)

    def test_closing_the_input_ends_the_game_cleanly(self):
        def closed(prompt):
            raise EOFError

        out = []
        game = Game(2, input_fn=closed, output_fn=out.append, show_intro=False)
        record = game.play()
        self.assertEqual(record.outcome, "abandoned")


class FourPlayerGameTests(unittest.TestCase):
    def test_a_full_game_won_by_player_b_on_the_left_edge(self):
        a_moves = ["4", "4", "4", "4", "3", "3", "3", "3"]
        c_moves = ["4", "4", "4", "4", "3", "3", "3"]
        d_moves = ["1", "1", "1", "1", "2", "2", "2"]
        answers = []
        for i in range(8):
            answers.append(a_moves[i])
            answers.append("3")  # B walks left along the middle row
            if i < 7:
                answers.append(c_moves[i])
                answers.append(d_moves[i])
        game, out = make_game(4, answers)
        record = game.play()
        self.assertEqual(record.outcome, "win")
        self.assertEqual(record.winner, 1)
        self.assertIn("Player B wins by reaching the left edge after 8 turns", "\n".join(out))

    def test_a_player_who_runs_out_of_time_leaves_and_the_game_goes_on(self):
        fake = FakeTime()
        calls = {"n": 0}

        def burn_time():
            calls["n"] += 1
            if calls["n"] == 1:
                fake.t += 400

        game, out = make_game(4, ["2", "q", "y"], minutes=5, now=fake, on_ask=burn_time)
        record = game.play()
        self.assertEqual(record.actions[0].kind, FORFEIT)
        self.assertEqual(game.board.eliminated, {0})
        self.assertEqual(record.outcome, "abandoned")  # B then quit
        after = "\n".join(out).split("is out of the game.")[1]
        self.assertIn("Clocks: B 5:00   C 5:00   D 5:00", after)

    def test_eliminated_players_are_skipped_in_the_turn_order(self):
        game, out = make_game(4, ["4", "4", "q", "y"])
        game.board.eliminate(1)
        record = game.play()
        self.assertEqual([a.player for a in record.actions], [0, 2])


if __name__ == "__main__":
    unittest.main()
