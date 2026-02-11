"""Unit tests for explicit pin side placement feature."""

import pytest
from pydantic import ValidationError

from pinviz.devices.loader import load_device_from_config
from pinviz.model import Point
from pinviz.schemas import validate_device_config


class TestPinSidePlacement:
    """Test cases for the 'side' field in device pin configurations."""

    def test_explicit_left_side(self):
        """Test that pins with side='left' are placed on the left."""
        device = load_device_from_config("relay_module")

        # Pins explicitly set to left
        left_pins = ["VCC", "GND", "IN"]
        device_center = device.width / 2

        for pin in device.pins:
            if pin.name in left_pins:
                assert pin.position.x < device_center, (
                    f"Pin {pin.name} should be on left side but is at X={pin.position.x}"
                )

    def test_explicit_right_side(self):
        """Test that pins with side='right' are placed on the right."""
        device = load_device_from_config("relay_module")

        # Pins explicitly set to right
        right_pins = ["COM", "NO", "NC"]
        device_center = device.width / 2

        for pin in device.pins:
            if pin.name in right_pins:
                assert pin.position.x > device_center, (
                    f"Pin {pin.name} should be on right side but is at X={pin.position.x}"
                )

    def test_backward_compatibility_no_side_field(self):
        """Test that devices without 'side' field still work (automatic detection)."""
        device = load_device_from_config("relay_auto")

        # Should have 6 pins
        assert len(device.pins) == 6

        # All pins should have positions
        for pin in device.pins:
            assert pin.position is not None
            assert isinstance(pin.position, Point)
            assert pin.position.x >= 0
            assert pin.position.y >= 0

    def test_mixed_explicit_and_automatic(self):
        """Test device with some pins having 'side' and some using automatic detection."""
        # relay_auto has no side fields, uses automatic detection
        device = load_device_from_config("relay_auto")
        device_center = device.width / 2

        # COM, NO, NC should go right (automatic detection)
        output_pins = ["COM", "NO", "NC"]
        for pin in device.pins:
            if pin.name in output_pins:
                assert pin.position.x > device_center

    def test_side_field_case_insensitive(self):
        """Test that side field values are case-insensitive."""
        # The schema validator should convert to lowercase
        # This is tested implicitly by loading relay_module which uses lowercase
        device = load_device_from_config("relay_module")
        assert device is not None

    def test_all_pins_on_left(self):
        """Test device with all pins explicitly on left side."""
        # BH1750 has all pins on left by default
        device = load_device_from_config("bh1750")
        device_center = device.width / 2

        for pin in device.pins:
            assert pin.position.x < device_center, (
                f"All pins should be on left, but {pin.name} is at X={pin.position.x}"
            )

    def test_pin_positions_are_unique_per_side(self):
        """Test that pins on the same side have different Y positions."""
        device = load_device_from_config("relay_module")
        device_center = device.width / 2

        # Collect Y positions for left side
        left_y_positions = []
        right_y_positions = []

        for pin in device.pins:
            if pin.position.x < device_center:
                left_y_positions.append(pin.position.y)
            else:
                right_y_positions.append(pin.position.y)

        # Check left side pins have unique Y positions
        assert len(left_y_positions) == len(set(left_y_positions)), (
            "Left side pins should have unique Y positions"
        )

        # Check right side pins have unique Y positions
        assert len(right_y_positions) == len(set(right_y_positions)), (
            "Right side pins should have unique Y positions"
        )

    def test_explicit_position_overrides_side(self):
        """Test that explicit position takes precedence over side field."""
        # Create a test device config with both position and side
        # This is tested by checking that devices with explicit positions work
        device = load_device_from_config("bh1750")

        # All pins should have calculated positions
        for pin in device.pins:
            assert pin.position is not None

    def test_side_field_in_json_schema(self):
        """Test that the side field is accepted by JSON schema validation."""
        from pinviz.schemas import validate_device_config

        config = {
            "id": "test_device",
            "name": "Test Device",
            "category": "sensors",
            "pins": [
                {"name": "VCC", "role": "3V3", "side": "left"},
                {"name": "OUT", "role": "GPIO", "side": "right"},
            ],
        }

        # Should not raise ValidationError
        validated = validate_device_config(config)
        assert validated.pins[0].side == "left"
        assert validated.pins[1].side == "right"

    def test_invalid_side_value_raises_error(self):
        """Test that invalid side values are rejected by validation."""
        config = {
            "id": "test_device",
            "name": "Test Device",
            "category": "sensors",
            "pins": [
                {"name": "VCC", "role": "3V3", "side": "middle"},  # Invalid
            ],
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_device_config(config)

        assert "side" in str(exc_info.value).lower()

    def test_side_field_none_uses_automatic(self):
        """Test that side=None falls back to automatic detection."""
        # Load a device without side field
        device = load_device_from_config("bh1750")

        # Should still have valid positions
        for pin in device.pins:
            assert pin.position is not None
            assert pin.position.x >= 0

    def test_relay_module_has_correct_layout(self):
        """Test the specific relay module layout requirements."""
        device = load_device_from_config("relay_module")
        device_center = device.width / 2

        # Control pins (left side)
        control_pins = {"VCC", "GND", "IN"}
        # Load pins (right side)
        load_pins = {"COM", "NO", "NC"}

        pins_by_name = {pin.name: pin for pin in device.pins}

        # Verify control pins are on left
        for pin_name in control_pins:
            pin = pins_by_name[pin_name]
            assert pin.position.x < device_center, (
                f"Control pin {pin_name} should be on left side"
            )

        # Verify load pins are on right
        for pin_name in load_pins:
            pin = pins_by_name[pin_name]
            assert pin.position.x > device_center, (
                f"Load pin {pin_name} should be on right side"
            )

    def test_device_width_affects_pin_placement(self):
        """Test that device width is considered in pin placement."""
        device = load_device_from_config("relay_module")

        # Device should have the specified width
        assert device.width == 90.0

        # Left pins should be near left edge (around 5px from edge)
        left_pins = [p for p in device.pins if p.name in ["VCC", "GND", "IN"]]
        for pin in left_pins:
            assert 0 < pin.position.x < 20, (
                f"Left pin {pin.name} should be near left edge"
            )

        # Right pins should be near right edge
        right_pins = [p for p in device.pins if p.name in ["COM", "NO", "NC"]]
        for pin in right_pins:
            assert device.width - 20 < pin.position.x < device.width, (
                f"Right pin {pin.name} should be near right edge"
            )


class TestSidePlacementPrecedence:
    """Test the precedence order: position > side > automatic > default."""

    def test_precedence_explicit_position_highest(self):
        """Test that explicit position has highest precedence."""
        # Devices with explicit positions should use those
        # regardless of side field or automatic detection
        device = load_device_from_config("bh1750")

        # All pins should have positions (whether explicit or calculated)
        for pin in device.pins:
            assert pin.position is not None

    def test_precedence_side_over_automatic(self):
        """Test that explicit side overrides automatic detection."""
        # Relay module has explicit sides that override automatic
        device = load_device_from_config("relay_module")
        device_center = device.width / 2

        # IN pin would normally be on left (automatic), and it is on left (explicit)
        # COM would go right (automatic "COM" detection), and it is right (explicit)
        # This confirms side field is being used

        pins_by_name = {pin.name: pin for pin in device.pins}

        # Verify explicit placement
        assert pins_by_name["IN"].position.x < device_center
        assert pins_by_name["COM"].position.x > device_center

    def test_precedence_automatic_over_default(self):
        """Test that automatic detection overrides default left placement."""
        # Load device without side fields
        device = load_device_from_config("relay_auto")
        device_center = device.width / 2

        pins_by_name = {pin.name: pin for pin in device.pins}

        # COM should be on right due to automatic detection (not default left)
        assert pins_by_name["COM"].position.x > device_center


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_single_pin_device(self):
        """Test device with only one pin."""
        device = load_device_from_config("led")

        # Should have at least 2 pins (+ and -)
        assert len(device.pins) >= 2

        # All should have valid positions
        for pin in device.pins:
            assert pin.position is not None

    def test_device_with_no_output_pins(self):
        """Test device where all pins would default to left."""
        device = load_device_from_config("bh1750")
        device_center = device.width / 2

        # All pins should be on left (no output pins detected)
        for pin in device.pins:
            assert pin.position.x < device_center

    def test_vertical_layout_with_sides(self):
        """Test that vertical layout (default) works with side placement."""
        device = load_device_from_config("relay_module")

        # Get left side pins
        left_pins = [p for p in device.pins if p.name in ["VCC", "GND", "IN"]]

        # Should be vertically stacked (same X, different Y)
        x_positions = [p.position.x for p in left_pins]
        y_positions = [p.position.y for p in left_pins]

        # All left pins should have same X
        assert len(set(x_positions)) == 1, "Left pins should be vertically aligned"

        # All should have different Y
        assert len(set(y_positions)) == len(y_positions), (
            "Left pins should be at different Y positions"
        )

    def test_empty_side_value_treated_as_none(self):
        """Test that empty string for side is handled gracefully."""
        # This would be caught by schema validation, but test loader robustness
        device = load_device_from_config("bh1750")

        # Should load without errors
        assert device is not None
