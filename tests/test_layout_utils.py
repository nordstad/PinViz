"""Tests for layout utility helpers."""

from pinviz.layout.utils import create_bezier_path
from pinviz.model import Point


def test_create_bezier_path_many_points_skips_consumed_targets():
    """Paths with many points should not duplicate intermediate segments."""
    points = [Point(float(i), float(i)) for i in range(6)]

    path = create_bezier_path(points)

    # M + three Q commands (1->2, 3->4, and final approach to point 5)
    assert path.count(" Q ") == 3
    assert path.startswith("M 0.00,0.00")
    assert path.endswith("5.00,5.00")
