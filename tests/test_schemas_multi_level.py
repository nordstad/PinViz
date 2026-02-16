"""Tests for multi-level connection schemas (Phase 2.1)."""

import pytest
from pydantic import ValidationError

from pinviz.schemas import (
    ConnectionSchema,
    ConnectionSourceSchema,
    ConnectionTargetSchema,
)


class TestConnectionSourceSchema:
    """Test ConnectionSourceSchema validation."""

    def test_board_source_valid(self):
        """Test valid board pin source."""
        source = ConnectionSourceSchema(board_pin=1)
        assert source.board_pin == 1
        assert source.device is None
        assert source.device_pin is None

    def test_device_source_valid(self):
        """Test valid device source."""
        source = ConnectionSourceSchema(device="Regulator", device_pin="VOUT")
        assert source.device == "Regulator"
        assert source.device_pin == "VOUT"
        assert source.board_pin is None

    def test_board_pin_range_validation(self):
        """Test board pin must be between 1 and 50."""
        # Valid pins
        ConnectionSourceSchema(board_pin=1)
        ConnectionSourceSchema(board_pin=50)

        # Invalid pins
        with pytest.raises(ValidationError):
            ConnectionSourceSchema(board_pin=0)

        with pytest.raises(ValidationError):
            ConnectionSourceSchema(board_pin=51)

    def test_both_sources_invalid(self):
        """Test that specifying both board and device source is invalid."""
        with pytest.raises(ValidationError, match="cannot specify multiple types"):
            ConnectionSourceSchema(board_pin=1, device="Reg", device_pin="OUT")

    def test_no_source_invalid(self):
        """Test that omitting both sources is invalid."""
        with pytest.raises(ValidationError, match="must specify one of"):
            ConnectionSourceSchema()

    def test_device_without_pin_invalid(self):
        """Test that device source requires device_pin."""
        with pytest.raises(ValidationError, match="must specify one of"):
            ConnectionSourceSchema(device="Regulator")

    def test_pin_without_device_invalid(self):
        """Test that device_pin requires device."""
        with pytest.raises(ValidationError, match="must specify one of"):
            ConnectionSourceSchema(device_pin="OUT")


class TestConnectionTargetSchema:
    """Test ConnectionTargetSchema validation."""

    def test_valid_target(self):
        """Test valid connection target."""
        target = ConnectionTargetSchema(device="LED", device_pin="VCC")
        assert target.device == "LED"
        assert target.device_pin == "VCC"

    def test_missing_device_invalid(self):
        """Test that device is required."""
        with pytest.raises(ValidationError):
            ConnectionTargetSchema(device_pin="VCC")

    def test_missing_device_pin_invalid(self):
        """Test that device_pin is required."""
        with pytest.raises(ValidationError):
            ConnectionTargetSchema(device="LED")


class TestConnectionSchemaLegacyFormat:
    """Test ConnectionSchema with legacy format (backward compatibility)."""

    def test_parse_legacy_format(self):
        """Test parsing legacy board-to-device format."""
        data = {"board_pin": 1, "device": "LED", "device_pin": "VCC"}
        schema = ConnectionSchema(**data)

        assert schema.board_pin == 1
        assert schema.device == "LED"
        assert schema.device_pin == "VCC"
        assert schema.from_ is None
        assert schema.to is None

    def test_legacy_format_with_color(self):
        """Test legacy format with optional color."""
        data = {
            "board_pin": 1,
            "device": "LED",
            "device_pin": "VCC",
            "color": "#FF0000",
        }
        schema = ConnectionSchema(**data)
        assert schema.color == "#FF0000"

    def test_legacy_format_with_style(self):
        """Test legacy format with wire style."""
        data = {
            "board_pin": 1,
            "device": "LED",
            "device_pin": "VCC",
            "style": "orthogonal",
        }
        schema = ConnectionSchema(**data)
        assert schema.style == "orthogonal"

    def test_legacy_format_to_connection(self):
        """Test converting legacy format to Connection model."""
        data = {"board_pin": 1, "device": "LED", "device_pin": "VCC"}
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert conn.is_board_connection()
        assert not conn.is_device_connection()
        assert conn.board_pin == 1
        assert conn.device_name == "LED"
        assert conn.device_pin_name == "VCC"


class TestConnectionSchemaNewFormat:
    """Test ConnectionSchema with new from/to format."""

    def test_parse_new_format_board_source(self):
        """Test parsing new format with board source."""
        data = {"from": {"board_pin": 1}, "to": {"device": "LED", "device_pin": "VCC"}}
        schema = ConnectionSchema(**data)

        assert schema.from_ is not None
        assert schema.from_.board_pin == 1
        assert schema.to is not None
        assert schema.to.device == "LED"
        assert schema.to.device_pin == "VCC"

    def test_parse_new_format_device_source(self):
        """Test parsing new format with device source."""
        data = {
            "from": {"device": "Regulator", "device_pin": "VOUT"},
            "to": {"device": "LED", "device_pin": "VCC"},
        }
        schema = ConnectionSchema(**data)

        assert schema.from_ is not None
        assert schema.from_.device == "Regulator"
        assert schema.from_.device_pin == "VOUT"
        assert schema.to is not None
        assert schema.to.device == "LED"
        assert schema.to.device_pin == "VCC"

    def test_new_format_board_to_connection(self):
        """Test converting new format (board source) to Connection model."""
        data = {"from": {"board_pin": 1}, "to": {"device": "LED", "device_pin": "VCC"}}
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert conn.is_board_connection()
        assert not conn.is_device_connection()
        assert conn.board_pin == 1
        assert conn.device_name == "LED"
        assert conn.device_pin_name == "VCC"

    def test_new_format_device_to_connection(self):
        """Test converting new format (device source) to Connection model."""
        data = {
            "from": {"device": "Regulator", "device_pin": "VOUT"},
            "to": {"device": "LED", "device_pin": "VCC"},
        }
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert conn.is_device_connection()
        assert not conn.is_board_connection()
        assert conn.source_device == "Regulator"
        assert conn.source_pin == "VOUT"
        assert conn.device_name == "LED"
        assert conn.device_pin_name == "VCC"

    def test_new_format_with_color_and_style(self):
        """Test new format with optional color and style."""
        data = {
            "from": {"board_pin": 1},
            "to": {"device": "LED", "device_pin": "VCC"},
            "color": "#FF0000",
            "style": "curved",
        }
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert conn.color == "#FF0000"
        from pinviz.model import WireStyle

        assert conn.style == WireStyle.CURVED


class TestConnectionSchemaValidation:
    """Test ConnectionSchema validation rules."""

    def test_reject_mixed_format(self):
        """Test that mixing legacy and new format is rejected."""
        # Include all required legacy fields to trigger the validation
        data = {
            "board_pin": 1,
            "device": "LED",
            "device_pin": "VCC",
            "from": {"board_pin": 2},
            "to": {"device": "LED", "device_pin": "VCC"},
        }
        with pytest.raises(ValidationError, match="Cannot mix"):
            ConnectionSchema(**data)

    def test_reject_no_format(self):
        """Test that connection must use one format."""
        data = {"color": "#FF0000"}
        with pytest.raises(ValidationError, match="must use either"):
            ConnectionSchema(**data)

    def test_reject_partial_new_format_missing_from(self):
        """Test that new format requires both from and to."""
        data = {"to": {"device": "LED", "device_pin": "VCC"}}
        with pytest.raises(ValidationError, match="must use either"):
            ConnectionSchema(**data)

    def test_reject_partial_new_format_missing_to(self):
        """Test that new format requires both from and to."""
        data = {"from": {"board_pin": 1}}
        with pytest.raises(ValidationError, match="must use either"):
            ConnectionSchema(**data)

    def test_reject_partial_legacy_format(self):
        """Test that legacy format requires all three fields."""
        # Missing device
        with pytest.raises(ValidationError, match="must use either"):
            ConnectionSchema(board_pin=1, device_pin="VCC")

        # Missing device_pin
        with pytest.raises(ValidationError, match="must use either"):
            ConnectionSchema(board_pin=1, device="LED")

        # Missing board_pin
        with pytest.raises(ValidationError, match="must use either"):
            ConnectionSchema(device="LED", device_pin="VCC")


class TestConnectionSchemaComponents:
    """Test ConnectionSchema with inline components."""

    def test_legacy_format_with_components(self):
        """Test legacy format with inline components."""
        data = {
            "board_pin": 11,
            "device": "LED",
            "device_pin": "Anode",
            "components": [{"type": "resistor", "value": "220Ω"}],
        }
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert len(conn.components) == 1
        assert conn.components[0].value == "220Ω"

    def test_new_format_with_components(self):
        """Test new format with inline components."""
        data = {
            "from": {"board_pin": 11},
            "to": {"device": "LED", "device_pin": "Anode"},
            "components": [
                {"type": "resistor", "value": "220Ω", "position": 0.6},
                {"type": "diode", "value": "1N4148"},
            ],
        }
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert len(conn.components) == 2
        assert conn.components[0].value == "220Ω"
        assert conn.components[0].position == 0.6
        assert conn.components[1].value == "1N4148"


class TestConnectionSchemaWireStyle:
    """Test wire style validation and conversion."""

    @pytest.mark.parametrize(
        "style_str,expected_enum",
        [
            ("orthogonal", "ORTHOGONAL"),
            ("curved", "CURVED"),
            ("mixed", "MIXED"),
        ],
    )
    def test_wire_style_conversion(self, style_str, expected_enum):
        """Test wire style string to enum conversion."""
        from pinviz.model import WireStyle

        data = {
            "board_pin": 1,
            "device": "LED",
            "device_pin": "VCC",
            "style": style_str,
        }
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert conn.style == WireStyle[expected_enum]

    def test_invalid_wire_style(self):
        """Test that invalid wire style is rejected."""
        data = {
            "board_pin": 1,
            "device": "LED",
            "device_pin": "VCC",
            "style": "invalid_style",
        }
        with pytest.raises(ValidationError, match="Invalid wire style"):
            ConnectionSchema(**data)


class TestConnectionSchemaBackwardCompatibility:
    """Test backward compatibility with existing configurations."""

    def test_all_existing_examples_parse(self):
        """Test that all existing example connection formats still work."""
        # Simple connection
        conn1 = ConnectionSchema(board_pin=1, device="Sensor", device_pin="VCC")
        assert conn1.to_connection().is_board_connection()

        # With color
        conn2 = ConnectionSchema(board_pin=2, device="Sensor", device_pin="GND", color="#000000")
        assert conn2.color == "#000000"

        # With style
        conn3 = ConnectionSchema(board_pin=3, device="Sensor", device_pin="SDA", style="orthogonal")
        assert conn3.style == "orthogonal"

        # With net name
        conn4 = ConnectionSchema(board_pin=5, device="Sensor", device_pin="SCL", net="I2C_BUS")
        assert conn4.net == "I2C_BUS"

    def test_conversion_preserves_all_fields(self):
        """Test that to_connection() preserves all fields."""
        data = {
            "board_pin": 11,
            "device": "LED",
            "device_pin": "Anode",
            "color": "#FF0000",
            "net": "LED_POWER",
            "style": "curved",
        }
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert conn.board_pin == 11
        assert conn.device_name == "LED"
        assert conn.device_pin_name == "Anode"
        assert conn.color == "#FF0000"
        assert conn.net_name == "LED_POWER"
        from pinviz.model import WireStyle

        assert conn.style == WireStyle.CURVED


class TestConnectionSchemaEdgeCases:
    """Test edge cases and error handling."""

    def test_device_names_with_special_characters(self):
        """Test device names with spaces and special characters."""
        data = {
            "from": {"device": "5V Regulator", "device_pin": "VOUT"},
            "to": {"device": "Status LED", "device_pin": "VCC"},
        }
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert conn.source_device == "5V Regulator"
        assert conn.device_name == "Status LED"

    def test_pin_names_with_special_characters(self):
        """Test pin names with special characters."""
        data = {
            "from": {"device": "Charger", "device_pin": "OUT+"},
            "to": {"device": "Controller", "device_pin": "VIN"},
        }
        schema = ConnectionSchema(**data)
        conn = schema.to_connection()

        assert conn.source_pin == "OUT+"

    def test_case_sensitive_fields(self):
        """Test that field values are case-sensitive (except style)."""
        # Device names are case-sensitive
        data1 = {
            "from": {"device": "LED", "device_pin": "VCC"},
            "to": {"device": "led", "device_pin": "GND"},
        }
        schema1 = ConnectionSchema(**data1)
        assert schema1.from_.device == "LED"
        assert schema1.to.device == "led"

        # Style is case-insensitive
        data2 = {
            "board_pin": 1,
            "device": "LED",
            "device_pin": "VCC",
            "style": "ORTHOGONAL",
        }
        schema2 = ConnectionSchema(**data2)
        assert schema2.style == "orthogonal"
