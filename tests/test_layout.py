"""Tests for layout engine."""

from pinviz.devices import get_registry
from pinviz.layout import LayoutConfig, LayoutEngine, RoutedWire
from pinviz.model import Connection, Diagram, Point


def test_layout_config_defaults():
    """Test that LayoutConfig has sensible defaults."""
    config = LayoutConfig()
    assert config.board_margin_left == 40.0
    assert config.board_margin_top_base == 40.0
    assert config.title_height == 40.0
    assert config.title_margin == 50.0  # Increased to prevent wire overlap with title
    assert config.specs_table_top_margin == 30.0
    assert config.device_area_left == 450.0
    assert config.device_spacing_vertical == 20.0
    assert config.rail_offset == 40.0
    assert config.corner_radius == 5.0

    # Test dynamic board margin calculation
    assert config.get_board_margin_top(show_title=False) == 40.0  # Base only
    assert config.get_board_margin_top(show_title=True) == 130.0  # 40 + 40 + 50


def test_layout_config_custom_values():
    """Test creating LayoutConfig with custom values."""
    config = LayoutConfig(
        board_margin_left=50.0,
        device_spacing_vertical=30.0,
        corner_radius=10.0,
    )
    assert config.board_margin_left == 50.0
    assert config.device_spacing_vertical == 30.0
    assert config.corner_radius == 10.0


def test_routed_wire_creation(sample_connections):
    """Test creating a RoutedWire."""
    connection = sample_connections[0]
    path_points = [Point(0, 0), Point(100, 0), Point(100, 50)]
    wire = RoutedWire(
        connection=connection,
        path_points=path_points,
        color="#FF0000",
        from_pin_pos=Point(0, 0),
        to_pin_pos=Point(100, 50),
    )
    assert wire.connection == connection
    assert len(wire.path_points) == 3
    assert wire.color == "#FF0000"
    assert wire.from_pin_pos == Point(0, 0)
    assert wire.to_pin_pos == Point(100, 50)


def test_layout_engine_creation():
    """Test creating a LayoutEngine."""
    engine = LayoutEngine()
    assert engine is not None
    assert engine.config is not None


def test_layout_engine_with_custom_config():
    """Test creating LayoutEngine with custom config."""
    config = LayoutConfig(board_margin_left=100.0)
    engine = LayoutEngine(config)
    assert engine.config.board_margin_left == 100.0


def test_position_devices_vertically(sample_board, sample_device):
    """Test that devices are positioned correctly in single tier."""
    engine = LayoutEngine()

    # Create a diagram with one device connected to board
    connections = [Connection(1, "Test Device", "VCC")]
    diagram = Diagram(
        title="Test",
        board=sample_board,
        devices=[sample_device],
        connections=connections,
    )

    engine._position_devices_by_level(diagram)

    assert sample_device.position is not None
    assert sample_device.position.x == engine.config.device_area_left
    assert sample_device.position.y == engine.config.device_margin_top


def test_position_multiple_devices(sample_board, sample_device, bh1750_device):
    """Test positioning multiple devices with spacing in same tier."""
    engine = LayoutEngine()

    # Create diagram with two devices both connected to board (same tier)
    connections = [
        Connection(1, "Test Device", "VCC"),
        Connection(2, "BH1750 Light Sensor", "VCC"),
    ]
    diagram = Diagram(
        title="Test",
        board=sample_board,
        devices=[sample_device, bh1750_device],
        connections=connections,
    )

    engine._position_devices_by_level(diagram)

    # Both devices should be at same X (same tier)
    assert sample_device.position.x == engine.config.device_area_left
    assert bh1750_device.position.x == engine.config.device_area_left

    # First device at top
    assert sample_device.position.y == engine.config.device_margin_top

    # Second device should be below first with spacing
    expected_y = (
        engine.config.device_margin_top
        + sample_device.height
        + engine.config.device_spacing_vertical
    )
    assert bh1750_device.position.y == expected_y


def test_layout_diagram_returns_dimensions_and_wires(sample_diagram):
    """Test that layout_diagram returns canvas dimensions and wires."""
    engine = LayoutEngine()
    canvas_width, canvas_height, routed_wires = engine.layout_diagram(sample_diagram)

    assert isinstance(canvas_width, float)
    assert isinstance(canvas_height, float)
    assert canvas_width > 0
    assert canvas_height > 0
    assert isinstance(routed_wires, list)
    assert len(routed_wires) == len(sample_diagram.connections)


def test_layout_diagram_positions_devices(sample_diagram):
    """Test that layout_diagram positions devices."""
    engine = LayoutEngine()
    engine.layout_diagram(sample_diagram)

    for device in sample_diagram.devices:
        assert device.position is not None
        assert device.position.x > 0
        assert device.position.y > 0


def test_layout_diagram_routes_all_connections(sample_diagram):
    """Test that layout_diagram routes all connections."""
    engine = LayoutEngine()
    _, _, routed_wires = engine.layout_diagram(sample_diagram)

    assert len(routed_wires) == len(sample_diagram.connections)
    for wire in routed_wires:
        assert isinstance(wire, RoutedWire)
        assert wire.connection in sample_diagram.connections
        assert len(wire.path_points) > 0
        assert wire.color is not None


def test_canvas_size_includes_board(sample_diagram):
    """Test that canvas size includes the board with padding."""
    engine = LayoutEngine()
    canvas_width, canvas_height, _ = engine.layout_diagram(sample_diagram)

    # Canvas should be at least as large as board + margins + padding
    # Use dynamic board margin based on whether title is shown
    board_margin_top = engine.config.get_board_margin_top(sample_diagram.show_title)

    expected_min_width = (
        engine.config.board_margin_left + sample_diagram.board.width + engine.config.canvas_padding
    )
    expected_min_height = (
        board_margin_top + sample_diagram.board.height + engine.config.canvas_padding
    )
    assert canvas_width >= expected_min_width
    assert canvas_height >= expected_min_height


def test_canvas_size_includes_devices(sample_diagram):
    """Test that canvas size includes all devices."""
    engine = LayoutEngine()
    canvas_width, canvas_height, _ = engine.layout_diagram(sample_diagram)

    # Find the rightmost and bottommost device positions
    for device in sample_diagram.devices:
        device_right = device.position.x + device.width
        device_bottom = device.position.y + device.height
        assert canvas_width >= device_right
        assert canvas_height >= device_bottom


def test_routed_wires_have_path_points(sample_diagram):
    """Test that routed wires have path points."""
    engine = LayoutEngine()
    _, _, routed_wires = engine.layout_diagram(sample_diagram)

    for wire in routed_wires:
        assert len(wire.path_points) >= 2  # At least start and end
        assert isinstance(wire.path_points[0], Point)
        assert isinstance(wire.path_points[-1], Point)


def test_routed_wires_have_colors(sample_diagram):
    """Test that routed wires have assigned colors."""
    engine = LayoutEngine()
    _, _, routed_wires = engine.layout_diagram(sample_diagram)

    for wire in routed_wires:
        assert wire.color is not None
        assert isinstance(wire.color, str)
        # Should be a hex color or color name
        assert len(wire.color) > 0


def test_routed_wires_track_endpoints(sample_diagram):
    """Test that routed wires track from/to pin positions."""
    engine = LayoutEngine()
    _, _, routed_wires = engine.layout_diagram(sample_diagram)

    for wire in routed_wires:
        assert wire.from_pin_pos is not None
        assert wire.to_pin_pos is not None
        assert isinstance(wire.from_pin_pos, Point)
        assert isinstance(wire.to_pin_pos, Point)


def test_layout_with_single_device(rpi5_board, bh1750_device):
    """Test layout with a single device."""
    connections = [
        Connection(1, "BH1750 Light Sensor", "VCC"),
        Connection(6, "BH1750 Light Sensor", "GND"),
    ]
    diagram = Diagram(
        title="Single Device",
        board=rpi5_board,
        devices=[bh1750_device],
        connections=connections,
    )

    engine = LayoutEngine()
    canvas_width, canvas_height, routed_wires = engine.layout_diagram(diagram)

    assert canvas_width > 0
    assert canvas_height > 0
    assert len(routed_wires) == 2


def test_layout_with_multiple_devices(rpi5_board, bh1750_device, led_device):
    """Test layout with multiple devices."""
    # LED device name includes color, e.g., "Red LED"
    led_name = led_device.name

    connections = [
        Connection(1, "BH1750 Light Sensor", "VCC"),
        Connection(6, "BH1750 Light Sensor", "GND"),
        Connection(7, led_name, "+"),
        Connection(9, led_name, "-"),
    ]
    diagram = Diagram(
        title="Multiple Devices",
        board=rpi5_board,
        devices=[bh1750_device, led_device],
        connections=connections,
    )

    engine = LayoutEngine()
    canvas_width, canvas_height, routed_wires = engine.layout_diagram(diagram)

    # Devices should be positioned at different y coordinates
    assert diagram.devices[0].position.y != diagram.devices[1].position.y
    assert len(routed_wires) == 4


def test_layout_with_no_connections(rpi5_board, bh1750_device):
    """Test layout with devices but no connections."""
    diagram = Diagram(
        title="No Connections",
        board=rpi5_board,
        devices=[bh1750_device],
        connections=[],
    )

    engine = LayoutEngine()
    canvas_width, canvas_height, routed_wires = engine.layout_diagram(diagram)

    assert canvas_width > 0
    assert canvas_height > 0
    assert len(routed_wires) == 0
    # Device should still be positioned
    assert bh1750_device.position is not None


def test_custom_device_spacing(sample_diagram):
    """Test layout with custom device spacing."""
    config = LayoutConfig(device_spacing_vertical=50.0)
    engine = LayoutEngine(config)

    # Add second device for spacing test
    sample_diagram.devices.append(get_registry().create("bh1750"))

    engine.layout_diagram(sample_diagram)

    # Check spacing between devices
    device1_bottom = sample_diagram.devices[0].position.y + sample_diagram.devices[0].height
    device2_top = sample_diagram.devices[1].position.y
    spacing = device2_top - device1_bottom

    assert spacing == config.device_spacing_vertical


def test_custom_device_area_position(sample_diagram):
    """Test layout with custom device area position."""
    config = LayoutConfig(device_area_left=600.0)
    engine = LayoutEngine(config)

    engine.layout_diagram(sample_diagram)

    for device in sample_diagram.devices:
        assert device.position.x == config.device_area_left


# Multi-tier layout tests
def test_single_tier_layout(sample_board):
    """Test single-tier layout where all devices are connected to board."""
    from pinviz.model import Device, DevicePin, PinRole, Point

    # Create three simple devices with custom names
    device_a = Device(
        name="Device A",
        pins=[DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0))],
        width=60,
        height=40,
        color="#4A90E2",
    )
    device_b = Device(
        name="Device B",
        pins=[DevicePin("+", PinRole.POWER_3V3, Point(0, 0))],
        width=60,
        height=40,
        color="#E24A4A",
    )
    device_c = Device(
        name="Device C",
        pins=[DevicePin("OUT", PinRole.GPIO, Point(0, 0))],
        width=60,
        height=40,
        color="#4AE24A",
    )

    # All connections are board-to-device (no device-to-device)
    connections = [
        Connection(1, "Device A", "VCC"),
        Connection(2, "Device B", "+"),
        Connection(3, "Device C", "OUT"),
    ]

    diagram = Diagram(
        title="Single Tier Test",
        board=sample_board,
        devices=[device_a, device_b, device_c],
        connections=connections,
    )

    engine = LayoutEngine()
    engine.layout_diagram(diagram)

    # All devices should be at same X position (same tier/level 0)
    x_positions = [device.position.x for device in diagram.devices]
    assert len(set(x_positions)) == 1, "All devices should be in the same tier"


def test_multi_tier_layout_linear_chain(sample_board):
    """Test multi-tier layout with linear chain: Board → A → B → C."""
    from pinviz.model import Device, DevicePin, PinRole, Point

    # Create three devices in a linear chain
    device_a = Device(
        name="Device A",
        pins=[
            DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
            DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
        ],
        width=60,
        height=40,
        color="#4A90E2",
    )
    device_b = Device(
        name="Device B",
        pins=[
            DevicePin("IN", PinRole.GPIO, Point(0, 0)),
            DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
        ],
        width=60,
        height=40,
        color="#E24A4A",
    )
    device_c = Device(
        name="Device C",
        pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
        width=60,
        height=40,
        color="#4AE24A",
    )

    # Linear chain: Board → A → B → C
    connections = [
        # Board to A
        Connection(board_pin=1, device_name="Device A", device_pin_name="VCC"),
        # A to B (device-to-device)
        Connection(
            source_device="Device A",
            source_pin="OUT",
            device_name="Device B",
            device_pin_name="IN",
        ),
        # B to C (device-to-device)
        Connection(
            source_device="Device B",
            source_pin="OUT",
            device_name="Device C",
            device_pin_name="IN",
        ),
    ]

    diagram = Diagram(
        title="Linear Chain Test",
        board=sample_board,
        devices=[device_a, device_b, device_c],
        connections=connections,
    )

    engine = LayoutEngine()
    engine.layout_diagram(diagram)

    # Devices should be at increasing X positions (different tiers)
    pos_a = device_a.position.x
    pos_b = device_b.position.x
    pos_c = device_c.position.x

    assert pos_a < pos_b < pos_c, "Devices should be positioned in increasing tiers"


def test_branching_layout(sample_board):
    """Test branching layout: Board → A → [B, C] (B and C at same level)."""
    from pinviz.model import Device, DevicePin, PinRole, Point

    # Create three devices where A branches to B and C
    device_a = Device(
        name="Device A",
        pins=[
            DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
            DevicePin("OUT1", PinRole.GPIO, Point(0, 10)),
            DevicePin("OUT2", PinRole.GPIO, Point(0, 20)),
        ],
        width=60,
        height=40,
        color="#4A90E2",
    )
    device_b = Device(
        name="Device B",
        pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
        width=60,
        height=40,
        color="#E24A4A",
    )
    device_c = Device(
        name="Device C",
        pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
        width=60,
        height=40,
        color="#4AE24A",
    )

    # Branching: Board → A, then A → B and A → C
    connections = [
        # Board to A
        Connection(board_pin=1, device_name="Device A", device_pin_name="VCC"),
        # A to B
        Connection(
            source_device="Device A",
            source_pin="OUT1",
            device_name="Device B",
            device_pin_name="IN",
        ),
        # A to C
        Connection(
            source_device="Device A",
            source_pin="OUT2",
            device_name="Device C",
            device_pin_name="IN",
        ),
    ]

    diagram = Diagram(
        title="Branching Test",
        board=sample_board,
        devices=[device_a, device_b, device_c],
        connections=connections,
    )

    engine = LayoutEngine()
    engine.layout_diagram(diagram)

    pos_a = device_a.position
    pos_b = device_b.position
    pos_c = device_c.position

    # B and C should be at same X (same tier/level)
    assert pos_b.x == pos_c.x, "B and C should be at the same tier"

    # B and C should be at different Y (stacked vertically)
    assert pos_b.y != pos_c.y, "B and C should be stacked vertically"

    # A should be at a smaller X (earlier tier)
    assert pos_a.x < pos_b.x, "A should be at an earlier tier than B and C"
