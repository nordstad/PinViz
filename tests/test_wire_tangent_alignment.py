"""Unit tests for PathGenerator._align_exit_tangent (kink-free wire->pin joins)."""

from pinviz.layout.routing import PathGenerator
from pinviz.layout.types import LayoutConstants
from pinviz.model import Point


def _gen() -> PathGenerator:
    return PathGenerator(LayoutConstants())


def test_non_five_point_path_is_unchanged():
    """Paths that are not the 5-point curve+lead-in form are returned as-is."""
    pts = [Point(0, 0), Point(5, 5), Point(10, 0)]
    result = _gen()._align_exit_tangent(pts)
    assert result == pts


def test_zero_length_lead_in_is_unchanged():
    """When connection_point == pin (no lead-in direction), ctrl2 is untouched."""
    cp = Point(100, 50)
    ctrl2 = Point(80, 40)
    pts = [Point(0, 0), Point(20, 10), ctrl2, cp, Point(100, 50)]
    result = _gen()._align_exit_tangent(pts)
    assert result[2] == ctrl2  # unchanged


def test_ctrl2_aligned_with_pin_lead_in():
    """ctrl2 becomes collinear with the connection_point -> pin lead-in."""
    p0 = Point(0, 100)
    cp = Point(100, 100)  # connection point
    pin = Point(120, 100)  # pin, straight to the right of cp
    pts = [p0, Point(30, 90), Point(110, 95), cp, pin]

    _gen()._align_exit_tangent(pts)
    ctrl2 = pts[2]

    # Tangent at cp (cp - ctrl2) must be parallel to the lead-in (pin - cp):
    cross = (cp.x - ctrl2.x) * (pin.y - cp.y) - (cp.y - ctrl2.y) * (pin.x - cp.x)
    assert abs(cross) < 1e-6
    # ...and point toward the pin (ctrl2 sits on the far side of cp):
    dot = (cp.x - ctrl2.x) * (pin.x - cp.x) + (cp.y - ctrl2.y) * (pin.y - cp.y)
    assert dot > 0
    # For a horizontal lead-in, ctrl2 stays on the connection-point line:
    assert ctrl2.y == cp.y
    assert ctrl2.x < cp.x
