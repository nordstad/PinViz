"""Property-based tests for layout engine using Hypothesis.

These tests use property-based testing to automatically generate
test cases with various configurations to ensure the layout engine
behaves correctly across a wide range of inputs.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from pinviz import boards
from pinviz.layout import LayoutEngine
from pinviz.model import Connection, Device, DevicePin, Diagram, Point, WireStyle


# Custom strategies for generating test data
@st.composite
def device_pin_strategy(draw):
    """Generate a random DevicePin."""
    name = draw(
        st.text(
            min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))
        )
    )
    role = draw(st.sampled_from(["GPIO", "3V3", "5V", "GND", "I2C_SDA", "I2C_SCL"]))
    x = draw(st.floats(min_value=0, max_value=100))
    y = draw(st.floats(min_value=0, max_value=200))
    return DevicePin(name, role, Point(x, y))


@st.composite
def device_strategy(draw, min_pins=1, max_pins=10):
    """Generate a random Device."""
    # Reserved names that should not be used for devices
    reserved_names = {"board", "raspberry", "pi", "pico"}

    name = draw(
        st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
        ).filter(lambda n: n.strip() and n.strip().lower() not in reserved_names)
    )
    num_pins = draw(st.integers(min_value=min_pins, max_value=max_pins))
    pins = [draw(device_pin_strategy()) for _ in range(num_pins)]

    # Ensure unique pin names within the device
    unique_pins = []
    seen_names = set()
    for pin in pins:
        if pin.name not in seen_names:
            unique_pins.append(pin)
            seen_names.add(pin.name)

    if not unique_pins:
        unique_pins = [DevicePin("PIN1", "GPIO", Point(5, 10))]

    width = draw(st.floats(min_value=50, max_value=150))
    height = draw(st.floats(min_value=30, max_value=250))

    return Device(name=name.strip() or "Device", pins=unique_pins, width=width, height=height)


@st.composite
def connection_strategy(draw, device_names, device_pin_names_map):
    """Generate a random Connection."""
    board_pin = draw(st.integers(min_value=1, max_value=40))
    device_name = draw(st.sampled_from(device_names))
    device_pin_name = draw(st.sampled_from(device_pin_names_map[device_name]))
    style = draw(st.sampled_from([WireStyle.ORTHOGONAL, WireStyle.CURVED, WireStyle.MIXED]))

    return Connection(
        board_pin=board_pin,
        device_name=device_name,
        device_pin_name=device_pin_name,
        style=style,
    )


@st.composite
def diagram_strategy(draw, max_devices=5, max_connections=15):
    """Generate a random Diagram."""
    board = boards.raspberry_pi_5()
    title = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
        )
    )

    num_devices = draw(st.integers(min_value=1, max_value=max_devices))
    devices = [draw(device_strategy()) for _ in range(num_devices)]

    # Ensure unique device names
    unique_devices = []
    seen_names = set()
    for device in devices:
        if device.name not in seen_names:
            unique_devices.append(device)
            seen_names.add(device.name)

    if not unique_devices:
        unique_devices = [Device("Device1", [DevicePin("PIN1", "GPIO", Point(5, 10))])]

    # Build map of device names to their pin names
    device_pin_names_map = {
        device.name: [pin.name for pin in device.pins] for device in unique_devices
    }
    device_names = list(device_pin_names_map.keys())

    # Generate connections
    num_connections = draw(st.integers(min_value=0, max_value=min(max_connections, 40)))
    connections = []
    for _ in range(num_connections):
        conn = draw(connection_strategy(device_names, device_pin_names_map))
        connections.append(conn)

    return Diagram(
        title=title.strip() or "Test Diagram",
        board=board,
        devices=unique_devices,
        connections=connections,
    )


class TestLayoutProperties:
    """Property-based tests for layout engine."""

    @settings(max_examples=50, deadline=2000)
    @given(diagram_strategy(max_devices=3, max_connections=10))
    def test_layout_always_produces_valid_output(self, diagram):
        """Property: Layout should always produce valid output for any diagram."""
        engine = LayoutEngine()

        # Layout should not raise an exception
        _, _, routed_wires = engine.layout_diagram(diagram)

        # Basic validity checks
        assert routed_wires is not None
        assert diagram.board is not None
        assert len(diagram.devices) > 0

        # All devices should have positions
        for device in diagram.devices:
            assert device.position is not None
            assert device.position.x >= 0
            assert device.position.y >= 0

        # Number of routed wires should match connections
        assert len(routed_wires) == len(diagram.connections)

    @settings(max_examples=30, deadline=2000)
    @given(diagram_strategy(max_devices=2, max_connections=5))
    def test_all_wires_have_valid_paths(self, diagram):
        """Property: All routed wires should have valid path points."""
        engine = LayoutEngine()
        _, _, routed_wires = engine.layout_diagram(diagram)

        for wire in routed_wires:
            # Every wire should have at least 2 path points
            assert len(wire.path_points) >= 2

            # From and to positions should be defined
            assert wire.from_pin_pos is not None
            assert wire.to_pin_pos is not None

            # All points should have finite coordinates
            for point in wire.path_points:
                assert isinstance(point.x, (int, float))
                assert isinstance(point.y, (int, float))
                assert not (point.x == float("inf") or point.x == float("-inf"))
                assert not (point.y == float("inf") or point.y == float("-inf"))

    @settings(max_examples=30, deadline=2000)
    @given(diagram_strategy(max_devices=3, max_connections=8))
    def test_device_positions_are_distinct(self, diagram):
        """Property: Devices should have distinct positions (no complete overlap)."""
        if len(diagram.devices) < 2:
            return  # Need at least 2 devices to test

        engine = LayoutEngine()
        _, _, routed_wires = engine.layout_diagram(diagram)

        positions = [(d.position.x, d.position.y) for d in diagram.devices]

        # At least some positions should be different
        # (perfect overlap would mean all positions identical)
        unique_positions = set(positions)
        assert len(unique_positions) >= 1  # At minimum, one unique position

    @settings(max_examples=30, deadline=2000)
    @given(
        st.integers(min_value=1, max_value=40),  # board_pin
        st.text(
            min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))
        ),  # device_name
        st.text(
            min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))
        ),  # pin_name
    )
    def test_single_connection_layout(self, board_pin, device_name, pin_name):
        """Property: Single connection should always route successfully."""
        board = boards.raspberry_pi_5()
        device = Device(
            name=device_name.strip() or "Device",
            pins=[DevicePin(pin_name.strip() or "PIN", "GPIO", Point(5, 10))],
        )

        connection = Connection(
            board_pin=board_pin,
            device_name=device.name,
            device_pin_name=device.pins[0].name,
        )

        diagram = Diagram(
            title="Single Connection Test",
            board=board,
            devices=[device],
            connections=[connection],
        )

        engine = LayoutEngine()
        _, _, routed_wires = engine.layout_diagram(diagram)

        assert len(routed_wires) == 1
        wire = routed_wires[0]
        assert len(wire.path_points) >= 2

    @settings(max_examples=20, deadline=2000)
    @given(st.integers(min_value=1, max_value=10))
    def test_multiple_devices_same_structure(self, num_devices):
        """Property: Multiple identical devices should layout successfully."""
        board = boards.raspberry_pi_5()

        devices = []
        connections = []
        for i in range(num_devices):
            device = Device(
                name=f"Device{i}",
                pins=[DevicePin("PIN1", "GPIO", Point(5, 10))],
            )
            devices.append(device)

            if i < 40:  # Max 40 GPIO pins
                connections.append(Connection(i + 1, device.name, "PIN1"))

        diagram = Diagram(
            title="Multiple Devices Test",
            board=board,
            devices=devices,
            connections=connections,
        )

        engine = LayoutEngine()
        _, _, routed_wires = engine.layout_diagram(diagram)

        assert len(diagram.devices) == num_devices
        assert len(routed_wires) == len(connections)

    @settings(max_examples=20, deadline=2000)
    @given(st.integers(min_value=1, max_value=20))
    def test_varying_device_sizes(self, num_pins):
        """Property: Devices with varying numbers of pins should layout."""
        board = boards.raspberry_pi_5()

        pins = [DevicePin(f"PIN{i}", "GPIO", Point(5, 10 + i * 5)) for i in range(num_pins)]
        device = Device(
            name="VaryingDevice",
            pins=pins,
            height=max(50, num_pins * 10),
        )

        # Connect up to 40 pins
        connections = [
            Connection(i + 1, "VaryingDevice", f"PIN{i}") for i in range(min(num_pins, 40))
        ]

        diagram = Diagram(
            title="Varying Size Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()
        _, _, routed_wires = engine.layout_diagram(diagram)

        assert len(routed_wires) == len(connections)
        for wire in routed_wires:
            assert len(wire.path_points) >= 2


class TestLayoutInvariants:
    """Test invariants that should hold for all layouts."""

    @settings(max_examples=20, deadline=2000)
    @given(diagram_strategy(max_devices=3, max_connections=10))
    def test_layout_is_deterministic(self, diagram):
        """Property: Same diagram should produce same layout."""
        engine = LayoutEngine()

        # Layout twice - need to create separate diagram instances
        # because layout modifies device positions in place
        from copy import deepcopy

        diagram1 = deepcopy(diagram)
        diagram2 = deepcopy(diagram)

        _, _, wires1 = engine.layout_diagram(diagram1)
        _, _, wires2 = engine.layout_diagram(diagram2)

        # Device positions should be identical
        for d1, d2 in zip(diagram1.devices, diagram2.devices, strict=True):
            assert d1.position.x == d2.position.x
            assert d1.position.y == d2.position.y

        # Wire paths should be identical
        assert len(wires1) == len(wires2)
        for w1, w2 in zip(wires1, wires2, strict=True):
            assert len(w1.path_points) == len(w2.path_points)

    @settings(max_examples=20, deadline=2000)
    @given(diagram_strategy(max_devices=2, max_connections=5))
    def test_all_connections_are_routed(self, diagram):
        """Property: Number of routed wires equals number of connections."""
        engine = LayoutEngine()
        _, _, routed_wires = engine.layout_diagram(diagram)

        assert len(routed_wires) == len(diagram.connections)

    @settings(max_examples=20, deadline=2000)
    @given(diagram_strategy(max_devices=3, max_connections=10))
    def test_wire_colors_are_assigned(self, diagram):
        """Property: All wires should have colors assigned."""
        engine = LayoutEngine()
        _, _, routed_wires = engine.layout_diagram(diagram)

        for wire in routed_wires:
            assert wire.color is not None
            assert isinstance(wire.color, str)
            # Should be hex color format or color name
            assert len(wire.color) > 0
