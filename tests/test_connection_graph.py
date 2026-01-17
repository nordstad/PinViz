"""Tests for the ConnectionGraph utility class."""

import pytest

from pinviz.connection_graph import ConnectionGraph
from pinviz.model import Connection, Device, DevicePin, PinRole


@pytest.fixture
def simple_devices():
    """Create simple test devices."""
    return [
        Device(name="A", pins=[DevicePin(name="OUT", role=PinRole.GPIO)]),
        Device(name="B", pins=[DevicePin(name="IN", role=PinRole.GPIO)]),
        Device(name="C", pins=[DevicePin(name="IN", role=PinRole.GPIO)]),
    ]


def test_linear_chain_level_calculation():
    """Test level calculation for a linear chain: board->A->B->C."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="C",
            pins=[DevicePin(name="IN", role=PinRole.GPIO)],
        ),
    ]

    connections = [
        # Board -> A
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # A -> B
        Connection(source_device="A", source_pin="OUT", device_name="B", device_pin_name="IN"),
        # B -> C
        Connection(source_device="B", source_pin="OUT", device_name="C", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    levels = graph.calculate_device_levels()

    # Expected levels: A=0 (board connected), B=1, C=2
    assert levels["A"] == 0
    assert levels["B"] == 1
    assert levels["C"] == 2


def test_diamond_pattern_level_calculation():
    """Test level calculation for diamond pattern: board->A, board->B, A->C, B->C."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="C",
            pins=[
                DevicePin(name="IN1", role=PinRole.GPIO),
                DevicePin(name="IN2", role=PinRole.GPIO),
            ],
        ),
    ]

    connections = [
        # Board -> A
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # Board -> B
        Connection(board_pin=2, device_name="B", device_pin_name="IN"),
        # A -> C
        Connection(source_device="A", source_pin="OUT", device_name="C", device_pin_name="IN1"),
        # B -> C
        Connection(source_device="B", source_pin="OUT", device_name="C", device_pin_name="IN2"),
    ]

    graph = ConnectionGraph(devices, connections)
    levels = graph.calculate_device_levels()

    # Expected levels: A=0, B=0 (both board connected), C=1 (max(0,0)+1)
    assert levels["A"] == 0
    assert levels["B"] == 0
    assert levels["C"] == 1


def test_cycle_detection_simple_cycle():
    """Test cycle detection for A->B->C->A cycle."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="C",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
    ]

    connections = [
        # Board -> A (to make it reachable)
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # A -> B
        Connection(source_device="A", source_pin="OUT", device_name="B", device_pin_name="IN"),
        # B -> C
        Connection(source_device="B", source_pin="OUT", device_name="C", device_pin_name="IN"),
        # C -> A (creates cycle)
        Connection(source_device="C", source_pin="OUT", device_name="A", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    cycles = graph.detect_cycles()

    # Should detect the cycle A->B->C->A
    assert len(cycles) > 0
    # Check that all three devices are in at least one cycle
    cycle_nodes = set()
    for cycle in cycles:
        cycle_nodes.update(cycle)
    assert "A" in cycle_nodes
    assert "B" in cycle_nodes
    assert "C" in cycle_nodes


def test_self_loop_detection():
    """Test detection of self-loop (device connected to itself)."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
    ]

    connections = [
        # Board -> A
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # A -> A (self-loop)
        Connection(source_device="A", source_pin="OUT", device_name="A", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    cycles = graph.detect_cycles()

    # Should detect the self-loop
    assert len(cycles) > 0
    # The cycle should contain A appearing twice
    has_self_loop = any("A" in cycle and cycle.count("A") >= 2 for cycle in cycles)
    assert has_self_loop


def test_is_acyclic_true():
    """Test is_acyclic returns True for acyclic graph."""
    devices = [
        Device(name="A", pins=[DevicePin(name="IN", role=PinRole.GPIO)]),
        Device(name="B", pins=[DevicePin(name="IN", role=PinRole.GPIO)]),
    ]

    connections = [
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        Connection(board_pin=2, device_name="B", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    assert graph.is_acyclic() is True


def test_is_acyclic_false():
    """Test is_acyclic returns False for cyclic graph."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
    ]

    connections = [
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        Connection(source_device="A", source_pin="OUT", device_name="B", device_pin_name="IN"),
        Connection(source_device="B", source_pin="OUT", device_name="A", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    assert graph.is_acyclic() is False


def test_calculate_levels_with_cycle_raises_error():
    """Test that calculate_device_levels raises error for cyclic graph."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
    ]

    connections = [
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        Connection(source_device="A", source_pin="OUT", device_name="B", device_pin_name="IN"),
        Connection(source_device="B", source_pin="OUT", device_name="A", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    with pytest.raises(ValueError, match="Cannot calculate levels: graph contains cycles"):
        graph.calculate_device_levels()


def test_get_device_dependencies():
    """Test getting device dependencies (upstream devices)."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="C",
            pins=[
                DevicePin(name="IN1", role=PinRole.GPIO),
                DevicePin(name="IN2", role=PinRole.GPIO),
            ],
        ),
    ]

    connections = [
        # Board -> A
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # Board -> B
        Connection(board_pin=2, device_name="B", device_pin_name="IN"),
        # A -> C
        Connection(source_device="A", source_pin="OUT", device_name="C", device_pin_name="IN1"),
        # B -> C
        Connection(source_device="B", source_pin="OUT", device_name="C", device_pin_name="IN2"),
    ]

    graph = ConnectionGraph(devices, connections)

    # A depends on board
    assert graph.get_device_dependencies("A") == ["board"]

    # B depends on board
    assert graph.get_device_dependencies("B") == ["board"]

    # C depends on A and B
    deps_c = graph.get_device_dependencies("C")
    assert set(deps_c) == {"A", "B"}


def test_get_device_dependents():
    """Test getting device dependents (downstream devices)."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[DevicePin(name="IN", role=PinRole.GPIO)],
        ),
        Device(
            name="C",
            pins=[DevicePin(name="IN", role=PinRole.GPIO)],
        ),
    ]

    connections = [
        # Board -> A
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # A -> B
        Connection(source_device="A", source_pin="OUT", device_name="B", device_pin_name="IN"),
        # A -> C
        Connection(source_device="A", source_pin="OUT", device_name="C", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)

    # A connects to B and C
    dependents_a = graph.get_device_dependents("A")
    assert set(dependents_a) == {"B", "C"}

    # B has no dependents
    assert graph.get_device_dependents("B") == []

    # C has no dependents
    assert graph.get_device_dependents("C") == []


def test_get_root_devices():
    """Test getting root devices (board-connected)."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="C",
            pins=[DevicePin(name="IN", role=PinRole.GPIO)],
        ),
    ]

    connections = [
        # Board -> A
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # Board -> B
        Connection(board_pin=2, device_name="B", device_pin_name="IN"),
        # A -> C
        Connection(source_device="A", source_pin="OUT", device_name="C", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    root_devices = graph.get_root_devices()

    # A and B are root devices (board-connected)
    assert set(root_devices) == {"A", "B"}


def test_get_leaf_devices():
    """Test getting leaf devices (no outgoing connections)."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[DevicePin(name="IN", role=PinRole.GPIO)],
        ),
        Device(
            name="C",
            pins=[DevicePin(name="IN", role=PinRole.GPIO)],
        ),
    ]

    connections = [
        # Board -> A
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # A -> B
        Connection(source_device="A", source_pin="OUT", device_name="B", device_pin_name="IN"),
        # Board -> C
        Connection(board_pin=2, device_name="C", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    leaf_devices = graph.get_leaf_devices()

    # B and C are leaf devices (no outgoing connections)
    assert set(leaf_devices) == {"B", "C"}


def test_empty_graph():
    """Test empty graph (no devices or connections)."""
    devices = []
    connections = []

    graph = ConnectionGraph(devices, connections)

    # Empty graph should be acyclic
    assert graph.is_acyclic() is True

    # No cycles detected
    assert graph.detect_cycles() == []

    # No levels to calculate
    levels = graph.calculate_device_levels()
    assert levels == {}

    # No root or leaf devices
    assert graph.get_root_devices() == []
    assert graph.get_leaf_devices() == []


def test_devices_with_no_connections():
    """Test devices that have no connections at all."""
    devices = [
        Device(name="A", pins=[DevicePin(name="IN", role=PinRole.GPIO)]),
        Device(name="B", pins=[DevicePin(name="IN", role=PinRole.GPIO)]),
    ]

    # No connections
    connections = []

    graph = ConnectionGraph(devices, connections)

    # Should be acyclic
    assert graph.is_acyclic() is True

    # Calculate levels (devices with no connections won't appear in levels)
    levels = graph.calculate_device_levels()
    assert levels == {}

    # All devices are leaf devices (no outgoing connections)
    leaf_devices = graph.get_leaf_devices()
    assert set(leaf_devices) == {"A", "B"}


def test_build_adjacency_list():
    """Test adjacency list building."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO),
                DevicePin(name="OUT", role=PinRole.GPIO),
            ],
        ),
        Device(
            name="B",
            pins=[DevicePin(name="IN", role=PinRole.GPIO)],
        ),
    ]

    connections = [
        # Board -> A
        Connection(board_pin=1, device_name="A", device_pin_name="IN"),
        # A -> B
        Connection(source_device="A", source_pin="OUT", device_name="B", device_pin_name="IN"),
    ]

    graph = ConnectionGraph(devices, connections)
    adj_list = graph.build_adjacency_list()

    # Check adjacency list structure
    assert "board" in adj_list
    assert "A" in adj_list["board"]
    assert "A" in adj_list
    assert "B" in adj_list["A"]


def test_duplicate_connections_handled():
    """Test that duplicate connections don't create duplicate edges."""
    devices = [
        Device(
            name="A",
            pins=[
                DevicePin(name="IN1", role=PinRole.GPIO),
                DevicePin(name="IN2", role=PinRole.GPIO),
            ],
        ),
    ]

    connections = [
        # Two connections from board to same device (different pins)
        Connection(board_pin=1, device_name="A", device_pin_name="IN1"),
        Connection(board_pin=2, device_name="A", device_pin_name="IN2"),
    ]

    graph = ConnectionGraph(devices, connections)
    adj_list = graph.build_adjacency_list()

    # Device A should appear only once in board's adjacency list
    assert adj_list["board"].count("A") == 1
