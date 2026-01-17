"""Tests for the core data model."""

import pytest

from pinviz.model import (
    Component,
    ComponentType,
    Connection,
    Device,
    DevicePin,
    Diagram,
    HeaderPin,
    PinRole,
    Point,
    WireColor,
    WireStyle,
)


def test_pin_role_values():
    """Test that PinRole enum has expected values."""
    assert PinRole.POWER_3V3.value == "3V3"
    assert PinRole.POWER_5V.value == "5V"
    assert PinRole.GROUND.value == "GND"
    assert PinRole.GPIO.value == "GPIO"
    assert PinRole.I2C_SDA.value == "I2C_SDA"
    assert PinRole.I2C_SCL.value == "I2C_SCL"


def test_pin_role_is_string_enum():
    """Test that PinRole is a string enum."""
    # PinRole is a string enum - check value attribute
    assert PinRole.GPIO.value == "GPIO"
    # Note: str() on enum returns "EnumName.VALUE" format
    assert "GPIO" in str(PinRole.GPIO)


def test_wire_color_values():
    """Test that WireColor enum has expected values."""
    assert WireColor.RED.value == "#FF0000"
    assert WireColor.BLACK.value == "#000000"
    assert WireColor.BLUE.value == "#0000FF"


def test_wire_color_is_string_enum():
    """Test that WireColor is a string enum."""
    assert isinstance(WireColor.RED, str)


def test_wire_style_values():
    """Test that WireStyle enum has expected values."""
    assert WireStyle.ORTHOGONAL.value == "orthogonal"
    assert WireStyle.CURVED.value == "curved"
    assert WireStyle.MIXED.value == "mixed"


def test_component_type_values():
    """Test that ComponentType enum has expected values."""
    assert ComponentType.RESISTOR.value == "resistor"
    assert ComponentType.CAPACITOR.value == "capacitor"
    assert ComponentType.DIODE.value == "diode"


def test_point_creation():
    """Test creating a Point."""
    p = Point(x=10.5, y=20.3)
    assert p.x == 10.5
    assert p.y == 20.3


def test_point_equality():
    """Test Point equality."""
    p1 = Point(10, 20)
    p2 = Point(10, 20)
    p3 = Point(11, 20)
    assert p1 == p2
    assert p1 != p3


def test_header_pin_creation():
    """Test creating a HeaderPin."""
    pin = HeaderPin(
        number=1, name="3V3", role=PinRole.POWER_3V3, gpio_bcm=None, position=Point(10, 20)
    )
    assert pin.number == 1
    assert pin.name == "3V3"
    assert pin.role == PinRole.POWER_3V3
    assert pin.gpio_bcm is None
    assert pin.position == Point(10, 20)


def test_header_pin_with_gpio():
    """Test creating a GPIO HeaderPin."""
    pin = HeaderPin(
        number=3, name="GPIO2", role=PinRole.I2C_SDA, gpio_bcm=2, position=Point(10, 30)
    )
    assert pin.gpio_bcm == 2
    assert pin.role == PinRole.I2C_SDA


def test_board_creation(sample_board):
    """Test creating a Board."""
    assert sample_board.name == "Test Board"
    assert len(sample_board.pins) == 6
    assert sample_board.width == 200
    assert sample_board.height == 150


def test_board_get_pin_by_number(sample_board):
    """Test getting a pin by physical pin number."""
    pin = sample_board.get_pin_by_number(1)
    assert pin is not None
    assert pin.name == "3V3"
    assert pin.role == PinRole.POWER_3V3


def test_board_get_pin_by_number_not_found(sample_board):
    """Test getting a non-existent pin by number."""
    pin = sample_board.get_pin_by_number(99)
    assert pin is None


def test_board_get_pin_by_bcm(sample_board):
    """Test getting a pin by BCM GPIO number."""
    pin = sample_board.get_pin_by_bcm(2)
    assert pin is not None
    assert pin.name == "GPIO2"
    assert pin.role == PinRole.I2C_SDA


def test_board_get_pin_by_bcm_not_found(sample_board):
    """Test getting a non-existent pin by BCM number."""
    pin = sample_board.get_pin_by_bcm(99)
    assert pin is None


def test_board_get_pin_by_name(sample_board):
    """Test getting a pin by name."""
    pin = sample_board.get_pin_by_name("GPIO2")
    assert pin is not None
    assert pin.number == 3
    assert pin.gpio_bcm == 2


def test_board_get_pin_by_name_not_found(sample_board):
    """Test getting a non-existent pin by name."""
    pin = sample_board.get_pin_by_name("INVALID")
    assert pin is None


def test_device_pin_creation():
    """Test creating a DevicePin."""
    pin = DevicePin(name="VCC", role=PinRole.POWER_3V3, position=Point(0, 0))
    assert pin.name == "VCC"
    assert pin.role == PinRole.POWER_3V3
    assert pin.position == Point(0, 0)


def test_device_pin_default_position():
    """Test DevicePin with default position."""
    pin = DevicePin(name="SDA", role=PinRole.I2C_SDA)
    assert pin.position == Point(0, 0)


def test_device_creation(sample_device):
    """Test creating a Device."""
    assert sample_device.name == "Test Device"
    assert len(sample_device.pins) == 4
    assert sample_device.width == 60
    assert sample_device.height == 40
    assert sample_device.color == "#4A90E2"


def test_device_get_pin_by_name(sample_device):
    """Test getting a device pin by name."""
    pin = sample_device.get_pin_by_name("VCC")
    assert pin is not None
    assert pin.role == PinRole.POWER_3V3


def test_device_get_pin_by_name_not_found(sample_device):
    """Test getting a non-existent device pin by name."""
    pin = sample_device.get_pin_by_name("INVALID")
    assert pin is None


def test_device_default_values():
    """Test Device with default values."""
    device = Device(name="Test", pins=[])
    assert device.width == 80.0
    assert device.height == 40.0
    assert device.position == Point(0, 0)
    assert device.color == "#4A90E2"


def test_component_creation():
    """Test creating a Component."""
    comp = Component(type=ComponentType.RESISTOR, value="220Ω", position=0.6)
    assert comp.type == ComponentType.RESISTOR
    assert comp.value == "220Ω"
    assert comp.position == 0.6


def test_component_default_position():
    """Test Component with default position."""
    comp = Component(type=ComponentType.CAPACITOR, value="100µF")
    assert comp.position == 0.55


def test_connection_creation():
    """Test creating a Connection."""
    conn = Connection(board_pin=1, device_name="Device1", device_pin_name="VCC")
    assert conn.board_pin == 1
    assert conn.device_name == "Device1"
    assert conn.device_pin_name == "VCC"
    assert conn.color is None
    assert conn.style == WireStyle.MIXED


def test_connection_with_color():
    """Test Connection with custom color."""
    conn = Connection(
        board_pin=1,
        device_name="Device1",
        device_pin_name="VCC",
        color="#FF0000",
        style=WireStyle.CURVED,
    )
    assert conn.color == "#FF0000"
    assert conn.style == WireStyle.CURVED


def test_connection_with_components():
    """Test Connection with inline components."""
    resistor = Component(type=ComponentType.RESISTOR, value="220Ω")
    conn = Connection(
        board_pin=7,
        device_name="LED",
        device_pin_name="Anode",
        components=[resistor],
    )
    assert len(conn.components) == 1
    assert conn.components[0].type == ComponentType.RESISTOR


def test_connection_with_net_name():
    """Test Connection with net name."""
    conn = Connection(board_pin=1, device_name="Device1", device_pin_name="VCC", net_name="VCC_3V3")
    assert conn.net_name == "VCC_3V3"


def test_board_connection_creation():
    """Test creating board-to-device connection."""
    conn = Connection(board_pin=1, device_name="LED", device_pin_name="VCC")
    assert conn.is_board_connection()
    assert not conn.is_device_connection()
    assert conn.board_pin == 1
    assert conn.device_name == "LED"
    assert conn.device_pin_name == "VCC"


def test_device_connection_creation():
    """Test creating device-to-device connection."""
    conn = Connection(
        source_device="Reg",
        source_pin="OUT",
        device_name="LED",
        device_pin_name="VCC",
    )
    assert conn.is_device_connection()
    assert not conn.is_board_connection()
    assert conn.source_device == "Reg"
    assert conn.source_pin == "OUT"


def test_invalid_connection_both_sources():
    """Test that specifying both sources raises error."""
    with pytest.raises(ValueError, match="Cannot specify both"):
        Connection(
            board_pin=1,
            source_device="Reg",
            source_pin="OUT",
            device_name="LED",
            device_pin_name="VCC",
        )


def test_invalid_connection_no_source():
    """Test that missing source raises error."""
    with pytest.raises(ValueError, match="Must specify either"):
        Connection(device_name="LED", device_pin_name="VCC")


def test_invalid_connection_partial_device_source():
    """Test that only specifying source_device without source_pin raises error."""
    with pytest.raises(ValueError, match="Must specify either"):
        Connection(source_device="Reg", device_name="LED", device_pin_name="VCC")


def test_invalid_connection_partial_device_source_pin_only():
    """Test that only specifying source_pin without source_device raises error."""
    with pytest.raises(ValueError, match="Must specify either"):
        Connection(source_pin="OUT", device_name="LED", device_pin_name="VCC")


def test_factory_method_from_board():
    """Test from_board factory method."""
    conn = Connection.from_board(1, "LED", "VCC", color="#FF0000")
    assert conn.is_board_connection()
    assert conn.board_pin == 1
    assert conn.device_name == "LED"
    assert conn.color == "#FF0000"


def test_factory_method_from_device():
    """Test from_device factory method."""
    conn = Connection.from_device("A", "OUT", "B", "IN", color="#00FF00")
    assert conn.is_device_connection()
    assert conn.source_device == "A"
    assert conn.source_pin == "OUT"
    assert conn.device_name == "B"
    assert conn.device_pin_name == "IN"
    assert conn.color == "#00FF00"


def test_get_source_board_connection():
    """Test get_source for board connection."""
    conn = Connection.from_board(1, "LED", "VCC")
    source = conn.get_source()
    assert source == ("board", "1")


def test_get_source_device_connection():
    """Test get_source for device connection."""
    conn = Connection.from_device("A", "OUT", "B", "IN")
    source = conn.get_source()
    assert source == ("A", "OUT")


def test_diagram_creation(sample_diagram):
    """Test creating a Diagram."""
    assert sample_diagram.title == "Test Diagram"
    assert sample_diagram.board.name == "Test Board"
    assert len(sample_diagram.devices) == 1
    assert len(sample_diagram.connections) == 4
    assert sample_diagram.show_legend is False


def test_diagram_default_values(sample_board, sample_device):
    """Test Diagram with default values."""
    diagram = Diagram(
        title="Simple Test",
        board=sample_board,
        devices=[sample_device],
        connections=[],
    )
    assert diagram.show_legend is False
    assert diagram.show_gpio_diagram is False
    assert diagram.canvas_width == 800.0
    assert diagram.canvas_height == 600.0


def test_diagram_custom_canvas_size(sample_board):
    """Test Diagram with custom canvas size."""
    diagram = Diagram(
        title="Custom Size",
        board=sample_board,
        devices=[],
        connections=[],
        canvas_width=1024.0,
        canvas_height=768.0,
    )
    assert diagram.canvas_width == 1024.0
    assert diagram.canvas_height == 768.0
