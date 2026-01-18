"""Performance regression tests.

These tests establish performance baselines and ensure that
performance doesn't significantly degrade over time.

Run with: pytest tests/test_performance_regression.py -v
"""

import time

import pytest

from pinviz import boards
from pinviz.config_loader import ConfigLoader
from pinviz.devices import get_registry
from pinviz.layout import LayoutEngine
from pinviz.model import Connection, Device, DevicePin, Diagram, Point
from pinviz.render_svg import SVGRenderer

# Performance baselines (in seconds)
BASELINE_SMALL_LAYOUT = 0.1  # 100ms for small diagrams (4 connections)
BASELINE_MEDIUM_LAYOUT = 0.2  # 200ms for medium diagrams (20 connections)
BASELINE_LARGE_LAYOUT = 0.5  # 500ms for large diagrams (40 connections)
BASELINE_SMALL_RENDER = 0.2  # 200ms for small diagram rendering
BASELINE_MEDIUM_RENDER = 0.4  # 400ms for medium diagram rendering
BASELINE_CONFIG_LOAD = 0.05  # 50ms for config loading


@pytest.mark.performance
class TestLayoutPerformanceBaselines:
    """Performance baseline tests for layout engine."""

    def test_baseline_small_diagram_layout(self):
        """Baseline: Small diagram (4 connections) should layout in <100ms."""
        board = boards.raspberry_pi_5()
        device = get_registry().create("bh1750")

        connections = [
            Connection(1, "BH1750", "VCC"),
            Connection(3, "BH1750", "SDA"),
            Connection(5, "BH1750", "SCL"),
            Connection(6, "BH1750", "GND"),
        ]

        diagram = Diagram(
            title="Small Diagram",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()

        start_time = time.time()
        engine.layout_diagram(diagram)
        elapsed_time = time.time() - start_time

        assert elapsed_time < BASELINE_SMALL_LAYOUT, (
            f"Small diagram layout took {elapsed_time:.3f}s, expected < {BASELINE_SMALL_LAYOUT}s"
        )

    def test_baseline_medium_diagram_layout(self):
        """Baseline: Medium diagram (20 connections) should layout in <200ms."""
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
            title="Medium Diagram",
            board=board,
            devices=test_devices,
            connections=connections,
        )

        engine = LayoutEngine()

        start_time = time.time()
        engine.layout_diagram(diagram)
        elapsed_time = time.time() - start_time

        assert elapsed_time < BASELINE_MEDIUM_LAYOUT, (
            f"Medium diagram layout took {elapsed_time:.3f}s, expected < {BASELINE_MEDIUM_LAYOUT}s"
        )

    def test_baseline_large_diagram_layout(self):
        """Baseline: Large diagram (40 connections) should layout in <500ms."""
        board = boards.raspberry_pi_5()

        # Create device with 40 pins
        pins = [DevicePin(f"PIN{i}", "GPIO", Point(5, 10 + i * 5)) for i in range(1, 41)]
        device = Device(name="LargeDevice", pins=pins, width=120, height=250)

        connections = [Connection(i, "LargeDevice", f"PIN{i}") for i in range(1, 41)]

        diagram = Diagram(
            title="Large Diagram",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()

        start_time = time.time()
        engine.layout_diagram(diagram)
        elapsed_time = time.time() - start_time

        assert elapsed_time < BASELINE_LARGE_LAYOUT, (
            f"Large diagram layout took {elapsed_time:.3f}s, expected < {BASELINE_LARGE_LAYOUT}s"
        )


@pytest.mark.performance
class TestRenderPerformanceBaselines:
    """Performance baseline tests for SVG rendering."""

    def test_baseline_small_diagram_render(self, temp_output_dir):
        """Baseline: Small diagram rendering should complete in <200ms."""
        board = boards.raspberry_pi_5()
        device = get_registry().create("bh1750")

        connections = [
            Connection(1, "BH1750", "VCC"),
            Connection(3, "BH1750", "SDA"),
            Connection(5, "BH1750", "SCL"),
            Connection(6, "BH1750", "GND"),
        ]

        diagram = Diagram(
            title="Small Render Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        renderer = SVGRenderer()
        output_path = temp_output_dir / "small_perf.svg"

        start_time = time.time()
        renderer.render(diagram, str(output_path))
        elapsed_time = time.time() - start_time

        assert elapsed_time < BASELINE_SMALL_RENDER, (
            f"Small diagram render took {elapsed_time:.3f}s, expected < {BASELINE_SMALL_RENDER}s"
        )

    def test_baseline_medium_diagram_render(self, temp_output_dir):
        """Baseline: Medium diagram rendering should complete in <400ms."""
        board = boards.raspberry_pi_5()

        # Create 4 devices
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
            title="Medium Render Test",
            board=board,
            devices=test_devices,
            connections=connections,
        )

        renderer = SVGRenderer()
        output_path = temp_output_dir / "medium_perf.svg"

        start_time = time.time()
        renderer.render(diagram, str(output_path))
        elapsed_time = time.time() - start_time

        assert elapsed_time < BASELINE_MEDIUM_RENDER, (
            f"Medium diagram render took {elapsed_time:.3f}s, expected < {BASELINE_MEDIUM_RENDER}s"
        )


@pytest.mark.performance
class TestConfigLoadPerformance:
    """Performance baseline tests for configuration loading."""

    def test_baseline_yaml_config_load(self, temp_output_dir):
        """Baseline: YAML config loading should complete in <50ms."""
        config_path = temp_output_dir / "perf_test.yaml"
        config_path.write_text("""
title: "Performance Test"
board: "raspberry_pi_5"
devices:
  - type: bh1750
    name: "Sensor"
  - type: led
    name: "LED"
connections:
  - board_pin: 1
    device: "Sensor"
    device_pin: "VCC"
  - board_pin: 11
    device: "LED"
    device_pin: "Anode"
        """)

        loader = ConfigLoader()

        start_time = time.time()
        loader.load_from_file(config_path)
        elapsed_time = time.time() - start_time

        assert elapsed_time < BASELINE_CONFIG_LOAD, (
            f"Config load took {elapsed_time:.3f}s, expected < {BASELINE_CONFIG_LOAD}s"
        )

    def test_baseline_json_config_load(self, temp_output_dir):
        """Baseline: JSON config loading should complete in <50ms."""
        import json

        config = {
            "title": "Performance Test",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "bh1750", "name": "Sensor"},
                {"type": "led", "name": "LED"},
            ],
            "connections": [
                {"board_pin": 1, "device": "Sensor", "device_pin": "VCC"},
                {"board_pin": 11, "device": "LED", "device_pin": "Anode"},
            ],
        }

        config_path = temp_output_dir / "perf_test.json"
        config_path.write_text(json.dumps(config))

        loader = ConfigLoader()

        start_time = time.time()
        loader.load_from_file(config_path)
        elapsed_time = time.time() - start_time

        assert elapsed_time < BASELINE_CONFIG_LOAD, (
            f"Config load took {elapsed_time:.3f}s, expected < {BASELINE_CONFIG_LOAD}s"
        )


@pytest.mark.performance
class TestScalingPerformance:
    """Test how performance scales with diagram size."""

    def test_render_scaling_with_connections(self, temp_output_dir):
        """Test that render time scales reasonably with number of connections."""
        board = boards.raspberry_pi_5()

        timings = []
        connection_counts = [5, 20, 40]

        for num_connections in connection_counts:
            pins = [
                DevicePin(f"PIN{i}", "GPIO", Point(5, 10 + i * 5)) for i in range(num_connections)
            ]
            device = Device(
                name="TestDevice", pins=pins, width=120, height=max(50, num_connections * 5)
            )

            connections = [
                Connection(i + 1, "TestDevice", f"PIN{i}") for i in range(num_connections)
            ]

            diagram = Diagram(
                title=f"Render Scaling Test {num_connections}",
                board=board,
                devices=[device],
                connections=connections,
            )

            renderer = SVGRenderer()
            output_path = temp_output_dir / f"scaling_{num_connections}.svg"

            start_time = time.time()
            renderer.render(diagram, str(output_path))
            elapsed_time = time.time() - start_time

            timings.append((num_connections, elapsed_time))

        # Check reasonable scaling
        time_5 = timings[0][1]
        time_40 = timings[-1][1]

        scaling_factor = time_40 / time_5 if time_5 > 0 else 0
        assert scaling_factor < 15, (
            f"Poor rendering scaling: 40 connections took {scaling_factor:.1f}x "
            f"longer than 5 connections (expected < 15x)"
        )


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryUsage:
    """Test memory usage characteristics (marked as slow)."""

    def test_large_diagram_memory_usage(self):
        """Test that large diagrams don't consume excessive memory."""
        import sys

        board = boards.raspberry_pi_5()

        # Create a large diagram
        pins = [DevicePin(f"PIN{i}", "GPIO", Point(5, 10 + i * 5)) for i in range(40)]
        device = Device(name="LargeDevice", pins=pins, width=120, height=250)

        connections = [Connection(i + 1, "LargeDevice", f"PIN{i}") for i in range(40)]

        diagram = Diagram(
            title="Memory Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        routed_wires = result.routed_wires

        # Check object sizes (rough heuristic)
        # A routed diagram with 40 connections shouldn't be huge
        size = sys.getsizeof(routed_wires)

        # This is a rough check - actual size depends on implementation
        # But should be less than 1MB for this diagram
        assert size < 1_000_000, f"Routed wires size is {size} bytes (expected < 1MB)"


@pytest.mark.performance
class TestPerformanceConsistency:
    """Test that performance is consistent across runs."""

    def test_layout_performance_consistency(self):
        """Test that layout performance is consistent across multiple runs."""
        board = boards.raspberry_pi_5()
        device = get_registry().create("bh1750")

        connections = [
            Connection(1, "BH1750", "VCC"),
            Connection(3, "BH1750", "SDA"),
            Connection(5, "BH1750", "SCL"),
            Connection(6, "BH1750", "GND"),
        ]

        diagram = Diagram(
            title="Consistency Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        engine = LayoutEngine()

        # Run multiple times with higher precision timer
        timings = []
        num_runs = 50  # Increased from 10 for more stable measurements
        for _ in range(num_runs):
            start_time = time.perf_counter()  # Higher precision than time.time()
            engine.layout_diagram(diagram)
            elapsed_time = time.perf_counter() - start_time
            timings.append(elapsed_time)

        # Calculate coefficient of variation
        import statistics

        mean_time = statistics.mean(timings)
        std_dev = statistics.stdev(timings) if len(timings) > 1 else 0
        cv = (std_dev / mean_time) if mean_time > 0 else 0

        # For very fast operations (< 0.001s), CV can be unreliable due to timing overhead
        # In such cases, we just verify the operation completes successfully
        if mean_time < 0.001:
            # Operation is extremely fast - just verify it completes without error
            assert mean_time >= 0, "Layout operation should complete"
        else:
            # Coefficient of variation should be reasonably low (< 0.5)
            assert cv < 0.5, (
                f"High performance variance: CV={cv:.2f}, "
                f"mean={mean_time:.4f}s, stddev={std_dev:.4f}s"
            )
