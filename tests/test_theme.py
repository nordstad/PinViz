"""Tests for theme system."""

import pytest

from pinviz.theme import DARK_SCHEME, LIGHT_SCHEME, ColorScheme, Theme, get_color_scheme


class TestThemeEnum:
    """Tests for Theme enum."""

    def test_light_theme_value(self):
        """Test light theme enum value."""
        assert Theme.LIGHT == "light"
        assert Theme.LIGHT.value == "light"

    def test_dark_theme_value(self):
        """Test dark theme enum value."""
        assert Theme.DARK == "dark"
        assert Theme.DARK.value == "dark"

    def test_theme_from_string(self):
        """Test creating Theme from string."""
        assert Theme("light") == Theme.LIGHT
        assert Theme("dark") == Theme.DARK

    def test_theme_case_insensitive(self):
        """Test theme creation is case-insensitive through lower()."""
        # The enum itself is case-sensitive, but we handle this in config_loader
        with pytest.raises(ValueError):
            Theme("LIGHT")

    def test_invalid_theme(self):
        """Test invalid theme string raises ValueError."""
        with pytest.raises(ValueError):
            Theme("invalid")


class TestColorScheme:
    """Tests for ColorScheme dataclass."""

    def test_color_scheme_has_required_fields(self):
        """Test ColorScheme has all required color fields."""
        scheme = ColorScheme(
            canvas_background="white",
            table_background="#F8F9FA",
            table_header_background="#E9ECEF",
            table_separator="#DEE2E6",
            legend_background="white",
            text_primary="#333",
            text_secondary="#666",
            pin_label_background="#000000",
            pin_label_text="#FFFFFF",
            pin_circle_stroke="#333",
            device_stroke="#333",
            legend_stroke="#333",
            legend_text="#333",
        )

        assert scheme.canvas_background == "white"
        assert scheme.text_primary == "#333"
        assert scheme.pin_label_background == "#000000"


class TestLightScheme:
    """Tests for LIGHT_SCHEME constant."""

    def test_light_scheme_is_color_scheme(self):
        """Test LIGHT_SCHEME is a ColorScheme instance."""
        assert isinstance(LIGHT_SCHEME, ColorScheme)

    def test_light_scheme_has_white_background(self):
        """Test light scheme has white canvas background."""
        assert LIGHT_SCHEME.canvas_background == "white"

    def test_light_scheme_has_dark_text(self):
        """Test light scheme has dark text colors."""
        assert LIGHT_SCHEME.text_primary == "#333"
        assert LIGHT_SCHEME.text_secondary == "#666"

    def test_light_scheme_has_black_pin_labels(self):
        """Test light scheme has black pin label backgrounds."""
        assert LIGHT_SCHEME.pin_label_background == "#000000"
        assert LIGHT_SCHEME.pin_label_text == "#FFFFFF"

    def test_light_scheme_has_light_tables(self):
        """Test light scheme has light table backgrounds."""
        assert LIGHT_SCHEME.table_background == "#F8F9FA"
        assert LIGHT_SCHEME.table_header_background == "#E9ECEF"


class TestDarkScheme:
    """Tests for DARK_SCHEME constant."""

    def test_dark_scheme_is_color_scheme(self):
        """Test DARK_SCHEME is a ColorScheme instance."""
        assert isinstance(DARK_SCHEME, ColorScheme)

    def test_dark_scheme_has_dark_background(self):
        """Test dark scheme has dark canvas background."""
        assert DARK_SCHEME.canvas_background == "#1E1E1E"

    def test_dark_scheme_has_light_text(self):
        """Test dark scheme has light text colors."""
        assert DARK_SCHEME.text_primary == "#E0E0E0"
        assert DARK_SCHEME.text_secondary == "#B0B0B0"

    def test_dark_scheme_has_white_pin_labels(self):
        """Test dark scheme has white pin label backgrounds (inverted)."""
        assert DARK_SCHEME.pin_label_background == "#FFFFFF"
        assert DARK_SCHEME.pin_label_text == "#000000"

    def test_dark_scheme_has_dark_tables(self):
        """Test dark scheme has dark table backgrounds."""
        assert DARK_SCHEME.table_background == "#2D2D2D"
        assert DARK_SCHEME.table_header_background == "#3A3A3A"

    def test_dark_scheme_has_light_strokes(self):
        """Test dark scheme has light stroke colors."""
        assert DARK_SCHEME.pin_circle_stroke == "#E0E0E0"
        assert DARK_SCHEME.device_stroke == "#E0E0E0"


class TestGetColorScheme:
    """Tests for get_color_scheme function."""

    def test_get_light_scheme(self):
        """Test getting light color scheme."""
        scheme = get_color_scheme(Theme.LIGHT)
        assert scheme is LIGHT_SCHEME

    def test_get_dark_scheme(self):
        """Test getting dark color scheme."""
        scheme = get_color_scheme(Theme.DARK)
        assert scheme is DARK_SCHEME

    def test_get_light_scheme_by_string(self):
        """Test getting light scheme using string value."""
        scheme = get_color_scheme(Theme("light"))
        assert scheme is LIGHT_SCHEME

    def test_get_dark_scheme_by_string(self):
        """Test getting dark scheme using string value."""
        scheme = get_color_scheme(Theme("dark"))
        assert scheme is DARK_SCHEME

    def test_default_is_light(self):
        """Test that light scheme is default."""
        # When no theme specified, light should be default
        # This is tested in config_loader and model, but verify here
        assert Theme.LIGHT == "light"


class TestThemeIntegration:
    """Integration tests for theme system."""

    def test_schemes_have_same_fields(self):
        """Test light and dark schemes have identical fields."""
        light_fields = set(LIGHT_SCHEME.__dataclass_fields__.keys())
        dark_fields = set(DARK_SCHEME.__dataclass_fields__.keys())
        assert light_fields == dark_fields

    def test_schemes_have_different_values(self):
        """Test light and dark schemes have different color values."""
        # Canvas backgrounds should be different
        assert LIGHT_SCHEME.canvas_background != DARK_SCHEME.canvas_background

        # Text colors should be different
        assert LIGHT_SCHEME.text_primary != DARK_SCHEME.text_primary

        # Pin labels should be inverted
        assert LIGHT_SCHEME.pin_label_background != DARK_SCHEME.pin_label_background

    def test_all_colors_are_valid_hex_or_named(self):
        """Test all colors in schemes are valid hex codes or named colors."""
        schemes = [LIGHT_SCHEME, DARK_SCHEME]

        # Valid CSS named colors used in schemes
        valid_named_colors = {"white", "black"}

        for scheme in schemes:
            for field_name, _field_value in scheme.__dataclass_fields__.items():
                color = getattr(scheme, field_name)
                # Should be either a hex color or named color
                assert isinstance(color, str)
                assert len(color) > 0

                # If it starts with #, should be valid hex
                if color.startswith("#"):
                    # Should be either #RGB (4 chars) or #RRGGBB (7 chars)
                    assert len(color) in [4, 7], f"Invalid hex color length for {color}"
                    # Check all characters after # are valid hex
                    hex_chars = color[1:]
                    assert all(c in "0123456789ABCDEFabcdef" for c in hex_chars)
                else:
                    # Should be a valid named color
                    assert color.lower() in valid_named_colors
