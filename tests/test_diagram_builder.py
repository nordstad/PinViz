"""Tests for the shared diagram builder."""

import pytest

from pinviz.diagram_builder import DiagramBuilder


def test_diagram_builder_requires_board_before_build():
    """Builder should reject incomplete diagrams without a resolved board."""
    builder = DiagramBuilder()

    with pytest.raises(ValueError, match="requires a board"):
        builder.build()
