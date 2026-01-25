"""Tests for wire halo color luminance detection."""

import pytest

from pinviz.render_constants import RENDER_CONSTANTS
from pinviz.wire_renderer import calculate_luminance, get_halo_color


class TestLuminanceCalculation:
    """Test luminance calculation for various colors."""

    def test_pure_black_luminance(self):
        """Pure black should have 0.0 luminance."""
        assert calculate_luminance("#000000") == pytest.approx(0.0, abs=0.001)

    def test_pure_white_luminance(self):
        """Pure white should have 1.0 luminance."""
        assert calculate_luminance("#FFFFFF") == pytest.approx(1.0, abs=0.001)

    def test_light_gray_luminance(self):
        """Light gray should have high luminance."""
        luminance = calculate_luminance("#F0F0F0")
        assert luminance > 0.8

    def test_pale_yellow_luminance(self):
        """Pale yellow should have very high luminance."""
        luminance = calculate_luminance("#FFFFE0")
        assert luminance > 0.9

    def test_red_luminance(self):
        """Pure red should have moderate luminance."""
        luminance = calculate_luminance("#FF0000")
        assert 0.1 < luminance < 0.3

    def test_blue_luminance(self):
        """Pure blue should have low luminance."""
        luminance = calculate_luminance("#0000FF")
        assert luminance < 0.1

    def test_green_luminance(self):
        """Pure green should have high luminance (humans perceive it as bright)."""
        luminance = calculate_luminance("#00FF00")
        assert luminance > 0.7

    def test_3char_hex_format(self):
        """3-character hex colors should be handled correctly."""
        # #FFF should expand to #FFFFFF
        assert calculate_luminance("#FFF") == pytest.approx(1.0, abs=0.001)
        # #000 should expand to #000000
        assert calculate_luminance("#000") == pytest.approx(0.0, abs=0.001)

    def test_hex_without_hash(self):
        """Hex colors without # prefix should be handled."""
        assert calculate_luminance("FFFFFF") == pytest.approx(1.0, abs=0.001)
        assert calculate_luminance("000000") == pytest.approx(0.0, abs=0.001)


class TestHaloColorSelection:
    """Test halo color selection based on wire color."""

    def test_white_gets_dark_halo(self):
        """Pure white wire should get dark halo."""
        halo = get_halo_color("#FFFFFF")
        assert halo == RENDER_CONSTANTS.DARK_HALO_COLOR

    def test_light_gray_gets_dark_halo(self):
        """Light gray wire should get dark halo."""
        halo = get_halo_color("#F0F0F0")
        assert halo == RENDER_CONSTANTS.DARK_HALO_COLOR

    def test_pale_yellow_gets_dark_halo(self):
        """Pale yellow wire should get dark halo."""
        halo = get_halo_color("#FFFFE0")
        assert halo == RENDER_CONSTANTS.DARK_HALO_COLOR

    def test_black_gets_white_halo(self):
        """Black wire should get white halo."""
        halo = get_halo_color("#000000")
        assert halo == RENDER_CONSTANTS.LIGHT_HALO_COLOR

    def test_red_gets_white_halo(self):
        """Red wire should get white halo."""
        halo = get_halo_color("#FF0000")
        assert halo == RENDER_CONSTANTS.LIGHT_HALO_COLOR

    def test_blue_gets_white_halo(self):
        """Blue wire should get white halo."""
        halo = get_halo_color("#0000FF")
        assert halo == RENDER_CONSTANTS.LIGHT_HALO_COLOR

    def test_light_blue_near_threshold(self):
        """Light blue (luminance ~0.637) should get white halo."""
        # Just below threshold of 0.7
        halo = get_halo_color("#ADD8E6")
        assert halo == RENDER_CONSTANTS.LIGHT_HALO_COLOR

    def test_threshold_boundary(self):
        """Test colors at the threshold boundary."""
        # Find a color with luminance very close to threshold
        # This tests that threshold comparison works correctly
        threshold = RENDER_CONSTANTS.LUMINANCE_THRESHOLD

        # Color slightly above threshold should get dark halo
        very_light_gray = "#F5F5F5"
        if calculate_luminance(very_light_gray) > threshold:
            assert get_halo_color(very_light_gray) == RENDER_CONSTANTS.DARK_HALO_COLOR

        # Color slightly below threshold should get white halo
        medium_gray = "#AAAAAA"
        if calculate_luminance(medium_gray) < threshold:
            assert get_halo_color(medium_gray) == RENDER_CONSTANTS.LIGHT_HALO_COLOR


class TestLuminanceAccuracy:
    """Test luminance calculation accuracy using known WCAG values."""

    def test_wcag_relative_luminance_formula(self):
        """Verify formula matches WCAG 2.0 spec for various gray values."""
        # #777777 (RGB 119,119,119) should have luminance ~0.184
        luminance = calculate_luminance("#777777")
        assert 0.18 < luminance < 0.19

        # #AAAAAA (RGB 170,170,170) should have luminance ~0.402
        luminance = calculate_luminance("#AAAAAA")
        assert 0.40 < luminance < 0.41

    def test_green_perception(self):
        """Green should appear brighter than red and blue due to human perception."""
        red_lum = calculate_luminance("#FF0000")
        green_lum = calculate_luminance("#00FF00")
        blue_lum = calculate_luminance("#0000FF")

        # Green should have highest luminance (0.2126 * 0 + 0.7152 * 1 + 0.0722 * 0 = 0.7152)
        assert green_lum > red_lum
        assert green_lum > blue_lum

        # Red should be brighter than blue (0.2126 vs 0.0722)
        assert red_lum > blue_lum
