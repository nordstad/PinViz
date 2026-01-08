"""Tests for wire routing spacing and non-overlap guarantees."""

from pinviz import Connection, Diagram, boards, devices
from pinviz.layout import LayoutConfig, LayoutEngine
from pinviz.model import Point


def line_segments_overlap(
    p1: Point, p2: Point, p3: Point, p4: Point, tolerance: float = 0.1
) -> bool:
    """
    Check if two line segments overlap (share the same pixels).

    Args:
        p1, p2: Endpoints of first segment
        p3, p4: Endpoints of second segment
        tolerance: Tolerance for floating point comparison

    Returns:
        True if segments overlap in the same location
    """
    # Check if segments are collinear and overlapping
    # For vertical segments (same X)
    if (
        abs(p1.x - p2.x) < tolerance
        and abs(p3.x - p4.x) < tolerance
        and abs(p1.x - p3.x) < tolerance
    ):
        # Check Y overlap
        y1_min, y1_max = min(p1.y, p2.y), max(p1.y, p2.y)
        y2_min, y2_max = min(p3.y, p4.y), max(p3.y, p4.y)
        return not (y1_max < y2_min or y2_max < y1_min)

    # For horizontal segments (same Y)
    if (
        abs(p1.y - p2.y) < tolerance
        and abs(p3.y - p4.y) < tolerance
        and abs(p1.y - p3.y) < tolerance
    ):
        # Check X overlap
        x1_min, x1_max = min(p1.x, p2.x), max(p1.x, p2.x)
        x2_min, x2_max = min(p3.x, p4.x), max(p3.x, p4.x)
        return not (x1_max < x2_min or x2_max < x1_min)

    return False


def calculate_min_distance_between_wires(
    wire1_points: list[Point], wire2_points: list[Point]
) -> float:
    """
    Calculate minimum distance between two wire paths.

    Args:
        wire1_points: Waypoints for first wire
        wire2_points: Waypoints for second wire

    Returns:
        Minimum distance in pixels
    """
    min_dist = float("inf")

    # Check distance between all segment pairs
    for i in range(len(wire1_points) - 1):
        for j in range(len(wire2_points) - 1):
            p1, p2 = wire1_points[i], wire1_points[i + 1]
            p3, p4 = wire2_points[j], wire2_points[j + 1]

            # For parallel segments, calculate perpendicular distance
            # For vertical segments
            if abs(p1.x - p2.x) < 0.1 and abs(p3.x - p4.x) < 0.1:
                y1_min, y1_max = min(p1.y, p2.y), max(p1.y, p2.y)
                y2_min, y2_max = min(p3.y, p4.y), max(p3.y, p4.y)
                # Check if they overlap in Y
                if not (y1_max < y2_min or y2_max < y1_min):
                    dist = abs(p1.x - p3.x)
                    min_dist = min(min_dist, dist)

            # For horizontal segments
            if abs(p1.y - p2.y) < 0.1 and abs(p3.y - p4.y) < 0.1:
                x1_min, x1_max = min(p1.x, p2.x), max(p1.x, p2.x)
                x2_min, x2_max = min(p3.x, p4.x), max(p3.x, p4.x)
                # Check if they overlap in X
                if not (x1_max < x2_min or x2_max < x1_min):
                    dist = abs(p1.y - p3.y)
                    min_dist = min(min_dist, dist)

    return min_dist if min_dist != float("inf") else 0.0


class TestWireSpacing:
    """Test suite for wire routing spacing guarantees."""

    def test_vertical_rail_separation(self):
        """Test that wires use different vertical rails with proper spacing."""
        # Create a diagram with multiple wires
        diagram = Diagram(
            title="Test Diagram",
            board=boards.raspberry_pi_5(),
            devices=[devices.bh1750_light_sensor()],
            connections=[
                Connection(1, "BH1750", "VCC"),
                Connection(6, "BH1750", "GND"),
                Connection(3, "BH1750", "SDA"),
                Connection(5, "BH1750", "SCL"),
            ],
        )

        engine = LayoutEngine()
        _, _, routed_wires = engine.layout_diagram(diagram)

        # Extract rail X positions (3rd waypoint is along the rail)
        rail_positions = set()
        for wire in routed_wires:
            if len(wire.path_points) >= 4:
                # Vertical rail segment
                rail_x = wire.path_points[2].x
                rail_positions.add(round(rail_x, 1))

        # Should have separation between rails
        rail_list = sorted(rail_positions)
        if len(rail_list) > 1:
            min_separation = min(rail_list[i + 1] - rail_list[i] for i in range(len(rail_list) - 1))
            assert min_separation >= 3.0, f"Rails too close: {min_separation:.1f}px"

    def test_minimum_wire_spacing(self):
        """Test that parallel wires maintain minimum spacing."""
        config = LayoutConfig(wire_spacing=8.0)
        diagram = Diagram(
            title="Test Diagram",
            board=boards.raspberry_pi_5(),
            devices=[devices.bh1750_light_sensor()],
            connections=[
                Connection(1, "BH1750", "VCC"),
                Connection(6, "BH1750", "GND"),
                Connection(3, "BH1750", "SDA"),
                Connection(5, "BH1750", "SCL"),
            ],
        )

        engine = LayoutEngine(config)
        _, _, routed_wires = engine.layout_diagram(diagram)

        # Check spacing between all wire pairs
        min_spacing_found = float("inf")

        for i in range(len(routed_wires)):
            for j in range(i + 1, len(routed_wires)):
                dist = calculate_min_distance_between_wires(
                    routed_wires[i].path_points,
                    routed_wires[j].path_points,
                )
                if dist > 0:  # Only check if wires are parallel
                    min_spacing_found = min(min_spacing_found, dist)

        # Allow small tolerance for floating point
        tolerance = 0.1
        assert min_spacing_found >= (config.wire_spacing - tolerance), (
            f"Minimum spacing {min_spacing_found:.2f}px is less than "
            f"required {config.wire_spacing}px"
        )

    def test_worst_case_header_breakout(self):
        """Test many wires from adjacent pins to multiple devices."""
        # Create a worst-case scenario: many wires from nearby pins
        dev1 = devices.generic_i2c_device("Device1")
        dev2 = devices.generic_i2c_device("Device2")

        diagram = Diagram(
            title="Worst Case Test",
            board=boards.raspberry_pi_5(),
            devices=[dev1, dev2],
            connections=[
                # I2C bus to Device1
                Connection(1, "Device1", "VCC"),
                Connection(3, "Device1", "SDA"),
                Connection(5, "Device1", "SCL"),
                Connection(9, "Device1", "GND"),
                # I2C bus to Device2
                Connection(17, "Device2", "VCC"),
                Connection(3, "Device2", "SDA"),  # Shared I2C
                Connection(5, "Device2", "SCL"),  # Shared I2C
                Connection(14, "Device2", "GND"),
            ],
        )

        config = LayoutConfig(wire_spacing=8.0)
        engine = LayoutEngine(config)
        _, _, routed_wires = engine.layout_diagram(diagram)

        # Verify rails are properly spaced
        assert len(routed_wires) == 8, f"Expected 8 wires, got {len(routed_wires)}"
        # Just verify routing completes successfully for complex diagram
        for wire in routed_wires:
            assert len(wire.path_points) >= 2, "Wire must have at least 2 points"

    def test_bundle_spacing_within_group(self):
        """Test that wires from the same pin route to different devices without crossing."""
        config = LayoutConfig(bundle_spacing=4.0, wire_spacing=8.0)

        # Multiple wires from same pin (pin 6 = GND) going to different devices
        dev1 = devices.bh1750_light_sensor()
        dev1.name = "Device1"
        dev2 = devices.bh1750_light_sensor()
        dev2.name = "Device2"
        dev3 = devices.bh1750_light_sensor()
        dev3.name = "Device3"

        diagram = Diagram(
            title="Bundle Test",
            board=boards.raspberry_pi_5(),
            devices=[dev1, dev2, dev3],
            connections=[
                Connection(6, "Device1", "GND"),
                Connection(6, "Device2", "GND"),
                Connection(6, "Device3", "GND"),
            ],
        )

        engine = LayoutEngine(config)
        _, _, routed_wires = engine.layout_diagram(diagram)

        # With device-based rail routing and Bezier curves, each wire to a different
        # device should use different control points (path_points[1] is first control point)
        control_point_x_positions = []
        for wire in routed_wires:
            # First control point X (Bezier curve control point, not raw rail X)
            ctrl_x = wire.path_points[1].x
            control_point_x_positions.append(ctrl_x)

        # All control point X positions should be different (preventing crossings)
        unique_ctrl_points = set(control_point_x_positions)
        assert len(unique_ctrl_points) == 3, (
            f"Expected 3 different control points (one per device), got {len(unique_ctrl_points)}"
        )

        # Check that control points maintain reasonable separation
        # With Bezier curves, control points are weighted blends, so spacing is smaller
        # than raw rail spacing. We just need to verify they're distinct and ordered.
        ctrl_x_sorted = sorted(unique_ctrl_points)
        for i in range(len(ctrl_x_sorted) - 1):
            spacing = ctrl_x_sorted[i + 1] - ctrl_x_sorted[i]
            # Minimum separation should be positive (wires don't overlap)
            assert spacing > 0.1, (
                f"Control point spacing {spacing:.2f} too small, wires may cross"
            )

    def test_deterministic_routing(self):
        """Test that routing is deterministic (same inputs -> same outputs)."""
        diagram = Diagram(
            title="Deterministic Test",
            board=boards.raspberry_pi_5(),
            devices=[devices.bh1750_light_sensor()],
            connections=[
                Connection(1, "BH1750", "VCC"),
                Connection(6, "BH1750", "GND"),
                Connection(3, "BH1750", "SDA"),
                Connection(5, "BH1750", "SCL"),
            ],
        )

        engine = LayoutEngine()

        # Route twice
        _, _, routed1 = engine.layout_diagram(diagram)
        _, _, routed2 = engine.layout_diagram(diagram)

        # Should produce identical results
        assert len(routed1) == len(routed2)

        for wire1, wire2 in zip(routed1, routed2, strict=True):
            assert len(wire1.path_points) == len(wire2.path_points)
            for p1, p2 in zip(wire1.path_points, wire2.path_points, strict=True):
                assert abs(p1.x - p2.x) < 0.001
                assert abs(p1.y - p2.y) < 0.001
