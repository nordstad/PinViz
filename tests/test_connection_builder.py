"""Unit tests for the connection builder module."""

from pinviz.model import Diagram, PinRole
from pinviz_mcp.connection_builder import (
    ConnectionBuilder,
    build_diagram_from_assignments,
)
from pinviz_mcp.pin_assignment import PinAssignment


class TestConnectionBuilder:
    """Test suite for ConnectionBuilder class."""

    def test_initialization(self):
        """Test that builder initializes correctly."""
        builder = ConnectionBuilder()
        assert builder is not None

    def test_get_board_raspberry_pi_5(self):
        """Test getting Raspberry Pi 5 board."""
        builder = ConnectionBuilder()
        board = builder._get_board("raspberry_pi_5")

        assert board.name == "Raspberry Pi"
        assert len(board.pins) == 40

    def test_get_board_default(self):
        """Test that unknown board names default to Raspberry Pi."""
        builder = ConnectionBuilder()
        board = builder._get_board("unknown_board")

        assert board.name == "Raspberry Pi"

    def test_build_single_device(self):
        """Test building a single device."""
        builder = ConnectionBuilder()

        device_data = [
            {
                "name": "BME280 Sensor",
                "category": "sensor",
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "SCL", "role": "I2C_SCL"},
                    {"name": "SDA", "role": "I2C_SDA"},
                ],
            }
        ]

        devices = builder._build_devices(device_data)

        assert len(devices) == 1
        device = devices[0]
        assert device.name == "BME280 Sensor"
        assert len(device.pins) == 4
        assert device.width == 120.0

    def test_build_multiple_devices(self):
        """Test building multiple devices."""
        builder = ConnectionBuilder()

        devices_data = [
            {
                "name": "Device 1",
                "category": "sensor",
                "pins": [{"name": "VCC", "role": "3V3"}],
            },
            {
                "name": "Device 2",
                "category": "display",
                "pins": [{"name": "GND", "role": "GND"}],
            },
        ]

        devices = builder._build_devices(devices_data)

        assert len(devices) == 2
        assert devices[0].name == "Device 1"
        assert devices[1].name == "Device 2"

    def test_device_color_by_category(self):
        """Test that device colors are assigned based on category."""
        builder = ConnectionBuilder()

        categories_and_colors = [
            ("display", "#4A90E2"),
            ("sensor", "#50E3C2"),
            ("actuator", "#F5A623"),
            ("hat", "#BD10E0"),
            ("breakout", "#7ED321"),
            ("component", "#F8E71C"),
        ]

        for category, expected_color in categories_and_colors:
            device_data = {"category": category, "name": "Test"}
            color = builder._get_device_color(device_data)
            assert color == expected_color

    def test_device_color_default(self):
        """Test default device color for unknown category."""
        builder = ConnectionBuilder()

        device_data = {"category": "unknown", "name": "Test"}
        color = builder._get_device_color(device_data)

        assert color == "#4A90E2"  # Default blue

    def test_build_connections(self):
        """Test building connections from assignments."""
        builder = ConnectionBuilder()

        assignments = [
            PinAssignment(
                board_pin_number=3,
                device_name="BME280",
                device_pin_name="SDA",
                pin_role=PinRole.I2C_SDA,
            ),
            PinAssignment(
                board_pin_number=5,
                device_name="BME280",
                device_pin_name="SCL",
                pin_role=PinRole.I2C_SCL,
            ),
        ]

        connections = builder._build_connections(assignments)

        assert len(connections) == 2
        assert connections[0].board_pin == 3
        assert connections[0].device_name == "BME280"
        assert connections[0].device_pin_name == "SDA"
        assert connections[1].board_pin == 5
        assert connections[1].device_name == "BME280"
        assert connections[1].device_pin_name == "SCL"

    def test_wire_color_assignment(self):
        """Test that wire colors are assigned based on pin roles."""
        builder = ConnectionBuilder()

        assignments = [
            PinAssignment(
                board_pin_number=1,
                device_name="Device",
                device_pin_name="VCC",
                pin_role=PinRole.POWER_3V3,
            ),
            PinAssignment(
                board_pin_number=6,
                device_name="Device",
                device_pin_name="GND",
                pin_role=PinRole.GROUND,
            ),
            PinAssignment(
                board_pin_number=3,
                device_name="Device",
                device_pin_name="SDA",
                pin_role=PinRole.I2C_SDA,
            ),
        ]

        connections = builder._build_connections(assignments)

        # Check that colors match DEFAULT_COLORS
        assert connections[0].color == "#FF8C00"  # Orange for 3.3V
        assert connections[1].color == "#000000"  # Black for GND
        assert connections[2].color == "#00FF00"  # Green for I2C_SDA

    def test_build_complete_diagram(self):
        """Test building a complete diagram."""
        builder = ConnectionBuilder()

        assignments = [
            PinAssignment(
                board_pin_number=3,
                device_name="BME280 Sensor",
                device_pin_name="SDA",
                pin_role=PinRole.I2C_SDA,
            ),
            PinAssignment(
                board_pin_number=1,
                device_name="BME280 Sensor",
                device_pin_name="VCC",
                pin_role=PinRole.POWER_3V3,
            ),
        ]

        devices_data = [
            {
                "name": "BME280 Sensor",
                "category": "sensor",
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "SDA", "role": "I2C_SDA"},
                ],
            }
        ]

        diagram = builder.build_diagram(
            assignments=assignments,
            devices_data=devices_data,
            board_name="raspberry_pi_5",
            title="Test Diagram",
        )

        assert isinstance(diagram, Diagram)
        assert diagram.title == "Test Diagram"
        assert diagram.board.name == "Raspberry Pi"
        assert len(diagram.devices) == 1
        assert len(diagram.connections) == 2
        assert diagram.show_legend is True

    def test_convenience_function(self):
        """Test the convenience function."""
        assignments = [
            PinAssignment(
                board_pin_number=3,
                device_name="LED",
                device_pin_name="SIG",
                pin_role=PinRole.GPIO,
            ),
        ]

        devices_data = [
            {
                "name": "LED",
                "category": "component",
                "pins": [{"name": "SIG", "role": "GPIO"}],
            }
        ]

        diagram = build_diagram_from_assignments(
            assignments=assignments,
            devices_data=devices_data,
            board_name="raspberry_pi_5",
            title="LED Diagram",
        )

        assert isinstance(diagram, Diagram)
        assert diagram.title == "LED Diagram"

    def test_device_height_scales_with_pins(self):
        """Test that device height scales with number of pins."""
        builder = ConnectionBuilder()

        devices_data = [
            {
                "name": "Device with many pins",
                "category": "sensor",
                "pins": [{"name": f"Pin{i}", "role": "GPIO"} for i in range(10)],
            }
        ]

        devices = builder._build_devices(devices_data)

        device = devices[0]
        # Height should be at least: num_pins * 10 + 20
        expected_min_height = 10 * 10 + 20
        assert device.height >= expected_min_height

    def test_mixed_wire_style(self):
        """Test that connections use 'mixed' wire style."""
        builder = ConnectionBuilder()

        assignments = [
            PinAssignment(
                board_pin_number=3,
                device_name="Device",
                device_pin_name="Pin",
                pin_role=PinRole.GPIO,
            ),
        ]

        connections = builder._build_connections(assignments)

        assert connections[0].style == "mixed"

    def test_empty_assignments(self):
        """Test building diagram with no assignments."""
        builder = ConnectionBuilder()

        diagram = builder.build_diagram(
            assignments=[],
            devices_data=[],
            board_name="raspberry_pi_5",
            title="Empty Diagram",
        )

        assert isinstance(diagram, Diagram)
        assert len(diagram.devices) == 0
        assert len(diagram.connections) == 0

    def test_device_pin_positions(self):
        """Test that device pins are positioned correctly."""
        builder = ConnectionBuilder()

        device_data = [
            {
                "name": "Test Device",
                "category": "sensor",
                "pins": [
                    {"name": "Pin1", "role": "3V3"},
                    {"name": "Pin2", "role": "GND"},
                    {"name": "Pin3", "role": "GPIO"},
                ],
            }
        ]

        devices = builder._build_devices(device_data)
        device = devices[0]

        # Pins should be vertically spaced by 10 units
        assert device.pins[0].position.y == 0
        assert device.pins[1].position.y == 10
        assert device.pins[2].position.y == 20

    def test_complex_diagram_with_multiple_devices(self):
        """Test building a complex diagram with multiple devices and connections."""
        builder = ConnectionBuilder()

        assignments = [
            # BME280 I2C device
            PinAssignment(3, "BME280", "SDA", PinRole.I2C_SDA),
            PinAssignment(5, "BME280", "SCL", PinRole.I2C_SCL),
            PinAssignment(1, "BME280", "VCC", PinRole.POWER_3V3),
            PinAssignment(6, "BME280", "GND", PinRole.GROUND),
            # LED GPIO device
            PinAssignment(7, "LED", "SIG", PinRole.GPIO),
            PinAssignment(9, "LED", "GND", PinRole.GROUND),
        ]

        devices_data = [
            {
                "name": "BME280",
                "category": "sensor",
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "SCL", "role": "I2C_SCL"},
                    {"name": "SDA", "role": "I2C_SDA"},
                ],
            },
            {
                "name": "LED",
                "category": "component",
                "pins": [
                    {"name": "SIG", "role": "GPIO"},
                    {"name": "GND", "role": "GND"},
                ],
            },
        ]

        diagram = builder.build_diagram(
            assignments=assignments,
            devices_data=devices_data,
            title="Complex Diagram",
        )

        assert len(diagram.devices) == 2
        assert len(diagram.connections) == 6

        # Verify device names
        device_names = [d.name for d in diagram.devices]
        assert "BME280" in device_names
        assert "LED" in device_names

        # Verify connection count per device
        bme280_connections = [c for c in diagram.connections if c.device_name == "BME280"]
        led_connections = [c for c in diagram.connections if c.device_name == "LED"]

        assert len(bme280_connections) == 4
        assert len(led_connections) == 2
