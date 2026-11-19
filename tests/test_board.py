import unittest

from quoridor.board import Board, InvalidMove, InvalidWall
from quoridor.models import Direction, Orientation, Wall

H = Orientation.HORIZONTAL
V = Orientation.VERTICAL


class StartingPositionTests(unittest.TestCase):
    def test_two_player_layout(self):
        board = Board(2)
        self.assertEqual(board.positions, [(0, 4), (8, 4)])
        self.assertEqual(board.walls_left, [10, 10])

    def test_four_player_layout_is_clockwise_from_the_top(self):
        board = Board(4)
        self.assertEqual(board.positions, [(0, 4), (4, 8), (8, 4), (4, 0)])
        self.assertEqual(board.walls_left, [5, 5, 5, 5])

    def test_only_two_or_four_players(self):
        with self.assertRaises(ValueError):
            Board(3)


class WinningTests(unittest.TestCase):
    def test_each_player_wins_on_the_opposite_edge(self):
        board = Board(4)
        goals = [(8, 2), (3, 0), (0, 6), (5, 8)]
        for player, cell in enumerate(goals):
            self.assertFalse(board.has_won(player))
            board.positions[player] = cell
            self.assertTrue(board.has_won(player), f"player {player} at {cell}")

    def test_two_player_goals(self):
        board = Board(2)
        board.positions = [(8, 0), (0, 8)]
        self.assertTrue(board.has_won(0))
        self.assertTrue(board.has_won(1))

    def test_an_eliminated_player_cannot_win(self):
        board = Board(2)
        board.positions[0] = (8, 4)
        board.eliminate(0)
        self.assertFalse(board.has_won(0))


class MovementTests(unittest.TestCase):
    def test_a_legal_move_changes_position(self):
        board = Board(2)
        board.move(0, Direction.DOWN)
        self.assertEqual(board.positions[0], (1, 4))

    def test_cannot_leave_the_board(self):
        board = Board(2)
        with self.assertRaises(InvalidMove):
            board.move(0, Direction.UP)
        self.assertEqual(board.positions[0], (0, 4))

    def test_cannot_walk_through_a_wall(self):
        board = Board(2)
        board.place_wall(1, Wall(H, 0, 3))  # below (0,3) and (0,4)
        with self.assertRaises(InvalidMove):
            board.move(0, Direction.DOWN)
        board.move(0, Direction.RIGHT)  # (0,5) is free of the wall
        board.move(0, Direction.DOWN)

    def test_vertical_wall_blocks_both_cells_it_touches(self):
        board = Board(2)
        board.positions[0] = (3, 3)
        board.place_wall(0, Wall(V, 3, 3))  # right of (3,3) and (4,3)
        with self.assertRaises(InvalidMove):
            board.move(0, Direction.RIGHT)
        board.positions[0] = (4, 4)
        with self.assertRaises(InvalidMove):
            board.move(0, Direction.LEFT)
        board.positions[0] = (5, 3)
        board.move(0, Direction.RIGHT)

    def test_cannot_move_onto_another_pawn(self):
        board = Board(2)
        board.positions = [(3, 3), (3, 4)]
        with self.assertRaises(InvalidMove):
            board.move(0, Direction.RIGHT)

    def test_legal_moves_at_the_start(self):
        board = Board(2)
        self.assertCountEqual(
            board.legal_moves(0), [Direction.DOWN, Direction.LEFT, Direction.RIGHT]
        )

    def test_eliminated_pawns_stop_blocking(self):
        board = Board(2)
        board.positions = [(3, 3), (3, 4)]
        board.eliminate(1)
        board.move(0, Direction.RIGHT)


class WallPlacementTests(unittest.TestCase):
    def test_placing_a_wall_uses_one_of_the_players_walls(self):
        board = Board(2)
        board.place_wall(0, Wall(H, 3, 3))
        self.assertEqual(board.walls_left, [9, 10])

    def test_walls_must_fit_on_the_board_and_off_the_edge(self):
        board = Board(2)
        for wall in (Wall(H, 8, 0), Wall(H, 0, 8), Wall(V, -1, 0), Wall(V, 0, 8)):
            with self.assertRaises(InvalidWall, msg=str(wall)):
                board.place_wall(0, wall)
        board.place_wall(0, Wall(H, 7, 7))  # the furthest legal corner

    def test_overlapping_walls_are_rejected(self):
        board = Board(2)
        board.place_wall(0, Wall(H, 3, 3))
        for wall in (Wall(H, 3, 3), Wall(H, 3, 2), Wall(H, 3, 4)):
            with self.assertRaises(InvalidWall, msg=str(wall)):
                board.place_wall(0, wall)
        board.place_wall(0, Wall(V, 5, 3))
        for wall in (Wall(V, 5, 3), Wall(V, 4, 3), Wall(V, 6, 3)):
            with self.assertRaises(InvalidWall, msg=str(wall)):
                board.place_wall(0, wall)

    def test_crossing_walls_are_rejected_in_both_orders(self):
        board = Board(2)
        board.place_wall(0, Wall(H, 3, 3))
        with self.assertRaises(InvalidWall):
            board.place_wall(0, Wall(V, 3, 3))
        board = Board(2)
        board.place_wall(0, Wall(V, 3, 3))
        with self.assertRaises(InvalidWall):
            board.place_wall(0, Wall(H, 3, 3))

    def test_corners_and_t_shapes_are_allowed(self):
        board = Board(2)
        board.place_wall(0, Wall(H, 3, 3))
        board.place_wall(0, Wall(H, 3, 5))  # end to end
        board.place_wall(0, Wall(V, 4, 3))  # T shape under the first wall
        board.place_wall(0, Wall(V, 2, 4))  # touches at a corner
        self.assertEqual(len(board.walls), 4)

    def test_a_failed_placement_costs_nothing(self):
        board = Board(2)
        with self.assertRaises(InvalidWall):
            board.place_wall(0, Wall(H, 8, 8))
        self.assertEqual(board.walls_left, [10, 10])
        self.assertEqual(board.walls, set())

    def test_no_walls_left(self):
        board = Board(2)
        board.walls_left[0] = 0
        with self.assertRaises(InvalidWall):
            board.place_wall(0, Wall(H, 3, 3))


class PathBlockingRuleTests(unittest.TestCase):
    def test_a_wall_that_seals_a_player_into_a_pocket_is_refused(self):
        board = Board(2)
        board.positions[0] = (0, 0)
        board.place_wall(1, Wall(H, 0, 0))  # under (0,0) and (0,1)
        # Closing the right side would leave a two-cell pocket: the pawn could
        # still shuffle about, but could never reach the bottom edge.
        message = board.wall_error(1, Wall(V, 0, 1))
        self.assertIsNotNone(message)
        self.assertIn("no route", message)
        with self.assertRaises(InvalidWall):
            board.place_wall(1, Wall(V, 0, 1))
        self.assertNotIn(Wall(V, 0, 1), board.walls)

    def test_a_wall_that_leaves_a_detour_is_allowed(self):
        board = Board(2)
        board.positions[0] = (0, 0)
        board.place_wall(1, Wall(H, 0, 0))
        self.assertIsNone(board.wall_error(1, Wall(V, 0, 2)))

    def test_the_rule_protects_the_player_placing_the_wall_as_well(self):
        board = Board(2)
        board.positions[1] = (8, 8)
        board.place_wall(1, Wall(H, 7, 7))  # roof over (8,7) and (8,8)
        message = board.wall_error(1, Wall(V, 7, 6))  # would seal their own pocket
        self.assertIsNotNone(message)
        self.assertIn("player B", message)

    def test_pawns_do_not_count_as_blockers(self):
        board = Board(2)
        board.positions = [(0, 0), (1, 0)]
        board.place_wall(1, Wall(V, 0, 0))  # A's only way out is through B's cell
        self.assertIsNone(board.wall_error(1, Wall(H, 5, 5)))

    def test_eliminated_players_need_no_route(self):
        board = Board(2)
        board.positions[0] = (0, 0)
        board.place_wall(1, Wall(H, 0, 0))
        board.eliminate(0)
        self.assertIsNone(board.wall_error(1, Wall(V, 0, 1)))

    def test_distance_to_goal_grows_with_walls(self):
        board = Board(2)
        self.assertEqual(board.distance_to_goal(0), 8)
        self.assertEqual(board.distance_to_goal(1), 8)
        board.place_wall(1, Wall(H, 0, 3))  # forces a step sideways first
        self.assertEqual(board.distance_to_goal(0), 9)


class RenderTests(unittest.TestCase):
    def test_dimensions_and_pawns(self):
        lines = Board(2).render().split("\n")
        self.assertEqual(len(lines), 20)
        self.assertIn(" A ", lines[2])
        self.assertIn(" B ", lines[18])

    def test_walls_are_drawn_where_they_stand(self):
        board = Board(2)
        board.place_wall(0, Wall(H, 3, 4))  # under row 4, columns 5-6
        board.place_wall(0, Wall(V, 0, 0))  # right of column 1, rows 1-2
        lines = board.render().split("\n")
        self.assertIn("═══════", lines[9])  # separator between rows 4 and 5
        self.assertIn("║", lines[2])
        self.assertIn("║", lines[3])
        self.assertIn("║", lines[4])

    def test_eliminated_pawns_disappear(self):
        board = Board(2)
        board.eliminate(1)
        self.assertNotIn("B", board.render())


if __name__ == "__main__":
    unittest.main()
