"""Tests for diagram complexity checking."""

import pytest

from pinviz import boards, Connection, Diagram
from pinviz.devices import get_registry
from pinviz.layout.engine import LayoutEngine
from pinviz.layout.types import LayoutConfig


class TestComplexityChecking:
    """Tests for complexity checking in LayoutEngine."""

    def test_simple_diagram_no_warnings(self):
        """Test that simple diagrams don't trigger warnings."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create small diagram (well under thresholds)
        devices = [registry.create("led", color_name="Red") for i in range(3)]
        for i, dev in enumerate(devices):
            dev.name = f"LED{i}"

        connections = [
            Connection.from_board(i + 1, f"LED{i}", "VCC")
            for i in range(3)
        ]

        diagram = Diagram(
            title="Simple Diagram",
            board=board,
            devices=devices,
            connections=connections,
        )

        # Should not raise any warnings or errors
        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        assert result is not None

    def test_warning_threshold_connections(self):
        """Test that warning is logged when exceeding connection threshold."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create diagram with 35 connections (> 30 threshold)
        devices = [registry.create("led", color_name="Red") for i in range(35)]
        for i, dev in enumerate(devices):
            dev.name = f"LED{i}"

        connections = [
            Connection.from_board(i + 1, f"LED{i}", "VCC")
            for i in range(35)
        ]

        diagram = Diagram(
            title="Complex Diagram",
            board=board,
            devices=devices,
            connections=connections,
        )

        # Should log warning but not raise error
        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        assert result is not None

    def test_warning_threshold_devices(self):
        """Test that warning is logged when exceeding device threshold."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create diagram with 25 devices (> 20 threshold)
        devices = [registry.create("led", color_name="Red") for i in range(25)]
        for i, dev in enumerate(devices):
            dev.name = f"LED{i}"

        connections = [
            Connection.from_board(i + 1, f"LED{i}", "VCC")
            for i in range(25)
        ]

        diagram = Diagram(
            title="Many Devices",
            board=board,
            devices=devices,
            connections=connections,
        )

        # Should log warning but not raise error
        engine = LayoutEngine()
        result = engine.layout_diagram(diagram)
        assert result is not None

    def test_max_connections_limit_enforced(self):
        """Test that max_connections hard limit is enforced."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create diagram with 35 connections
        devices = [registry.create("led", color_name="Red") for i in range(35)]
        for i, dev in enumerate(devices):
            dev.name = f"LED{i}"

        connections = [
            Connection.from_board(i + 1, f"LED{i}", "VCC")
            for i in range(35)
        ]

        diagram = Diagram(
            title="Complex Diagram",
            board=board,
            devices=devices,
            connections=connections,
        )

        # Set max_connections to 20
        config = LayoutConfig()
        config.max_connections = 20
        engine = LayoutEngine(config)

        # Should raise ValueError
        with pytest.raises(ValueError, match="35 connections, exceeding maximum of 20"):
            engine.layout_diagram(diagram)

    def test_max_devices_limit_enforced(self):
        """Test that max_devices hard limit is enforced."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create diagram with 25 devices
        devices = [registry.create("led", color_name="Red") for i in range(25)]
        for i, dev in enumerate(devices):
            dev.name = f"LED{i}"

        connections = [
            Connection.from_board(i + 1, f"LED{i}", "VCC")
            for i in range(25)
        ]

        diagram = Diagram(
            title="Many Devices",
            board=board,
            devices=devices,
            connections=connections,
        )

        # Set max_devices to 15
        config = LayoutConfig()
        config.max_devices = 15
        engine = LayoutEngine(config)

        # Should raise ValueError
        with pytest.raises(ValueError, match="25 devices, exceeding maximum of 15"):
            engine.layout_diagram(diagram)

    def test_custom_warning_thresholds(self):
        """Test that custom warning thresholds can be set."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create diagram with 6 connections
        devices = [registry.create("led", color_name="Red") for i in range(6)]
        for i, dev in enumerate(devices):
            dev.name = f"LED{i}"

        connections = [
            Connection.from_board(i + 1, f"LED{i}", "VCC")
            for i in range(6)
        ]

        diagram = Diagram(
            title="Small Diagram",
            board=board,
            devices=devices,
            connections=connections,
        )

        # Set custom thresholds (lower than default)
        config = LayoutConfig()
        config.warn_connections = 5
        config.warn_devices = 5
        engine = LayoutEngine(config)

        # Should log warnings (6 > 5)
        result = engine.layout_diagram(diagram)
        assert result is not None

    def test_no_limits_when_none(self):
        """Test that no limits are enforced when set to None."""
        board = boards.raspberry_pi_5()
        registry = get_registry()

        # Create large diagram
        devices = [registry.create("led", color_name="Red") for i in range(40)]
        for i, dev in enumerate(devices):
            dev.name = f"LED{i}"

        connections = [
            Connection.from_board(1, f"LED{i}", "VCC")
            for i in range(40)
        ]

        diagram = Diagram(
            title="Large Diagram",
            board=board,
            devices=devices,
            connections=connections,
        )

        # No hard limits (default)
        config = LayoutConfig()
        assert config.max_connections is None
        assert config.max_devices is None

        engine = LayoutEngine(config)

        # Should succeed (warnings logged but no errors)
        result = engine.layout_diagram(diagram)
        assert result is not None
