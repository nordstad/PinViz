"""Tests for configuration schema validation."""

import pytest
from pydantic import ValidationError

from pinviz.schemas import (
    ComponentSchema,
    ConnectionSchema,
    CustomDeviceSchema,
    DevicePinSchema,
    DeviceSchema,
    DiagramConfigSchema,
    PointSchema,
    PredefinedDeviceSchema,
    get_validation_errors,
    validate_config,
)


class TestPointSchema:
    """Tests for PointSchema validation."""

    def test_valid_point(self):
        """Test valid point coordinates."""
        point = PointSchema(x=10.5, y=20.0)
        assert point.x == 10.5
        assert point.y == 20.0

    def test_negative_coordinates(self):
        """Test that negative coordinates are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PointSchema(x=-10, y=20)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_zero_coordinates(self):
        """Test that zero coordinates are accepted."""
        point = PointSchema(x=0, y=0)
        assert point.x == 0
        assert point.y == 0


class TestDevicePinSchema:
    """Tests for DevicePinSchema validation."""

    def test_valid_device_pin(self):
        """Test valid device pin with default role."""
        pin = DevicePinSchema(name="VCC")
        assert pin.name == "VCC"
        assert pin.role == "GPIO"
        assert pin.position is None

    def test_valid_device_pin_with_role(self):
        """Test valid device pin with specific role."""
        pin = DevicePinSchema(name="SDA", role="I2C_SDA")
        assert pin.name == "SDA"
        assert pin.role == "I2C_SDA"

    def test_valid_device_pin_with_position(self):
        """Test valid device pin with position."""
        pin = DevicePinSchema(name="GND", role="GND", position={"x": 5, "y": 10})
        assert pin.name == "GND"
        assert pin.position.x == 5
        assert pin.position.y == 10

    def test_invalid_pin_role(self):
        """Test that invalid pin role is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DevicePinSchema(name="DATA", role="INVALID_ROLE")
        assert "Invalid pin role" in str(exc_info.value)

    def test_pin_role_case_insensitive(self):
        """Test that pin role is converted to uppercase."""
        pin = DevicePinSchema(name="GND", role="gnd")
        assert pin.role == "GND"

    def test_empty_pin_name(self):
        """Test that empty pin name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DevicePinSchema(name="")
        assert "at least 1 character" in str(exc_info.value)

    def test_pin_name_too_long(self):
        """Test that excessively long pin name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DevicePinSchema(name="A" * 51)
        assert "at most 50 characters" in str(exc_info.value)


class TestCustomDeviceSchema:
    """Tests for CustomDeviceSchema validation."""

    def test_valid_custom_device(self):
        """Test valid custom device definition."""
        device = CustomDeviceSchema(
            name="Test Device",
            pins=[
                {"name": "VCC", "role": "3V3"},
                {"name": "GND", "role": "GND"},
            ],
        )
        assert device.name == "Test Device"
        assert len(device.pins) == 2
        assert device.width == 80.0
        assert device.height == 40.0

    def test_custom_device_with_dimensions(self):
        """Test custom device with custom dimensions."""
        device = CustomDeviceSchema(
            name="Large Device",
            pins=[{"name": "PIN1", "role": "GPIO"}],
            width=120.0,
            height=60.0,
            color="#FF5733",
        )
        assert device.width == 120.0
        assert device.height == 60.0
        assert device.color == "#FF5733"

    def test_device_without_pins(self):
        """Test that device without pins is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CustomDeviceSchema(name="Invalid Device", pins=[])
        assert "at least 1" in str(exc_info.value)

    def test_device_with_duplicate_pin_names(self):
        """Test that duplicate pin names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CustomDeviceSchema(
                name="Bad Device",
                pins=[
                    {"name": "VCC", "role": "3V3"},
                    {"name": "VCC", "role": "5V"},
                ],
            )
        assert "Duplicate pin names" in str(exc_info.value)

    def test_named_color_accepted(self):
        """Test that named colors are accepted and converted to hex."""
        schema = CustomDeviceSchema(
            name="Device",
            pins=[{"name": "PIN1"}],
            color="red",  # Named color should work
        )
        assert schema.color == "#FF0000"

    def test_invalid_color_falls_back_to_default(self):
        """Test that invalid colors fall back to default."""
        schema = CustomDeviceSchema(
            name="Device",
            pins=[{"name": "PIN1"}],
            color="notacolor",  # Invalid color
        )
        assert schema.color == "#4A90E2"  # Default color

    def test_negative_dimensions(self):
        """Test that negative dimensions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CustomDeviceSchema(name="Device", pins=[{"name": "PIN1"}], width=-10)
        assert "greater than 0" in str(exc_info.value)


class TestPredefinedDeviceSchema:
    """Tests for PredefinedDeviceSchema validation."""

    def test_valid_predefined_device(self):
        """Test valid predefined device."""
        device = PredefinedDeviceSchema(type="bh1750", name="Light Sensor")
        assert device.type == "bh1750"
        assert device.name == "Light Sensor"

    def test_predefined_device_without_name(self):
        """Test predefined device without custom name."""
        device = PredefinedDeviceSchema(type="led")
        assert device.type == "led"
        assert device.name is None

    def test_ir_led_ring_with_num_leds(self):
        """Test IR LED ring with custom LED count."""
        device = PredefinedDeviceSchema(type="ir_led_ring", num_leds=16)
        assert device.type == "ir_led_ring"
        assert device.num_leds == 16

    def test_i2c_device_with_interrupt(self):
        """Test I2C device with interrupt pin."""
        device = PredefinedDeviceSchema(type="i2c_device", has_interrupt=True)
        assert device.type == "i2c_device"
        assert device.has_interrupt is True

    def test_led_with_color(self):
        """Test LED with color specification."""
        device = PredefinedDeviceSchema(type="led", color="Blue")
        assert device.type == "led"
        assert device.color == "Blue"

    def test_button_with_pull_up(self):
        """Test button with pull-up resistor."""
        device = PredefinedDeviceSchema(type="button", pull_up=False)
        assert device.type == "button"
        assert device.pull_up is False

    def test_invalid_device_type(self):
        """Test that invalid device type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PredefinedDeviceSchema(type="unknown_device")
        assert "Invalid device type" in str(exc_info.value)

    def test_device_type_case_insensitive(self):
        """Test that device type is converted to lowercase."""
        device = PredefinedDeviceSchema(type="BH1750")
        assert device.type == "bh1750"

    def test_num_leds_out_of_range(self):
        """Test that invalid LED count is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PredefinedDeviceSchema(type="ir_led_ring", num_leds=0)
        assert "greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            PredefinedDeviceSchema(type="ir_led_ring", num_leds=101)
        assert "less than or equal to 100" in str(exc_info.value)


class TestDeviceSchema:
    """Tests for DeviceSchema validation."""

    def test_validate_predefined_device(self):
        """Test validation of predefined device."""
        data = {"type": "bh1750", "name": "Sensor"}
        device = DeviceSchema.validate_device(data)
        assert isinstance(device, PredefinedDeviceSchema)
        assert device.type == "bh1750"

    def test_validate_custom_device(self):
        """Test validation of custom device."""
        data = {"name": "Custom", "pins": [{"name": "PIN1", "role": "GPIO"}]}
        device = DeviceSchema.validate_device(data)
        assert isinstance(device, CustomDeviceSchema)
        assert device.name == "Custom"

    def test_validate_device_missing_required_fields(self):
        """Test that device without type or pins is rejected."""
        with pytest.raises(ValueError) as exc_info:
            DeviceSchema.validate_device({"name": "Invalid"})
        assert "type" in str(exc_info.value) or "pins" in str(exc_info.value)


class TestComponentSchema:
    """Tests for ComponentSchema validation."""

    def test_valid_component(self):
        """Test valid component definition."""
        comp = ComponentSchema(type="resistor", value="220Ω", position=0.5)
        assert comp.type == "resistor"
        assert comp.value == "220Ω"
        assert comp.position == 0.5

    def test_component_defaults(self):
        """Test component with default values."""
        comp = ComponentSchema(value="10µF")
        assert comp.type == "resistor"
        assert comp.position == 0.55

    def test_component_types(self):
        """Test all valid component types."""
        for comp_type in ["resistor", "capacitor", "led", "diode"]:
            comp = ComponentSchema(type=comp_type, value="100Ω")
            assert comp.type == comp_type

    def test_invalid_component_type(self):
        """Test that invalid component type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentSchema(type="inductor", value="1mH")
        assert "Invalid component type" in str(exc_info.value)

    def test_component_position_out_of_range(self):
        """Test that position outside [0, 1] is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentSchema(value="220Ω", position=1.5)
        assert "less than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ComponentSchema(value="220Ω", position=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)


class TestConnectionSchema:
    """Tests for ConnectionSchema validation."""

    def test_valid_connection(self):
        """Test valid connection definition."""
        conn = ConnectionSchema(board_pin=1, device="LED", device_pin="Anode")
        assert conn.board_pin == 1
        assert conn.device == "LED"
        assert conn.device_pin == "Anode"
        assert conn.style == "mixed"

    def test_connection_with_color(self):
        """Test connection with custom color."""
        conn = ConnectionSchema(board_pin=11, device="LED", device_pin="Anode", color="#FF0000")
        assert conn.color == "#FF0000"

    def test_connection_with_net_name(self):
        """Test connection with net name."""
        conn = ConnectionSchema(board_pin=3, device="Device", device_pin="SDA", net="I2C_SDA")
        assert conn.net == "I2C_SDA"

    def test_connection_with_style(self):
        """Test connection with different wire styles."""
        for style in ["orthogonal", "curved", "mixed"]:
            conn = ConnectionSchema(board_pin=5, device="Device", device_pin="PIN", style=style)
            assert conn.style == style

    def test_connection_with_components(self):
        """Test connection with inline components."""
        conn = ConnectionSchema(
            board_pin=11,
            device="LED",
            device_pin="Anode",
            components=[{"type": "resistor", "value": "220Ω"}],
        )
        assert len(conn.components) == 1
        assert conn.components[0].type == "resistor"

    def test_invalid_board_pin_number(self):
        """Test that invalid board pin number is rejected."""
        # Pin numbers must be >= 1
        with pytest.raises(ValidationError) as exc_info:
            ConnectionSchema(board_pin=0, device="Device", device_pin="PIN")
        assert "greater than or equal to 1" in str(exc_info.value)

        # Note: No upper bound check - boards can have varying pin counts
        # (e.g., 40-pin for Raspberry Pi, but other boards may differ)

    def test_invalid_wire_style(self):
        """Test that invalid wire style is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ConnectionSchema(board_pin=1, device="Device", device_pin="PIN", style="invalid")
        assert "Invalid wire style" in str(exc_info.value)

    def test_named_color_accepted(self):
        """Test that named colors are accepted and converted to hex."""
        schema = ConnectionSchema(board_pin=1, device="Device", device_pin="PIN", color="red")
        assert schema.color == "#FF0000"

    def test_invalid_color_falls_back_to_default(self):
        """Test that invalid colors fall back to default."""
        schema = ConnectionSchema(board_pin=1, device="Device", device_pin="PIN", color="notacolor")
        assert schema.color == "#4A90E2"  # Default fallback


class TestDiagramConfigSchema:
    """Tests for DiagramConfigSchema validation."""

    def test_valid_diagram_config(self):
        """Test valid diagram configuration."""
        config = DiagramConfigSchema(
            title="Test Diagram",
            board="raspberry_pi_5",
            devices=[{"type": "bh1750"}],
            connections=[{"board_pin": 1, "device": "BH1750", "device_pin": "VCC"}],
        )
        assert config.title == "Test Diagram"
        assert config.board == "raspberry_pi_5"
        assert len(config.devices) == 1
        assert len(config.connections) == 1

    def test_diagram_config_defaults(self):
        """Test diagram configuration with default values."""
        config = DiagramConfigSchema(
            devices=[{"type": "led"}],
            connections=[{"board_pin": 11, "device": "LED", "device_pin": "Anode"}],
        )
        assert config.title == "GPIO Diagram"
        assert config.board == "raspberry_pi_5"
        assert config.show_legend is True
        assert config.show_gpio_diagram is False

    def test_multiple_devices_and_connections(self):
        """Test diagram with multiple devices and connections."""
        config = DiagramConfigSchema(
            devices=[{"type": "bh1750"}, {"type": "led", "color": "Red"}],
            connections=[
                {"board_pin": 1, "device": "BH1750", "device_pin": "VCC"},
                {"board_pin": 11, "device": "LED", "device_pin": "Anode"},
            ],
        )
        assert len(config.devices) == 2
        assert len(config.connections) == 2

    def test_custom_device_in_config(self):
        """Test diagram with custom device definition."""
        config = DiagramConfigSchema(
            devices=[
                {
                    "name": "Custom Sensor",
                    "pins": [
                        {"name": "VCC", "role": "3V3"},
                        {"name": "GND", "role": "GND"},
                    ],
                }
            ],
            connections=[{"board_pin": 1, "device": "Custom Sensor", "device_pin": "VCC"}],
        )
        assert len(config.devices) == 1

    def test_invalid_board_name(self):
        """Test that invalid board name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DiagramConfigSchema(
                board="arduino_uno",
                devices=[{"type": "led"}],
                connections=[{"board_pin": 1, "device": "LED", "device_pin": "Anode"}],
            )
        assert "Invalid board name" in str(exc_info.value)

    def test_board_name_case_insensitive(self):
        """Test that board name is converted to lowercase."""
        config = DiagramConfigSchema(
            board="RPI5",
            devices=[{"type": "led"}],
            connections=[{"board_pin": 1, "device": "LED", "device_pin": "Anode"}],
        )
        assert config.board == "rpi5"

    def test_empty_devices_list(self):
        """Test that empty devices list is allowed."""
        config = DiagramConfigSchema(devices=[], connections=[])
        assert len(config.devices) == 0
        assert len(config.connections) == 0

    def test_empty_connections_list(self):
        """Test that empty connections list is allowed."""
        config = DiagramConfigSchema(devices=[{"type": "led"}], connections=[])
        assert len(config.devices) == 1
        assert len(config.connections) == 0

    def test_invalid_device_in_list(self):
        """Test that invalid device in list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DiagramConfigSchema(
                devices=[{"type": "unknown_device"}],
                connections=[{"board_pin": 1, "device": "Unknown", "device_pin": "PIN"}],
            )
        assert "Invalid device" in str(exc_info.value)


class TestValidateConfig:
    """Tests for validate_config helper function."""

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = {
            "title": "Test",
            "devices": [{"type": "bh1750"}],
            "connections": [{"board_pin": 1, "device": "BH1750", "device_pin": "VCC"}],
        }
        result = validate_config(config)
        assert result.title == "Test"

    def test_validate_invalid_config(self):
        """Test validation of invalid configuration."""
        config = {"board": "invalid_board", "devices": [], "connections": []}
        with pytest.raises(ValidationError):
            validate_config(config)


class TestGetValidationErrors:
    """Tests for get_validation_errors helper function."""

    def test_get_errors_for_valid_config(self):
        """Test that valid config returns no errors."""
        config = {
            "devices": [{"type": "led"}],
            "connections": [{"board_pin": 1, "device": "LED", "device_pin": "Anode"}],
        }
        errors = get_validation_errors(config)
        assert errors == []

    def test_get_errors_for_invalid_config(self):
        """Test that invalid config returns error messages."""
        config = {"board": "invalid_board", "devices": [], "connections": []}
        errors = get_validation_errors(config)
        assert len(errors) > 0
        assert any("board" in err for err in errors)


class TestSchemaIntegration:
    """Integration tests for schema validation."""

    def test_complete_bh1750_example(self):
        """Test validation of complete BH1750 example."""
        config = {
            "title": "BH1750 Light Sensor",
            "board": "raspberry_pi_5",
            "devices": [{"type": "bh1750", "name": "Light Sensor"}],
            "connections": [
                {"board_pin": 1, "device": "Light Sensor", "device_pin": "VCC"},
                {"board_pin": 3, "device": "Light Sensor", "device_pin": "SDA"},
                {"board_pin": 5, "device": "Light Sensor", "device_pin": "SCL"},
                {"board_pin": 6, "device": "Light Sensor", "device_pin": "GND"},
            ],
            "show_legend": True,
        }
        result = validate_config(config)
        assert result.title == "BH1750 Light Sensor"
        assert len(result.connections) == 4

    def test_complete_led_with_resistor_example(self):
        """Test validation of LED with inline resistor."""
        config = {
            "title": "LED Circuit",
            "devices": [{"type": "led", "color": "Red", "name": "Status LED"}],
            "connections": [
                {
                    "board_pin": 11,
                    "device": "Status LED",
                    "device_pin": "Anode",
                    "color": "#FF0000",
                    "components": [{"type": "resistor", "value": "220Ω"}],
                },
                {"board_pin": 6, "device": "Status LED", "device_pin": "Cathode"},
            ],
        }
        result = validate_config(config)
        assert len(result.connections) == 2
        assert len(result.connections[0].components) == 1

    def test_mixed_device_types(self):
        """Test validation with mix of predefined and custom devices."""
        config = {
            "devices": [
                {"type": "led", "name": "LED1"},
                {
                    "name": "Custom Module",
                    "pins": [
                        {"name": "VIN", "role": "5V"},
                        {"name": "GND", "role": "GND"},
                    ],
                },
            ],
            "connections": [
                {"board_pin": 11, "device": "LED1", "device_pin": "Anode"},
                {"board_pin": 2, "device": "Custom Module", "device_pin": "VIN"},
            ],
        }
        result = validate_config(config)
        assert len(result.devices) == 2
        assert len(result.connections) == 2
