"""
Some simple tests.
"""
from collections import Counter
import logging
from sudoku import solve
import unittest

logging.basicConfig(level=logging.INFO)

PUZZLES = [
    [
        "7...4....",
        "6..1...4.",
        "..37...8.",
        "..2.....6",
        "96.....28",
        "3.....1..",
        ".8...29..",
        ".9...8..3",
        "....7...1",
    ],
    [
        "..7....4.",
        ".3.6..2.5",
        "8.9.7....",
        "....1....",
        "...3.8...",
        "..8.9.4..",
        "......5..",
        ".1...6.3.",
        "9.4.3.1.7",
    ],
    [
        ".4..3..7.",
        "3....8..2",
        "...9.5...",
        ".52...7..",
        "6.......8",
        "..8...19.",
        "...6.1...",
        "2..4....3",
        ".8..7..5.",
    ],
    [
        "....7..8.",
        ".185.....",
        "...9...75",
        "..38..79.",
        ".8.....1.",
        ".57..34..",
        "49...2...",
        ".....562.",
        ".3..1....",
    ],
]

class TestSolve(unittest.TestCase):
    """ Solve test cases. """

    @classmethod
    def str_to_board(cls, puzzle):
        """ Convert string sudoku to a board. """
        return [[int(value) if value != '.' else None for value in row]
                for row in puzzle]

    def assert_digits(self, digits, times):
        """ Check that digits 1-9 appear times times. """
        self.assertEqual(range(1, 10), sorted(digits.keys()),
                         "Must have digits [1, 9] inclusive")
        self.assertEqual([times] * 9, digits.values(),
                         "Digits [1, 9] inclusive did not appear expected number of times")

    def check_valid_solution(self, solution):
        """ Check sudoku row, column, and block invariants. """
        # Check each digit 1-9 appears exactly 9 times.
        digits = Counter(value for row in solution for value in row)
        self.assert_digits(digits, 9)
        # Check blocks have 1-9.
        block_slices = (slice(0, 3), slice(3, 6), slice(6, 9))
        for row_slice in block_slices:
            rows = solution[row_slice]
            for col_slice in block_slices:
                digits = Counter(value for row in rows for value in row[col_slice])
                self.assert_digits(digits, 1)
        # Check rows have 1-9.
        for row in solution:
            digits = Counter(value for value in row)
            self.assert_digits(digits, 1)
        # Check cols have 1-9.
        for col in xrange(9):
            digits = Counter(row[col] for row in solution)
            self.assert_digits(digits, 1)

    def test_solve(self):
        """ Solve puzzles with no exceptions. """
        for i, puzzle in enumerate(PUZZLES):
            solution = solve(self.str_to_board(puzzle))
            self.check_valid_solution(solution)

    def test_bad_puzzle(self):
        """ Solve a bad puzzle and expect an exception. """
        bad_puzzle = [
            "1.....1..",
            ".........",
            ".........",
            ".........",
            ".........",
            ".........",
            ".........",
            ".........",
            ".........",
        ]
        try:
            solution = solve(self.str_to_board(bad_puzzle))
        except ValueError as error:
            self.assertTrue('unsolvable' in error.message,
                            "Expecting \'unsolvable\' error")


if __name__ == '__main__':
    unittest.main()
