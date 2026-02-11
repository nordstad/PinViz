"""Tests for color utility functions."""

from pinviz.color_utils import resolve_color


def test_named_color_conversion():
    """Test that named colors convert to hex."""
    assert resolve_color("red") == "#FF0000"
    assert resolve_color("RED") == "#FF0000"
    assert resolve_color("green") == "#00FF00"
    assert resolve_color("blue") == "#0000FF"


def test_hex_passthrough():
    """Test that valid hex codes pass through unchanged."""
    assert resolve_color("#FF0000") == "#FF0000"
    assert resolve_color("#ff0000") == "#ff0000"
    assert resolve_color("#00FF00") == "#00FF00"
    assert resolve_color("#ABCDEF") == "#ABCDEF"


def test_invalid_color_fallback():
    """Test fallback for invalid colors."""
    assert resolve_color("notacolor") == "#4A90E2"
    assert resolve_color("notacolor", "#123456") == "#123456"
    assert resolve_color("invalid", "#FFFFFF") == "#FFFFFF"


def test_none_fallback():
    """Test None handling."""
    assert resolve_color(None) == "#4A90E2"
    assert resolve_color(None, "#ABCDEF") == "#ABCDEF"


def test_all_wirecolor_names():
    """Test all 15 WireColor enum values."""
    expected = {
        "red": "#FF0000",
        "black": "#000000",
        "white": "#FFFFFF",
        "green": "#00FF00",
        "blue": "#0000FF",
        "yellow": "#FFFF00",
        "orange": "#FF8C00",
        "purple": "#9370DB",
        "gray": "#808080",
        "brown": "#8B4513",
        "pink": "#FF69B4",
        "cyan": "#00CED1",
        "magenta": "#FF00FF",
        "lime": "#32CD32",
        "turquoise": "#40E0D0",
    }
    for name, hex_code in expected.items():
        assert resolve_color(name) == hex_code
        # Test case insensitivity
        assert resolve_color(name.upper()) == hex_code


def test_case_insensitivity():
    """Test that color names are case-insensitive."""
    assert resolve_color("Red") == "#FF0000"
    assert resolve_color("rEd") == "#FF0000"
    assert resolve_color("GREEN") == "#00FF00"
    assert resolve_color("GrEeN") == "#00FF00"


def test_invalid_hex_formats():
    """Test that invalid hex formats fall back to default."""
    # Missing #
    assert resolve_color("FF0000") == "#4A90E2"
    # Too short
    assert resolve_color("#FFF") == "#4A90E2"
    # Too long
    assert resolve_color("#FF00001") == "#4A90E2"
    # Invalid characters
    assert resolve_color("#GGGGGG") == "#4A90E2"
    assert resolve_color("#FF00GG") == "#4A90E2"


def test_empty_string():
    """Test that empty string falls back to default."""
    assert resolve_color("") == "#4A90E2"
    assert resolve_color("", "#111111") == "#111111"


def test_whitespace_handling():
    """Test that leading/trailing whitespace is trimmed."""
    assert resolve_color("  red  ") == "#FF0000"
    assert resolve_color("\tgreen\n") == "#00FF00"
    assert resolve_color("  #FF0000  ") == "#FF0000"
    assert resolve_color(" BLUE ") == "#0000FF"
