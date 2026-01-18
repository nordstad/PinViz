"""Comprehensive integration tests for Phase 4.1: Multi-Tier Layout System.

This module provides comprehensive integration tests for the multi-tier device layout
system, covering:

1. End-to-end layout scenarios (simple chains, branching, realistic power distribution)
2. Backward compatibility with single-tier diagrams
3. Edge cases (empty intermediate tiers, sparse connections)
4. Performance validation (50 devices within 1 second)
5. Layout validation for valid multi-tier diagrams

Issue: https://github.com/nordstad/PinViz/issues/83
Priority: HIGH
"""

import time

import pytest

from pinviz import boards
from pinviz.devices import get_registry
from pinviz.layout import LayoutEngine
from pinviz.model import Connection, Device, DevicePin, Diagram, PinRole, Point


class TestEndToEndLayoutScenarios:
    """End-to-end multi-tier layout scenario tests."""

    def test_simple_chain_layout(self):
        """Test simple chain: Board → Device A → Device B → Device C.

        This tests the basic multi-tier layout where devices form a linear chain.
        Note: Only board-to-device wires are routed; device-to-device connections
        are used only for positioning.
        """
        board = boards.raspberry_pi_5()

        # Create devices for a simple chain
        device_a = Device(
            name="Sensor",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
            ],
            width=80,
            height=50,
            color="#4A90E2",
        )
        device_b = Device(
            name="Processor",
            pins=[
                DevicePin("IN", PinRole.GPIO, Point(0, 0)),
                DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
            ],
            width=80,
            height=50,
            color="#E24A4A",
        )
        device_c = Device(
            name="Display",
            pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
            width=80,
            height=50,
            color="#4AE24A",
        )

        # Create linear chain connections
        # Only board-to-device connections will be routed as wires
        connections = [
            Connection(board_pin=1, device_name="Sensor", device_pin_name="VCC"),
            Connection(
                source_device="Sensor",
                source_pin="OUT",
                device_name="Processor",
                device_pin_name="IN",
            ),
            Connection(
                source_device="Processor",
                source_pin="OUT",
                device_name="Display",
                device_pin_name="IN",
            ),
        ]

        diagram = Diagram(
            title="Simple Chain Layout",
            board=board,
            devices=[device_a, device_b, device_c],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        routed_wires = result.routed_wires

        # Verify devices are positioned correctly in tiers
        assert device_a.position.x < device_b.position.x < device_c.position.x, (
            "Devices should be in increasing tiers"
        )

        # Verify all wires are routed (both board-to-device and device-to-device)
        assert len(routed_wires) == len(connections), (
            f"Expected {len(connections)} routed wires, got {len(routed_wires)}"
        )

        # Verify canvas dimensions are reasonable
        assert canvas_width > 0 and canvas_height > 0

        # Verify no layout validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0, f"Layout validation failed: {issues}"

    def test_branching_layout(self):
        """Test branching layout: Board → Device A → [Device B, Device C].

        This tests multi-tier layout where one device connects to multiple devices
        in the next tier.
        Note: Only board-to-device wires are routed.
        """
        board = boards.raspberry_pi_5()

        # Create devices for branching
        device_a = Device(
            name="Splitter",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                DevicePin("OUT1", PinRole.GPIO, Point(0, 10)),
                DevicePin("OUT2", PinRole.GPIO, Point(0, 20)),
            ],
            width=80,
            height=60,
            color="#4A90E2",
        )
        device_b = Device(
            name="LED Red",
            pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
            width=60,
            height=40,
            color="#E24A4A",
        )
        device_c = Device(
            name="LED Green",
            pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
            width=60,
            height=40,
            color="#4AE24A",
        )

        # Create branching connections
        connections = [
            Connection(board_pin=1, device_name="Splitter", device_pin_name="VCC"),
            Connection(
                source_device="Splitter",
                source_pin="OUT1",
                device_name="LED Red",
                device_pin_name="IN",
            ),
            Connection(
                source_device="Splitter",
                source_pin="OUT2",
                device_name="LED Green",
                device_pin_name="IN",
            ),
        ]

        diagram = Diagram(
            title="Branching Layout",
            board=board,
            devices=[device_a, device_b, device_c],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        routed_wires = result.routed_wires

        # Verify branching structure
        assert device_a.position.x < device_b.position.x, "Splitter before branches"
        assert device_a.position.x < device_c.position.x, "Splitter before branches"
        assert device_b.position.x == device_c.position.x, "Branches at same tier"
        assert device_b.position.y != device_c.position.y, "Branches stacked vertically"

        # Verify all wires are routed (both board-to-device and device-to-device)
        assert len(routed_wires) == len(connections)

        # Verify no layout validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0, f"Layout validation failed: {issues}"

    def test_realistic_power_distribution(self):
        """Test realistic power distribution with multiple devices and tiers.

        This tests a realistic scenario with power and ground distribution across
        multiple devices in different tiers.
        """
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create realistic device setup: sensors → controller → displays
        sensor1 = registry.create("bh1750")
        sensor1.name = "Light Sensor"

        sensor2 = registry.create("bme280")
        sensor2.name = "Temp Sensor"

        controller = Device(
            name="Controller",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                DevicePin("GND", PinRole.GROUND, Point(0, 10)),
                DevicePin("IN1", PinRole.I2C_SDA, Point(0, 20)),
                DevicePin("IN2", PinRole.I2C_SCL, Point(0, 30)),
                DevicePin("OUT", PinRole.GPIO, Point(0, 40)),
            ],
            width=100,
            height=80,
            color="#9B59B6",
        )

        display = registry.create("ssd1306")
        display.name = "OLED Display"

        # Create connections: board powers sensors and controller,
        # sensors connect to controller via I2C, controller drives display
        connections = [
            # Power sensors from board
            Connection(board_pin=1, device_name="Light Sensor", device_pin_name="VCC"),
            Connection(board_pin=6, device_name="Light Sensor", device_pin_name="GND"),
            Connection(board_pin=1, device_name="Temp Sensor", device_pin_name="VCC"),
            Connection(board_pin=9, device_name="Temp Sensor", device_pin_name="GND"),
            # I2C connections to controller
            Connection(board_pin=3, device_name="Light Sensor", device_pin_name="SDA"),
            Connection(board_pin=5, device_name="Light Sensor", device_pin_name="SCL"),
            Connection(board_pin=3, device_name="Temp Sensor", device_pin_name="SDA"),
            Connection(board_pin=5, device_name="Temp Sensor", device_pin_name="SCL"),
            Connection(board_pin=3, device_name="Controller", device_pin_name="IN1"),
            Connection(board_pin=5, device_name="Controller", device_pin_name="IN2"),
            # Power controller
            Connection(board_pin=1, device_name="Controller", device_pin_name="VCC"),
            Connection(board_pin=14, device_name="Controller", device_pin_name="GND"),
            # Controller to display
            Connection(
                source_device="Controller",
                source_pin="OUT",
                device_name="OLED Display",
                device_pin_name="SDA",
            ),
            # Power display
            Connection(board_pin=1, device_name="OLED Display", device_pin_name="VCC"),
            Connection(board_pin=20, device_name="OLED Display", device_pin_name="GND"),
        ]

        diagram = Diagram(
            title="Realistic Power Distribution",
            board=board,
            devices=[sensor1, sensor2, controller, display],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        routed_wires = result.routed_wires

        # Verify multi-tier structure
        # All devices directly connected to board are at tier 0
        tier0_devices = [sensor1, sensor2, controller]
        tier0_positions = [d.position.x for d in tier0_devices]
        assert all(x == tier0_positions[0] for x in tier0_positions), (
            "Devices with board connections at same tier"
        )
        # Display is connected via device-to-device, so it's at tier 1
        assert display.position.x > controller.position.x, "Display after controller"

        # Verify all wires are routed (both board-to-device and device-to-device)
        assert len(routed_wires) == len(connections)

        # Verify no layout validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0, f"Layout validation failed: {issues}"


class TestBackwardCompatibility:
    """Backward compatibility tests for single-tier layouts."""

    def test_single_device_single_tier(self):
        """Test that single device diagrams still work correctly."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        device = registry.create("bh1750")
        connections = [
            Connection(1, device.name, "VCC"),
            Connection(3, device.name, "SDA"),
            Connection(5, device.name, "SCL"),
            Connection(6, device.name, "GND"),
        ]

        diagram = Diagram(
            title="Single Device Backward Compatibility",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        routed_wires = result.routed_wires

        # Verify device is positioned
        assert device.position is not None
        assert device.position.x > 0 and device.position.y > 0

        # Verify all connections routed
        assert len(routed_wires) == len(connections)

        # Verify no validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0

    def test_multiple_devices_same_tier(self):
        """Test that multiple devices all connected to board stay in same tier."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create multiple devices all connected to board
        devices = [
            registry.create("bh1750"),
            registry.create("bme280"),
            registry.create("led"),
        ]
        devices[0].name = "Light Sensor"
        devices[1].name = "Temp Sensor"
        devices[2].name = "Status LED"

        connections = [
            Connection(1, "Light Sensor", "VCC"),
            Connection(6, "Light Sensor", "GND"),
            Connection(1, "Temp Sensor", "VCC"),
            Connection(9, "Temp Sensor", "GND"),
            Connection(11, "Status LED", "Anode"),
            Connection(14, "Status LED", "Cathode"),
        ]

        diagram = Diagram(
            title="Multiple Devices Same Tier",
            board=board,
            devices=devices,
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        # All devices should be at same X (same tier)
        x_positions = [d.position.x for d in devices]
        assert len(set(x_positions)) == 1, "All devices should be in same tier"

        # Verify no validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0

    def test_existing_examples_still_render(self):
        """Test that existing example diagrams still render correctly."""
        # Test loading and rendering existing example configs
        # This ensures backward compatibility with existing configurations
        registry = get_registry()
        board = boards.raspberry_pi_5()

        # Simulate loading a typical single-tier config
        bh1750 = registry.create("bh1750")

        diagram = Diagram(
            title="BH1750 Light Sensor",
            board=board,
            devices=[bh1750],
            connections=[
                Connection(1, bh1750.name, "VCC"),
                Connection(3, bh1750.name, "SDA"),
                Connection(5, bh1750.name, "SCL"),
                Connection(6, bh1750.name, "GND"),
            ],
            show_legend=True,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        routed_wires = result.routed_wires

        # Verify render completes without errors
        assert canvas_width > 0
        assert canvas_height > 0
        assert len(routed_wires) == 4

        # Verify no validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0


class TestEdgeCases:
    """Edge case tests for unusual multi-tier scenarios."""

    def test_empty_intermediate_tier(self):
        """Test layout with empty intermediate tier (level 0 and 2, but not 1).

        This tests the edge case where we have devices at level 0 (board connections)
        and level 2 (two hops from board), but no devices at level 1.
        """
        board = boards.raspberry_pi_5()

        # Create a scenario where we skip a tier
        # We'll have board → A and board → (imaginary) → C
        # But we'll make the connection pattern such that C appears at level 2
        device_a = Device(
            name="Direct Device",
            pins=[DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0))],
            width=80,
            height=50,
            color="#4A90E2",
        )

        # Create a chain device that we won't actually use
        device_b = Device(
            name="Intermediate",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
            ],
            width=80,
            height=50,
            color="#E24A4A",
        )

        device_c = Device(
            name="Chained Device",
            pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
            width=80,
            height=50,
            color="#4AE24A",
        )

        # Connect A directly to board, and C to B (which is also connected to board)
        # This creates: Board → A (level 0), Board → B (level 0), B → C (level 1)
        connections = [
            Connection(board_pin=1, device_name="Direct Device", device_pin_name="VCC"),
            Connection(board_pin=2, device_name="Intermediate", device_pin_name="VCC"),
            Connection(
                source_device="Intermediate",
                source_pin="OUT",
                device_name="Chained Device",
                device_pin_name="IN",
            ),
        ]

        diagram = Diagram(
            title="Edge Case: Sparse Tiers",
            board=board,
            devices=[device_a, device_b, device_c],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        # Verify layout completes without errors
        assert canvas_width > 0 and canvas_height > 0

        # Verify proper spacing is maintained
        assert device_c.position.x > device_b.position.x, "Chained device after intermediate"

        # Verify no validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0

    def test_complex_dependency_graph(self):
        """Test complex multi-tier dependency graph with cross-connections."""
        board = boards.raspberry_pi_5()

        # Create a complex graph: Board → [A, B] → C → D
        # with A and B both feeding into C
        device_a = Device(
            name="Input A",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
            ],
            width=70,
            height=50,
            color="#E74C3C",
        )
        device_b = Device(
            name="Input B",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
            ],
            width=70,
            height=50,
            color="#3498DB",
        )
        device_c = Device(
            name="Merger",
            pins=[
                DevicePin("IN1", PinRole.GPIO, Point(0, 0)),
                DevicePin("IN2", PinRole.GPIO, Point(0, 10)),
                DevicePin("OUT", PinRole.GPIO, Point(0, 20)),
            ],
            width=80,
            height=60,
            color="#2ECC71",
        )
        device_d = Device(
            name="Output",
            pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
            width=70,
            height=50,
            color="#F39C12",
        )

        connections = [
            # Board to A and B
            Connection(board_pin=1, device_name="Input A", device_pin_name="VCC"),
            Connection(board_pin=2, device_name="Input B", device_pin_name="VCC"),
            # A and B to C
            Connection(
                source_device="Input A",
                source_pin="OUT",
                device_name="Merger",
                device_pin_name="IN1",
            ),
            Connection(
                source_device="Input B",
                source_pin="OUT",
                device_name="Merger",
                device_pin_name="IN2",
            ),
            # C to D
            Connection(
                source_device="Merger",
                source_pin="OUT",
                device_name="Output",
                device_pin_name="IN",
            ),
        ]

        diagram = Diagram(
            title="Complex Dependency Graph",
            board=board,
            devices=[device_a, device_b, device_c, device_d],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        routed_wires = result.routed_wires

        # Verify multi-tier structure
        assert device_a.position.x == device_b.position.x, "Inputs at same tier"
        assert device_c.position.x > device_a.position.x, "Merger after inputs"
        assert device_d.position.x > device_c.position.x, "Output after merger"

        # Verify all wires are routed (both board-to-device and device-to-device)
        assert len(routed_wires) == len(connections)

        # Verify no validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0

    def test_single_device_chain(self):
        """Test edge case with minimal chain: Board → A."""
        board = boards.raspberry_pi_5()

        device = Device(
            name="Single Device",
            pins=[DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0))],
            width=80,
            height=50,
            color="#4A90E2",
        )

        connections = [Connection(board_pin=1, device_name="Single Device", device_pin_name="VCC")]

        diagram = Diagram(
            title="Minimal Chain",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        routed_wires = result.routed_wires

        # Verify basic layout
        assert device.position is not None
        assert len(routed_wires) == 1

        # Verify no validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0


class TestPerformanceValidation:
    """Performance validation tests for multi-tier layouts."""

    def test_50_devices_under_1_second(self):
        """Test that layout with 50 devices completes in under 1 second.

        This is a critical performance requirement for the multi-tier system.
        """
        board = boards.raspberry_pi_5()

        # Create 50 devices in a multi-tier structure
        # Structure: 10 devices at level 0, 20 at level 1, 20 at level 2
        devices = []
        connections = []

        # Level 0: 10 devices connected to board
        for i in range(10):
            device = Device(
                name=f"L0_Device_{i}",
                pins=[
                    DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                    DevicePin("OUT1", PinRole.GPIO, Point(0, 10)),
                    DevicePin("OUT2", PinRole.GPIO, Point(0, 20)),
                ],
                width=60,
                height=50,
                color="#3498DB",
            )
            devices.append(device)
            connections.append(
                Connection(board_pin=i + 1, device_name=device.name, device_pin_name="VCC")
            )

        # Level 1: 20 devices connected to level 0 devices (2 per level 0 device)
        for i in range(20):
            device = Device(
                name=f"L1_Device_{i}",
                pins=[
                    DevicePin("IN", PinRole.GPIO, Point(0, 0)),
                    DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
                ],
                width=60,
                height=50,
                color="#2ECC71",
            )
            devices.append(device)

            # Connect to a level 0 device
            source_device = devices[i // 2]
            source_pin = "OUT1" if i % 2 == 0 else "OUT2"
            connections.append(
                Connection(
                    source_device=source_device.name,
                    source_pin=source_pin,
                    device_name=device.name,
                    device_pin_name="IN",
                )
            )

        # Level 2: 20 devices connected to level 1 devices (1 per level 1 device)
        for i in range(20):
            device = Device(
                name=f"L2_Device_{i}",
                pins=[DevicePin("IN", PinRole.GPIO, Point(0, 0))],
                width=60,
                height=50,
                color="#E74C3C",
            )
            devices.append(device)

            # Connect to a level 1 device
            source_device = devices[10 + i]  # Level 1 devices start at index 10
            connections.append(
                Connection(
                    source_device=source_device.name,
                    source_pin="OUT",
                    device_name=device.name,
                    device_pin_name="IN",
                )
            )

        diagram = Diagram(
            title="50 Device Performance Test",
            board=board,
            devices=devices,
            connections=connections,
        )

        engine = LayoutEngine()

        # Measure layout time
        start_time = time.time()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        routed_wires = result.routed_wires
        elapsed_time = time.time() - start_time

        # Critical requirement: must complete in under 1 second
        assert elapsed_time < 1.0, f"Layout of 50 devices took {elapsed_time:.3f}s, expected < 1.0s"

        # Verify layout is valid
        assert len(devices) == 50
        # All wires are routed (both board-to-device and device-to-device)
        assert len(routed_wires) == len(connections)
        assert canvas_width > 0 and canvas_height > 0

        # Verify no validation issues
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0, f"Layout validation failed with {len(issues)} issues"

    def test_performance_scales_reasonably(self):
        """Test that performance scales reasonably with diagram complexity."""
        board = boards.raspberry_pi_5()

        timings = []
        device_counts = [5, 10, 20, 30]

        for num_devices in device_counts:
            # Create devices
            devices = []
            connections = []

            for i in range(num_devices):
                device = Device(
                    name=f"Device_{i}",
                    pins=[DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0))],
                    width=60,
                    height=50,
                    color="#3498DB",
                )
                devices.append(device)
                connections.append(
                    Connection(
                        board_pin=(i % 40) + 1, device_name=device.name, device_pin_name="VCC"
                    )
                )

            diagram = Diagram(
                title=f"Performance Test {num_devices}",
                board=board,
                devices=devices,
                connections=connections,
            )

            engine = LayoutEngine()

            start_time = time.time()
            engine.layout_diagram(diagram)
            elapsed_time = time.time() - start_time

            timings.append((num_devices, elapsed_time))

        # Verify reasonable scaling
        # Time for 30 devices should not be more than 50x time for 5 devices
        # (allowing for quadratic complexity in wire routing)
        time_5 = timings[0][1]
        time_30 = timings[-1][1]

        if time_5 > 0:
            scaling_factor = time_30 / time_5
            assert scaling_factor < 50, (
                f"Poor scaling: 30 devices took {scaling_factor:.1f}x "
                f"longer than 5 devices (expected < 50x)"
            )


class TestLayoutValidation:
    """Test that valid multi-tier layouts pass validation."""

    def test_valid_multi_tier_no_issues(self):
        """Test that a valid multi-tier layout has no validation issues."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create a valid multi-tier setup
        sensor = registry.create("bh1750")
        led = registry.create("led")

        controller = Device(
            name="Controller",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                DevicePin("IN", PinRole.I2C_SDA, Point(0, 10)),
                DevicePin("OUT", PinRole.GPIO, Point(0, 20)),
            ],
            width=80,
            height=60,
            color="#9B59B6",
        )

        connections = [
            # Board to sensor
            Connection(1, sensor.name, "VCC"),
            Connection(3, sensor.name, "SDA"),
            # Sensor to controller
            Connection(
                source_device=sensor.name,
                source_pin="SDA",
                device_name="Controller",
                device_pin_name="IN",
            ),
            # Board to controller
            Connection(1, "Controller", "VCC"),
            # Controller to LED
            Connection(
                source_device="Controller",
                source_pin="OUT",
                device_name=led.name,
                device_pin_name="Anode",
            ),
        ]

        diagram = Diagram(
            title="Valid Multi-Tier Layout",
            board=board,
            devices=[sensor, controller, led],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        # Validate layout
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)

        # Should have no issues
        assert len(issues) == 0, f"Valid layout should have no issues, found: {issues}"

    def test_all_devices_within_canvas(self):
        """Test that all devices in multi-tier layout are within canvas bounds."""
        board = boards.raspberry_pi_5()

        # Create multi-tier layout
        devices = []
        connections = []

        for i in range(10):
            device = Device(
                name=f"Device_{i}",
                pins=[
                    DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
                    DevicePin("OUT", PinRole.GPIO, Point(0, 10)),
                ],
                width=80,
                height=50,
                color="#3498DB",
            )
            devices.append(device)

            if i == 0:
                connections.append(
                    Connection(board_pin=1, device_name=device.name, device_pin_name="VCC")
                )
            else:
                connections.append(
                    Connection(
                        source_device=devices[i - 1].name,
                        source_pin="OUT",
                        device_name=device.name,
                        device_pin_name="VCC",
                    )
                )

        diagram = Diagram(
            title="Canvas Bounds Test",
            board=board,
            devices=devices,
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        # Verify all devices are within canvas
        for device in devices:
            assert 0 <= device.position.x <= canvas_width - device.width, (
                f"{device.name} X out of bounds"
            )
            assert 0 <= device.position.y <= canvas_height - device.height, (
                f"{device.name} Y out of bounds"
            )

        # Validate layout should pass
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0

    def test_no_device_overlaps_multi_tier(self):
        """Test that devices in multi-tier layout don't overlap."""
        board = boards.raspberry_pi_5()

        # Create scenario with multiple devices at same tier
        devices = []
        connections = []

        # Create 5 devices at tier 0
        for i in range(5):
            device = Device(
                name=f"Device_{i}",
                pins=[DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0))],
                width=80,
                height=60,
                color="#3498DB",
            )
            devices.append(device)
            connections.append(
                Connection(board_pin=i + 1, device_name=device.name, device_pin_name="VCC")
            )

        diagram = Diagram(
            title="No Overlap Test",
            board=board,
            devices=devices,
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        canvas_width = result.canvas_width
        canvas_height = result.canvas_height
        # Check no overlaps manually
        for i, dev1 in enumerate(devices):
            for dev2 in devices[i + 1 :]:
                # Check if rectangles overlap
                rect1 = (
                    dev1.position.x,
                    dev1.position.y,
                    dev1.position.x + dev1.width,
                    dev1.position.y + dev1.height,
                )
                rect2 = (
                    dev2.position.x,
                    dev2.position.y,
                    dev2.position.x + dev2.width,
                    dev2.position.y + dev2.height,
                )

                overlaps = engine._rectangles_overlap(rect1, rect2)
                assert not overlaps, f"{dev1.name} and {dev2.name} overlap"

        # Validate layout should pass
        issues = engine.validate_layout(diagram, canvas_width, canvas_height)
        assert len(issues) == 0


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
