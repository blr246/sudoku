"""
A sudoku game solver.

(c) 2015 Brandon L. Reiss
"""
from collections import Counter
from copy import copy, deepcopy
from itertools import ifilter
import logging
from random import shuffle, randint

LOGGER = logging.getLogger(__name__)


def format_board(board):
    """
    Pretty format a board.

    ###########################################
    #|---+---+---|#|---+---+---|#|---+---+---|#
    #|123|12 |1  |#|123|12 |1  |#|123|12 |1  |#
    #|456| 5 |4  |#|456| 5 |4  |#|456| 5 |4  |#
    #|789|7  | 8 |#|789|7  | 8 |#|789|7  | 8 |#
    #|---+---+---|#|---+---+---|#|---+---+---|#
    ...
    #|---+---+---|#|---+---+---|#|---+---+---|#
    ###########################################
    #|---+---+---|#|---+---+---|#|---+---+---|#
    ...
    ###########################################

    Each 3x3 block is outlined by '#' and each value is outlined by '|-+'.

    :return list: list of strings representing lines of the formatted board
    """

    def outer_border_row():
        return "###########################################"

    def inner_border_row():
        return "#|---+---+---|#|---+---+---|#|---+---+---|#"

    def format_row(row):

        fmt_rows = []

        # Generate rows for grid values 123, 456, 789.
        for val_div in xrange(3):
            # Generate strings of either space or matched possible values for
            # every cell in the row for this subset of possible values 1-9.
            possible_vals = range((3 * val_div) + 1, (3 * val_div) + 4)
            row_vals = [
                ''.join(str(pval) if pval in values else ' '
                        for pval in possible_vals)
                for values in row]


            # Loop over the 3 3x3 block sections.
            by_block = []
            for blk_idx in xrange(3):
                block_expanded = '|'.join(row_vals[3 * blk_idx:(3 * blk_idx) + 3])
                by_block.append('|{}|'.format(block_expanded))
            fmt_rows.append('#{}#'.format('#'.join(by_block)))

        return fmt_rows

    rows = [outer_border_row()]
    # Loop over the 3 3x3 block sections.
    for block_div in xrange(3):
        rows.append(inner_border_row())
        for row in board[3 * block_div:(3 * block_div) + 3]:
            rows.extend(format_row(row))
            rows.append(inner_border_row())
        rows.append(outer_border_row())

    return rows

def solve(initial_board):

    def _check_elim_row_col(select_pred, counts, iter_rc):

        for i, counted in enumerate(counts):
            selected_values = set(next(iter(board[sel_i][sel_j]))
                                  for sel_i, sel_j in selected
                                  if select_pred(sel_i, sel_j, i))
            unique_values = set(val
                                for val, count in counted.iteritems()
                                if count == 1)
            unique_not_selected = unique_values - selected_values

            # Select the first unique-but-not-yet-selected value.
            if len(unique_not_selected) > 0:
                value = next(iter(unique_not_selected))
                j = next(idx
                         for idx, values in enumerate(iter_rc(board, i))
                         if value in values)
                return (i, j), value

        return None, None

    def check_elim_row(row_counts):
        return _check_elim_row_col(lambda sel_i, _, i: i == sel_i,
                                   row_counts,
                                   lambda board, i: iter(board[i]))

    def check_elim_col(col_counts):
        return _check_elim_row_col(lambda _, sel_j, j: j == sel_j,
                                   col_counts,
                                   lambda board, j: (row[j] for row in board))

    def board_is_valid(board, row_counts, col_counts):
        """
        Look for
          - any space that has zero possible values
          - any row where at least one value in [1, 9] is impossible
          - any column where at least one value in [1, 9] is impossible

        :returns: True when the board is valid and False otherwise
        """

        empty_space = next((True
                            for row in board
                            for values in row
                            if len(values) == 0), False)
        if empty_space:
            return False

        empty_count = lambda counts: any(count == 0 for count in counts.itervalues())

        empty_row_count = next((True
                                for counts in row_counts
                                if empty_count(counts)), False)
        if empty_row_count:
            return False

        empty_col_count = next((True
                                for counts in col_counts
                                if empty_count(counts)), False)
        if empty_col_count:
            return False

        return True

    def set_value(board, value, i, j, row_counts, col_counts):
        """
        Set value (i, j) within the board. Values must be eliminated within the
        local 3x3 block as well as down the row and column.
        """

        # Get 3x3 block address.
        block_i = i / 3
        block_j = j / 3

        # Eliminate value from block.
        for my_i, row in enumerate(board[3 * block_i:(3 * block_i) + 3], 3 * block_i):
            for my_j, values in enumerate(row[3 * block_j:(3 * block_j) + 3], 3 * block_j):
                if value in values:
                    values.remove(value)
                    row_counts[my_i][value] -= 1
                    col_counts[my_j][value] -= 1

        # Eliminate value from row.
        for my_j, values in enumerate(board[i]):
            if value in values:
                values.discard(value)
                row_counts[i][value] -= 1
                col_counts[my_j][value] -= 1

        # Eliminate value from column.
        for my_i, values in enumerate(row[j] for row in board):
            if value in values:
                values.discard(value)
                row_counts[my_i][value] -= 1
                col_counts[j][value] -= 1

        # Set the value.
        row_counts[i][value] = 1
        col_counts[j][value] = 1
        for discard_value in board[i][j]:
            row_counts[i][discard_value] -= 1
            col_counts[j][discard_value] -= 1
        board[i][j] = set((value,))

    move_type_elim, \
        move_type_row_elim, \
        move_type_col_elim, \
        move_type_guess = range(4)
    move_type_to_str = {
        move_type_elim : "elimination",
        move_type_row_elim : "row elimination",
        move_type_col_elim : "col elimination",
        move_type_guess : "guess",
    }

    board = [[set(xrange(1, 10)) for _ in xrange(9)] for _ in xrange(9)]
    row_counts = [Counter(v for values in row for v in values)
                  for row in board]
    col_counts = [Counter(v for row in board for v in row[j])
                  for j in xrange(9)]
    selected = set()

    for i, j, value in ((i, j, value)
                        for i, row in enumerate(initial_board)
                        for j, value in enumerate(row)
                        if value is not None):
        #print "Setting ({}, {}) = {}".format(i, j, value)
        set_value(board, value, i, j, row_counts, col_counts)
        selected.add((i,j))
        #print '\n'.join(format_board(board))

    num_set_initially = len(selected)

    #print 'Initial board:'
    #print '\n'.join(format_board(board))
    #raw_input("Continue...")
    #print 'num_set_initially:', num_set_initially

    failed_guesses = 0
    longest_discarded_moves = 0
    move_counter = 0
    board_stack = []
    while True:

        # Check whether or not the board is still valid.
        if not board_is_valid(board, row_counts, col_counts):
            # If we didn't guess previously, then this board is no good.
            if len(board_stack) == 0:
                raise ValueError("Puzzle is invalid and therefore unsolvable.\n"
                                 '\n'.join(format_board(board)))

            failed_guesses += 1

            # Pop the board state and update the counts.
            move_count, board, selected = board_stack.pop()
            row_counts = [Counter(v for values in row for v in values)
                          for row in board]
            col_counts = [Counter(v for row in board for v in row[j])
                          for j in xrange(9)]
            discarded_moves = move_counter - move_count
            longest_discarded_moves = max(discarded_moves, longest_discarded_moves)

            #print "Guess after move {} failed after {} moves".format(
            #    move_count, discarded_moves)

            #print '\n'.join(format_board(board))
            #raw_input("Continue...")

        # All done?
        if len(selected) == 81:
            break

        next_move = None

        # Check for naive unique value (only remaining choice).
        try:
            i, j = next(((i, j)
                         for i, row in enumerate(board)
                         for j, values in enumerate(row)
                         if len(values) == 1
                         and (i, j) not in selected))
            next_move = (i, j), next(iter(board[i][j])), move_type_elim
        except StopIteration:
            pass

        # Check for unique value within a row.
        if next_move is None:
            ij_pre, value = check_elim_row(row_counts)
            if ij_pre is not None:
                i, j = ij_pre
                next_move = (i, j), value, move_type_row_elim

        # Check for unique value within a column.
        if next_move is None:
            ji_pre, value = check_elim_col(col_counts)
            if ji_pre is not None:
                j, i = ji_pre
                next_move = (i, j), value, move_type_col_elim

        # See if we must guess. All forced moves are exhausted here.
        if next_move is None:

            # Find a good place to guess.
            count_values = [(len(values),
                             i, j)
                            for i, row in enumerate(board)
                            for j, values in enumerate(row)
                            if len(values) > 1]
            min_remaining, _, _ = min(count_values)
            min_values = [(i, j)
                          for count, i, j in count_values
                          if count == min_remaining]

            # Get a random guess location with the min possible values
            # remaining.
            i, j = min_values[randint(0, len(min_values) - 1)]

            # Guess and push the world.
            value = next(iter(board[i][j]))
            board_copy, selected_copy = deepcopy(board), copy(selected)
            board_copy[i][j].discard(value)
            board_stack.append((move_counter, board_copy, selected_copy))
            next_move = (i, j), value, move_type_guess

            #print '\n'.join(format_board(board))
            #raw_input("Continue...")

        # We must have found a move by now since the board is valid and we can
        # guess.
        (i, j), value, move_type = next_move
        move_counter += 1
        #print '{:3d} : Picked ({},{}) = {} ({})'.format(
        #    move_counter, i, j, value, move_type_to_str[move_type])
        set_value(board, value, i, j, row_counts, col_counts)
        selected.add((i, j))

        #print '\n'.join(format_board(board))
        #raw_input("Continue...")

    moves_to_solve_directly = 81 - num_set_initially
    LOGGER.info("Solved after {} moves with {} discarded from {} failed guesses".format(
                move_counter, move_counter - moves_to_solve_directly, failed_guesses))
    LOGGER.info("Longest discarded move sequence: {}".format(longest_discarded_moves))

    return [[next(iter(values)) for values in row] for row in board]
