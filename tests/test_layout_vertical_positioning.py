"""Tests for smart vertical device positioning."""

import pytest

from pinviz.layout import LayoutConfig, LayoutEngine, RoutedWire
from pinviz.layout.positioning import DevicePositioner
from pinviz.model import (
    Board,
    Connection,
    Device,
    DevicePin,
    Diagram,
    HeaderPin,
    PinRole,
    Point,
)


@pytest.fixture
def pi5_like_board():
    """Create a Pi 5-like board with vertical pin layout."""
    pins = []
    # Create 20 pins distributed vertically (simulating Pi 5 GPIO header)
    for i in range(20):
        pin_num = i + 1
        y_pos = 16.2 + (i * 12.0)  # Pi 5 pin spacing
        pins.append(
            HeaderPin(
                number=pin_num,
                name=f"Pin{pin_num}",
                role=PinRole.GPIO if i % 2 == 0 else PinRole.GROUND,
                gpio_bcm=i if i % 2 == 0 else None,
                position=Point(187.1, y_pos),
            )
        )
    return Board(
        name="Pi 5 Like",
        pins=pins,
        svg_asset_path="test.svg",
        width=230,
        height=220,
    )


@pytest.fixture
def pico_like_board():
    """Create a Pico-like board with horizontal pin rows (top and bottom)."""
    pins = []
    # Top row pins (pins 1-20)
    for i in range(20):
        pin_num = i + 1
        x_pos = 8.0 + (i * 12.0)
        pins.append(
            HeaderPin(
                number=pin_num,
                name=f"GP{i}",
                role=PinRole.GPIO,
                gpio_bcm=i,
                position=Point(x_pos, 6.5),  # Top row Y
            )
        )
    # Bottom row pins (pins 21-40)
    for i in range(20):
        pin_num = 21 + i
        x_pos = 8.0 + (i * 12.0)
        pins.append(
            HeaderPin(
                number=pin_num,
                name=f"GP{20 + i}",
                role=PinRole.GPIO,
                gpio_bcm=20 + i,
                position=Point(x_pos, 94.0),  # Bottom row Y
            )
        )
    return Board(
        name="Pico Like",
        pins=pins,
        svg_asset_path="test.svg",
        width=250,
        height=101,
    )


@pytest.fixture
def simple_device():
    """Create a simple device for testing."""
    return Device(
        name="Test Device",
        pins=[
            DevicePin(name="VCC", role=PinRole.POWER_3V3, position=Point(0, 5)),
            DevicePin(name="GND", role=PinRole.GROUND, position=Point(0, 15)),
        ],
        width=60,
        height=40,
        color="#4A90E2",
    )


def test_get_board_vertical_range_pi5(pi5_like_board):
    """Test board vertical range calculation for Pi 5-like board."""
    config = LayoutConfig()
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[],
        connections=[],
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(True)
    positioner = DevicePositioner(config, board_margin_top)

    board_top, board_bottom = positioner._get_board_vertical_range(diagram)

    # Board should span from margin_top to margin_top + height
    assert board_top == board_margin_top
    assert board_bottom == board_margin_top + pi5_like_board.height
    assert board_bottom - board_top == 220  # Pi 5 height


def test_get_board_vertical_range_pico(pico_like_board):
    """Test board vertical range calculation for Pico-like board."""
    config = LayoutConfig()
    diagram = Diagram(
        title="Test",
        board=pico_like_board,
        devices=[],
        connections=[],
        show_title=False,
    )
    board_margin_top = config.get_board_margin_top(False)
    positioner = DevicePositioner(config, board_margin_top)

    board_top, board_bottom = positioner._get_board_vertical_range(diagram)

    assert board_top == board_margin_top
    assert board_bottom == board_margin_top + pico_like_board.height
    assert board_bottom - board_top == 101  # Pico height


def test_calculate_device_target_y_pi5_top_pins(pi5_like_board, simple_device):
    """Test target Y calculation for device connected to top pins on Pi 5."""
    config = LayoutConfig()
    # Device connected to pins 1, 2, 3 (top of board)
    connections = [
        Connection(1, "Test Device", "VCC"),
        Connection(2, "Test Device", "GND"),
    ]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(True)
    positioner = DevicePositioner(config, board_margin_top)

    target_y = positioner._calculate_device_target_y(simple_device, diagram)

    # Should be near top pins (around y=16-28)
    expected_y = (board_margin_top + 16.2 + board_margin_top + 28.2) / 2
    assert abs(target_y - expected_y) < 5


def test_calculate_device_target_y_pi5_bottom_pins(pi5_like_board, simple_device):
    """Test target Y calculation for device connected to bottom pins on Pi 5."""
    config = LayoutConfig()
    # Device connected to pins 19, 20 (bottom of board)
    connections = [
        Connection(19, "Test Device", "VCC"),
        Connection(20, "Test Device", "GND"),
    ]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(True)
    positioner = DevicePositioner(config, board_margin_top)

    target_y = positioner._calculate_device_target_y(simple_device, diagram)

    # Should be near bottom pins
    pin19_y = board_margin_top + 16.2 + (18 * 12.0)
    pin20_y = board_margin_top + 16.2 + (19 * 12.0)
    expected_y = (pin19_y + pin20_y) / 2
    assert abs(target_y - expected_y) < 5


def test_calculate_device_target_y_pico_top_row(pico_like_board, simple_device):
    """Test target Y calculation for device connected to top row on Pico."""
    config = LayoutConfig()
    # Device connected to top row pins
    connections = [
        Connection(1, "Test Device", "VCC"),
        Connection(2, "Test Device", "GND"),
    ]
    diagram = Diagram(
        title="Test",
        board=pico_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=False,
    )
    board_margin_top = config.get_board_margin_top(False)
    positioner = DevicePositioner(config, board_margin_top)

    target_y = positioner._calculate_device_target_y(simple_device, diagram)

    # Should be near top row (y ≈ 6.5)
    expected_y = board_margin_top + 6.5
    assert abs(target_y - expected_y) < 5


def test_calculate_device_target_y_pico_bottom_row(pico_like_board, simple_device):
    """Test target Y calculation for device connected to bottom row on Pico."""
    config = LayoutConfig()
    # Device connected to bottom row pins
    connections = [
        Connection(21, "Test Device", "VCC"),
        Connection(22, "Test Device", "GND"),
    ]
    diagram = Diagram(
        title="Test",
        board=pico_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=False,
    )
    board_margin_top = config.get_board_margin_top(False)
    positioner = DevicePositioner(config, board_margin_top)

    target_y = positioner._calculate_device_target_y(simple_device, diagram)

    # Should be near bottom row (y ≈ 94)
    expected_y = board_margin_top + 94.0
    assert abs(target_y - expected_y) < 5


def test_calculate_device_target_y_pico_both_rows(pico_like_board, simple_device):
    """Test target Y calculation for device connected to both rows on Pico."""
    config = LayoutConfig()
    # Device connected to both top and bottom rows
    connections = [
        Connection(1, "Test Device", "VCC"),  # Top row
        Connection(21, "Test Device", "GND"),  # Bottom row
    ]
    diagram = Diagram(
        title="Test",
        board=pico_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=False,
    )
    board_margin_top = config.get_board_margin_top(False)
    positioner = DevicePositioner(config, board_margin_top)

    target_y = positioner._calculate_device_target_y(simple_device, diagram)

    # Should be in middle (centroid of top and bottom)
    top_y = board_margin_top + 6.5
    bottom_y = board_margin_top + 94.0
    expected_y = (top_y + bottom_y) / 2
    assert abs(target_y - expected_y) < 5


def test_calculate_device_target_y_no_connections(pi5_like_board, simple_device):
    """Test target Y calculation for device with no connections (fallback)."""
    config = LayoutConfig()
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=[],  # No connections
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(True)
    positioner = DevicePositioner(config, board_margin_top)

    target_y = positioner._calculate_device_target_y(simple_device, diagram)

    # Should fallback to center of board
    board_top, board_bottom = positioner._get_board_vertical_range(diagram)
    expected_y = (board_top + board_bottom) / 2
    assert abs(target_y - expected_y) < 1


def test_calculate_min_device_y_with_title(pi5_like_board, simple_device):
    """Test minimum Y calculation with title shown."""
    config = LayoutConfig()
    connections = [Connection(1, "Test Device", "VCC")]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(True)
    positioner = DevicePositioner(config, board_margin_top)

    min_y = positioner._calculate_min_device_y(diagram)

    # Should respect title clearance
    title_bottom = config.board_margin_top_base + config.title_height
    min_y_with_clearance = title_bottom + config.title_margin
    assert min_y >= min_y_with_clearance


def test_calculate_min_device_y_without_title(pi5_like_board, simple_device):
    """Test minimum Y calculation without title shown."""
    config = LayoutConfig()
    connections = [Connection(1, "Test Device", "VCC")]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=False,
    )
    board_margin_top = config.get_board_margin_top(False)
    positioner = DevicePositioner(config, board_margin_top)

    min_y = positioner._calculate_min_device_y(diagram)

    # Should just use board margin top
    assert min_y == board_margin_top


def test_position_devices_vertically_smart_single_device(pi5_like_board, simple_device):
    """Test smart vertical positioning with single device."""
    config = LayoutConfig()
    connections = [Connection(10, "Test Device", "VCC")]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(True)
    positioner = DevicePositioner(config, board_margin_top)

    # Set initial X position
    simple_device.position = Point(450, 0)

    positioner._position_devices_vertically_smart([simple_device], diagram)

    # Device should be positioned (Y should be set)
    assert simple_device.position.y > 0
    # X should remain unchanged
    assert simple_device.position.x == 450


def test_position_devices_vertically_smart_multiple_devices(pi5_like_board):
    """Test smart vertical positioning with multiple devices."""
    config = LayoutConfig()

    # Create three devices
    device1 = Device(
        name="Device 1",
        pins=[DevicePin(name="VCC", role=PinRole.POWER_3V3, position=Point(0, 5))],
        width=60,
        height=40,
        color="#FF0000",
    )
    device2 = Device(
        name="Device 2",
        pins=[DevicePin(name="VCC", role=PinRole.POWER_3V3, position=Point(0, 5))],
        width=60,
        height=40,
        color="#00FF00",
    )
    device3 = Device(
        name="Device 3",
        pins=[DevicePin(name="VCC", role=PinRole.POWER_3V3, position=Point(0, 5))],
        width=60,
        height=40,
        color="#0000FF",
    )

    # Connect to top, middle, and bottom pins
    connections = [
        Connection(1, "Device 1", "VCC"),  # Top
        Connection(10, "Device 2", "VCC"),  # Middle
        Connection(20, "Device 3", "VCC"),  # Bottom
    ]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[device1, device2, device3],
        connections=connections,
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(True)
    positioner = DevicePositioner(config, board_margin_top)

    # Set initial X positions
    for device in diagram.devices:
        device.position = Point(450, 0)

    positioner._position_devices_vertically_smart(diagram.devices, diagram)

    # All devices should be positioned
    assert device1.position.y > 0
    assert device2.position.y > 0
    assert device3.position.y > 0

    # Devices should be ordered top to bottom
    assert device1.position.y < device2.position.y
    assert device2.position.y < device3.position.y

    # Devices should not overlap
    assert device1.position.y + device1.height <= device2.position.y
    assert device2.position.y + device2.height <= device3.position.y


def test_validate_wire_clearance_sufficient(pi5_like_board, simple_device):
    """Test wire clearance validation with sufficient clearance."""
    config = LayoutConfig()
    engine = LayoutEngine(config)
    connections = [Connection(10, "Test Device", "VCC")]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(diagram.show_title)

    # Create routed wires with good clearance
    routed_wires = [
        RoutedWire(
            connection=connections[0],
            path_points=[Point(100, 150), Point(200, 150)],  # Well below title
            color="#FF0000",
            from_pin_pos=Point(100, 150),
            to_pin_pos=Point(200, 150),
        )
    ]

    issues = engine._validate_wire_clearance(diagram, routed_wires, board_margin_top)
    assert len(issues) == 0


def test_validate_wire_clearance_insufficient(pi5_like_board, simple_device):
    """Test wire clearance validation with insufficient clearance."""
    config = LayoutConfig()
    engine = LayoutEngine(config)
    connections = [Connection(1, "Test Device", "VCC")]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=True,
    )
    board_margin_top = config.get_board_margin_top(diagram.show_title)

    # Create routed wires with insufficient clearance (too close to title)
    title_bottom = config.board_margin_top_base + config.title_height
    wire_y = title_bottom + 20  # Only 20px clearance (need 50px)

    routed_wires = [
        RoutedWire(
            connection=connections[0],
            path_points=[Point(100, wire_y), Point(200, wire_y)],
            color="#FF0000",
            from_pin_pos=Point(100, wire_y),
            to_pin_pos=Point(200, wire_y),
        )
    ]

    issues = engine._validate_wire_clearance(diagram, routed_wires, board_margin_top)
    assert len(issues) == 1
    assert "Wire clearance warning" in issues[0]
    assert "20.0px" in issues[0]


def test_validate_wire_clearance_no_title(pi5_like_board, simple_device):
    """Test wire clearance validation when title is not shown."""
    config = LayoutConfig()
    engine = LayoutEngine(config)
    connections = [Connection(1, "Test Device", "VCC")]
    diagram = Diagram(
        title="Test",
        board=pi5_like_board,
        devices=[simple_device],
        connections=connections,
        show_title=False,  # No title
    )
    board_margin_top = config.get_board_margin_top(diagram.show_title)

    routed_wires = [
        RoutedWire(
            connection=connections[0],
            path_points=[Point(100, 50), Point(200, 50)],
            color="#FF0000",
            from_pin_pos=Point(100, 50),
            to_pin_pos=Point(200, 50),
        )
    ]

    issues = engine._validate_wire_clearance(diagram, routed_wires, board_margin_top)
    assert len(issues) == 0  # No issues when title not shown
