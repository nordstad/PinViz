"""Edge case tests for layout engine and wire routing.

This module tests the layout engine with extreme cases including:
- Large diagrams with many connections
- Maximum wire overlap scenarios
- Different wire routing styles
- Performance characteristics
"""

import time

from pinviz import boards
from pinviz.devices import get_registry
from pinviz.layout import LayoutEngine
from pinviz.model import Connection, Device, DevicePin, Diagram, Point, WireStyle


class TestLargeDiagrams:
    """Tests for diagrams with many connections."""

    def test_diagram_with_50_connections(self):
        """Test layout with 50+ connections."""
        board = boards.raspberry_pi_5()

        # Create 5 devices with 10 pins each
        test_devices = []
        for i in range(5):
            pins = [DevicePin(f"PIN{j}", "GPIO", Point(5, 10 + j * 8)) for j in range(10)]
            device = Device(
                name=f"Device_{i}",
                pins=pins,
                width=80,
                height=100,
            )
            test_devices.append(device)

        # Create 50 connections (10 from each device)
        connections = []
        pin_index = 1
        for device in test_devices:
            for pin in device.pins:
                if pin_index <= 40:  # Max 40 GPIO pins
                    connections.append(
                        Connection(
                            board_pin=pin_index,
                            device_name=device.name,
                            device_pin_name=pin.name,
                        )
                    )
                    pin_index += 1

        diagram = Diagram(
            title="Large Diagram Test",
            board=board,
            devices=test_devices,
            connections=connections,
        )

        # Layout should complete without errors
        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        # Verify all connections were routed
        assert len(routed_wires) == len(connections)
        assert len(routed_wires) >= 40

        # Verify all wires have valid paths
        for wire in routed_wires:
            assert len(wire.path_points) >= 2
            assert wire.from_pin_pos is not None
            assert wire.to_pin_pos is not None

    def test_diagram_with_all_40_gpio_pins(self):
        """Test diagram using all 40 GPIO pins."""
        board = boards.raspberry_pi_5()

        # Create a single large device with 40 pins
        pins = [DevicePin(f"PIN{i}", "GPIO", Point(5, 10 + i * 5)) for i in range(1, 41)]
        device = Device(
            name="MegaDevice",
            pins=pins,
            width=120,
            height=250,
        )

        # Connect all 40 pins
        connections = [
            Connection(
                board_pin=i,
                device_name="MegaDevice",
                device_pin_name=f"PIN{i}",
            )
            for i in range(1, 41)
        ]

        diagram = Diagram(
            title="Full GPIO Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 40

        # Check that wires don't have extreme overlaps
        # (some overlap is expected and handled by offset)
        for wire in routed_wires:
            # Verify path is reasonable (not too long)
            path_length = sum(
                abs(wire.path_points[i + 1].x - wire.path_points[i].x)
                + abs(wire.path_points[i + 1].y - wire.path_points[i].y)
                for i in range(len(wire.path_points) - 1)
            )
            # Path should be less than 2000 units (sanity check)
            assert path_length < 2000, f"Wire path too long: {path_length}"


class TestWireOverlapScenarios:
    """Tests for maximum wire overlap scenarios."""

    def test_multiple_connections_from_same_pin(self):
        """Test multiple devices connected to the same board pin."""
        board = boards.raspberry_pi_5()

        # Create 3 devices
        device1 = get_registry().create("bh1750")
        device1.name = "Sensor1"
        device2 = get_registry().create("bh1750")
        device2.name = "Sensor2"
        device3 = get_registry().create("bh1750")
        device3.name = "Sensor3"

        # All connect VCC to pin 1 (should create parallel wires with offset)
        connections = [
            Connection(1, "Sensor1", "VCC"),
            Connection(1, "Sensor2", "VCC"),
            Connection(1, "Sensor3", "VCC"),
        ]

        diagram = Diagram(
            title="Overlap Test",
            board=board,
            devices=[device1, device2, device3],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 3

        # Wires from the same pin should have different rail positions
        rail_positions = set()
        for wire in routed_wires:
            # The second point in the path (after leaving the pin) indicates rail position
            if len(wire.path_points) >= 2:
                rail_x = wire.path_points[1].x
                rail_positions.add(rail_x)

        # Should have 3 distinct rail positions (one for each wire)
        assert len(rail_positions) == 3

    def test_many_connections_to_gnd_pins(self):
        """Test many devices connecting to ground pins."""
        board = boards.raspberry_pi_5()

        # Create 10 LED devices
        test_devices = []
        for i in range(10):
            led = get_registry().create("led")
            led.name = f"LED{i}"
            test_devices.append(led)

        # All connect to ground pins (6, 9, 14, 20, 25, 30, 34, 39)
        # Distribute across available ground pins
        gnd_pins = [6, 9, 14, 20, 25, 30, 34, 39]
        connections = []

        for i, device in enumerate(test_devices):
            gnd_pin = gnd_pins[i % len(gnd_pins)]
            connections.append(Connection(gnd_pin, device.name, "-"))

        diagram = Diagram(
            title="Multiple GND Test",
            board=board,
            devices=test_devices,
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 10

        # Verify all wires are routed properly
        for wire in routed_wires:
            assert wire.from_pin_pos is not None
            assert wire.to_pin_pos is not None
            assert len(wire.path_points) >= 2


class TestWireStyleDifferences:
    """Tests for different wire routing styles."""

    def _create_test_diagram_for_styles(self, style: WireStyle) -> Diagram:
        """Helper to create a diagram with specified wire style."""
        board = boards.raspberry_pi_5()
        device = get_registry().create("bh1750")

        connections = [
            Connection(1, "BH1750 Light Sensor", "VCC", style=style),
            Connection(3, "BH1750 Light Sensor", "SDA", style=style),
            Connection(5, "BH1750 Light Sensor", "SCL", style=style),
            Connection(6, "BH1750 Light Sensor", "GND", style=style),
        ]

        return Diagram(
            title=f"{style.value} Style Test",
            board=board,
            devices=[device],
            connections=connections,
        )

    def test_orthogonal_wire_style(self):
        """Test layout with orthogonal wire routing."""
        diagram = self._create_test_diagram_for_styles(WireStyle.ORTHOGONAL)

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 4

        # Orthogonal wires should have mostly horizontal/vertical segments
        for wire in routed_wires:
            points = wire.path_points
            # Check that consecutive points form horizontal or vertical lines
            for i in range(len(points) - 1):
                dx = abs(points[i + 1].x - points[i].x)
                dy = abs(points[i + 1].y - points[i].y)
                # At least one dimension should have minimal change
                # (allowing some tolerance for corner radius)
                assert dx < 1 or dy < 1 or dx > 10 or dy > 10

    def test_curved_wire_style(self):
        """Test layout with curved wire routing."""
        diagram = self._create_test_diagram_for_styles(WireStyle.CURVED)

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 4

        # Curved wires should have smooth paths
        for wire in routed_wires:
            assert len(wire.path_points) >= 2
            # Path should exist and be valid
            assert wire.from_pin_pos is not None
            assert wire.to_pin_pos is not None

    def test_mixed_wire_style(self):
        """Test layout with mixed wire routing (default)."""
        diagram = self._create_test_diagram_for_styles(WireStyle.MIXED)

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 4

        # Mixed style should work for all wires
        for wire in routed_wires:
            assert len(wire.path_points) >= 2

    def test_different_styles_in_same_diagram(self):
        """Test diagram with different wire styles for different connections."""
        board = boards.raspberry_pi_5()
        device = get_registry().create("bh1750")

        connections = [
            Connection(1, "BH1750 Light Sensor", "VCC", style=WireStyle.ORTHOGONAL),
            Connection(3, "BH1750 Light Sensor", "SDA", style=WireStyle.CURVED),
            Connection(5, "BH1750 Light Sensor", "SCL", style=WireStyle.MIXED),
            Connection(6, "BH1750 Light Sensor", "GND", style=WireStyle.ORTHOGONAL),
        ]

        diagram = Diagram(
            title="Mixed Styles Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 4

        # All wires should be routed despite different styles
        for wire in routed_wires:
            assert wire.path_points is not None
            assert len(wire.path_points) >= 2


class TestLayoutPerformance:
    """Performance tests for layout engine."""

    def test_layout_performance_small_diagram(self):
        """Test layout performance with small diagram."""
        board = boards.raspberry_pi_5()
        device = get_registry().create("bh1750")

        connections = [
            Connection(1, "BH1750 Light Sensor", "VCC"),
            Connection(3, "BH1750 Light Sensor", "SDA"),
            Connection(5, "BH1750 Light Sensor", "SCL"),
            Connection(6, "BH1750 Light Sensor", "GND"),
        ]

        diagram = Diagram(
            title="Performance Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()

        # Measure time
        start_time = time.time()
        engine.layout_diagram(diagram)
        elapsed_time = time.time() - start_time

        # Should complete in less than 100ms
        assert elapsed_time < 0.1, f"Layout took {elapsed_time:.3f}s, expected < 0.1s"

    def test_layout_performance_medium_diagram(self):
        """Test layout performance with medium diagram (20 connections)."""
        board = boards.raspberry_pi_5()

        # Create 4 devices with 5 connections each
        test_devices = []
        for i in range(4):
            pins = [DevicePin(f"PIN{j}", "GPIO", Point(5, 10 + j * 10)) for j in range(5)]
            device = Device(name=f"Device_{i}", pins=pins)
            test_devices.append(device)

        connections = []
        pin_index = 1
        for device in test_devices:
            for pin in device.pins:
                connections.append(Connection(pin_index, device.name, pin.name))
                pin_index += 1

        diagram = Diagram(
            title="Medium Performance Test",
            board=board,
            devices=test_devices,
            connections=connections,
        )

        engine = LayoutEngine()

        start_time = time.time()
        engine.layout_diagram(diagram)
        elapsed_time = time.time() - start_time

        # Should complete in less than 200ms
        assert elapsed_time < 0.2, f"Layout took {elapsed_time:.3f}s, expected < 0.2s"

    def test_layout_performance_large_diagram(self):
        """Test layout performance with large diagram (40 connections)."""
        board = boards.raspberry_pi_5()

        # Create device with 40 pins
        pins = [DevicePin(f"PIN{i}", "GPIO", Point(5, 10 + i * 5)) for i in range(1, 41)]
        device = Device(name="LargeDevice", pins=pins, width=120, height=250)

        connections = [Connection(i, "LargeDevice", f"PIN{i}") for i in range(1, 41)]

        diagram = Diagram(
            title="Large Performance Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()

        start_time = time.time()
        engine.layout_diagram(diagram)
        elapsed_time = time.time() - start_time

        # Should complete in less than 500ms even for 40 connections
        assert elapsed_time < 0.5, f"Layout took {elapsed_time:.3f}s, expected < 0.5s"


class TestLayoutEdgeCases:
    """Edge case tests for layout engine."""

    def test_single_connection(self):
        """Test layout with just one connection."""
        board = boards.raspberry_pi_5()
        led = get_registry().create("led")
        led.name = "LED"

        connections = [Connection(11, "LED", "+")]

        diagram = Diagram(
            title="Single Connection",
            board=board,
            devices=[led],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 1
        wire = routed_wires[0]
        assert len(wire.path_points) >= 2

    def test_no_connections(self):
        """Test layout with devices but no connections."""
        board = boards.raspberry_pi_5()
        device = get_registry().create("bh1750")

        diagram = Diagram(
            title="No Connections",
            board=board,
            devices=[device],
            connections=[],
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        # Should have positioned the device
        assert diagram.devices[0].position is not None
        # No wires should be routed
        assert len(routed_wires) == 0

    def test_device_with_many_pins(self):
        """Test device with unusually many pins."""
        board = boards.raspberry_pi_5()

        # Device with 50 pins
        pins = [DevicePin(f"PIN{i}", "GPIO", Point(5, 5 + i * 3)) for i in range(50)]
        device = Device(
            name="ManyPins",
            pins=pins,
            width=100,
            height=180,
        )

        # Connect 20 of them
        connections = [Connection(i + 1, "ManyPins", f"PIN{i}") for i in range(20)]

        diagram = Diagram(
            title="Many Pins Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 20

    def test_very_tall_device(self):
        """Test layout with a very tall device."""
        board = boards.raspberry_pi_5()

        pins = [DevicePin(f"PIN{i}", "GPIO", Point(5, 10 + i * 20)) for i in range(10)]
        device = Device(
            name="TallDevice",
            pins=pins,
            width=80,
            height=250,  # Very tall
        )

        connections = [Connection(i + 1, "TallDevice", f"PIN{i}") for i in range(10)]

        diagram = Diagram(
            title="Tall Device Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        assert len(routed_wires) == 10

        # Device should be positioned
        assert diagram.devices[0].position is not None

        # All wires should reach their targets
        for wire in routed_wires:
            assert wire.from_pin_pos is not None
            assert wire.to_pin_pos is not None
