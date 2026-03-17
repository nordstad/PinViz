"""Tests for board selection strategies."""

import pytest

from pinviz.board_selection import AliasBoardSelectionStrategy


def test_alias_board_selection_unknown_board_raises_value_error():
    """Unknown boards should fail when no fallback is configured."""
    strategy = AliasBoardSelectionStrategy()

    with pytest.raises(ValueError, match="Unknown board: mystery_board"):
        strategy.select_board("mystery_board")
