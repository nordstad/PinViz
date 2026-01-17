"""Tests for ConfigLoader with multi-level connections (Phase 2.2)."""

import pytest

from pinviz.config_loader import ConfigLoader
from pinviz.model import WireStyle


class TestConfigLoaderLegacyFormat:
    """Test ConfigLoader with legacy connection format (backward compatibility)."""

    def test_load_legacy_format(self):
        """Test loading legacy board-to-device format."""
        config = {
            "title": "Legacy Format Test",
            "board": "raspberry_pi_5",
            "devices": [{"type": "led", "name": "LED"}],
            "connections": [{"board_pin": 1, "device": "LED", "device_pin": "VCC"}],
        }

        loader = ConfigLoader()
        diagram = loader.load_from_dict(config)

        assert len(diagram.connections) == 1
        conn = diagram.connections[0]
        assert conn.is_board_connection()
        assert conn.board_pin == 1
        assert conn.device_name == "LED"
        assert conn.device_pin_name == "VCC"

    def test_load_legacy_format_with_options(self):
        """Test legacy format with color, style, and components."""
        config = {
            "title": "Legacy Options Test",
            "board": "raspberry_pi_5",
            "devices": [{"type": "led", "name": "LED"}],
            "connections": [
                {
                    "board_pin": 11,
                    "device": "LED",
                    "device_pin": "Anode",
                    "color": "#FF0000",
                    "style": "curved",
                    "components": [{"type": "resistor", "value": "220Ω"}],
                }
            ],
        }

        loader = ConfigLoader()
        diagram = loader.load_from_dict(config)

        assert len(diagram.connections) == 1
        conn = diagram.connections[0]
        assert conn.is_board_connection()
        assert conn.color == "#FF0000"
        assert conn.style == WireStyle.CURVED
        assert len(conn.components) == 1
        assert conn.components[0].value == "220Ω"


class TestConfigLoaderNewFormat:
    """Test ConfigLoader with new from/to connection format."""

    def test_load_new_format_board_source(self):
        """Test loading new format with board source."""
        config = {
            "title": "New Format Board Source",
            "board": "raspberry_pi_5",
            "devices": [{"type": "led", "name": "LED"}],
            "connections": [
                {"from": {"board_pin": 1}, "to": {"device": "LED", "device_pin": "VCC"}}
            ],
        }

        loader = ConfigLoader()
        diagram = loader.load_from_dict(config)

        assert len(diagram.connections) == 1
        conn = diagram.connections[0]
        assert conn.is_board_connection()
        assert not conn.is_device_connection()
        assert conn.board_pin == 1
        assert conn.device_name == "LED"
        assert conn.device_pin_name == "VCC"

    def test_load_new_format_device_source(self):
        """Test loading new format with device source (device-to-device)."""
        config = {
            "title": "New Format Device Source",
            "board": "raspberry_pi_5",
            "devices": [
                {"name": "Regulator", "pins": [{"name": "VOUT", "role": "3V3"}]},
                {"type": "led", "name": "LED"},
            ],
            "connections": [
                {
                    "from": {"device": "Regulator", "device_pin": "VOUT"},
                    "to": {"device": "LED", "device_pin": "VCC"},
                }
            ],
        }

        loader = ConfigLoader()
        diagram = loader.load_from_dict(config)

        assert len(diagram.connections) == 1
        conn = diagram.connections[0]
        assert conn.is_device_connection()
        assert not conn.is_board_connection()
        assert conn.source_device == "Regulator"
        assert conn.source_pin == "VOUT"
        assert conn.device_name == "LED"
        assert conn.device_pin_name == "VCC"

    def test_load_new_format_with_options(self):
        """Test new format with color, style, net, and components."""
        config = {
            "title": "New Format Options",
            "board": "raspberry_pi_5",
            "devices": [
                {"name": "Regulator", "pins": [{"name": "VOUT", "role": "3V3"}]},
                {"type": "led", "name": "LED"},
            ],
            "connections": [
                {
                    "from": {"device": "Regulator", "device_pin": "VOUT"},
                    "to": {"device": "LED", "device_pin": "VCC"},
                    "color": "#00FF00",
                    "style": "orthogonal",
                    "net": "LED_POWER",
                    "components": [
                        {"type": "resistor", "value": "220Ω", "position": 0.5},
                        {"type": "diode", "value": "1N4148"},
                    ],
                }
            ],
        }

        loader = ConfigLoader()
        diagram = loader.load_from_dict(config)

        assert len(diagram.connections) == 1
        conn = diagram.connections[0]
        assert conn.is_device_connection()
        assert conn.color == "#00FF00"
        assert conn.style == WireStyle.ORTHOGONAL
        assert conn.net_name == "LED_POWER"
        assert len(conn.components) == 2
        assert conn.components[0].value == "220Ω"
        assert conn.components[0].position == 0.5
        assert conn.components[1].value == "1N4148"


class TestConfigLoaderMixedFormats:
    """Test ConfigLoader with mixed connection formats in same config."""

    def test_load_mixed_formats_in_config(self):
        """Test loading config with both legacy and new format connections."""
        config = {
            "title": "Mixed Format Test",
            "board": "raspberry_pi_5",
            "devices": [
                {"name": "Regulator", "pins": [{"name": "VOUT", "role": "3V3"}]},
                {"type": "led", "name": "LED1"},
                {"type": "led", "name": "LED2"},
            ],
            "connections": [
                # Legacy format: Board to LED1
                {"board_pin": 1, "device": "LED1", "device_pin": "VCC"},
                # New format with board source: Board to Regulator
                {"from": {"board_pin": 2}, "to": {"device": "Regulator", "device_pin": "VIN"}},
                # New format with device source: Regulator to LED2
                {
                    "from": {"device": "Regulator", "device_pin": "VOUT"},
                    "to": {"device": "LED2", "device_pin": "VCC"},
                },
            ],
        }

        loader = ConfigLoader()
        diagram = loader.load_from_dict(config)

        assert len(diagram.connections) == 3

        # First connection: legacy format (board to LED1)
        conn1 = diagram.connections[0]
        assert conn1.is_board_connection()
        assert conn1.board_pin == 1
        assert conn1.device_name == "LED1"

        # Second connection: new format, board source (board to Regulator)
        conn2 = diagram.connections[1]
        assert conn2.is_board_connection()
        assert conn2.board_pin == 2
        assert conn2.device_name == "Regulator"

        # Third connection: new format, device source (Regulator to LED2)
        conn3 = diagram.connections[2]
        assert conn3.is_device_connection()
        assert conn3.source_device == "Regulator"
        assert conn3.source_pin == "VOUT"
        assert conn3.device_name == "LED2"


class TestConfigLoaderValidation:
    """Test ConfigLoader validation of connection formats."""

    def test_reject_invalid_connection_format(self):
        """Test that invalid connection format is rejected."""
        config = {
            "title": "Invalid Format",
            "board": "raspberry_pi_5",
            "devices": [{"type": "led", "name": "LED"}],
            "connections": [
                # Missing required fields
                {"device": "LED"}
            ],
        }

        loader = ConfigLoader()
        with pytest.raises(ValueError, match="Configuration validation failed"):
            loader.load_from_dict(config)

    def test_reject_mixed_format_in_single_connection(self):
        """Test that mixing formats in a single connection is rejected."""
        config = {
            "title": "Mixed Format Single Connection",
            "board": "raspberry_pi_5",
            "devices": [{"type": "led", "name": "LED"}],
            "connections": [
                # Mixing legacy and new format in same connection
                {
                    "board_pin": 1,
                    "device": "LED",
                    "device_pin": "VCC",
                    "from": {"board_pin": 2},
                    "to": {"device": "LED", "device_pin": "VCC"},
                }
            ],
        }

        loader = ConfigLoader()
        with pytest.raises(ValueError, match="Cannot mix"):
            loader.load_from_dict(config)


class TestConfigLoaderDeviceToDevice:
    """Test ConfigLoader with complex device-to-device connection scenarios."""

    def test_load_power_chain(self):
        """Test loading a power chain: Board -> Regulator -> Multiple Devices."""
        config = {
            "title": "Power Chain",
            "board": "raspberry_pi_5",
            "devices": [
                {
                    "name": "Regulator",
                    "pins": [
                        {"name": "VIN", "role": "5V"},
                        {"name": "GND", "role": "GND"},
                        {"name": "VOUT", "role": "3V3"},
                    ],
                },
                {"type": "bh1750", "name": "Sensor"},
                {"type": "led", "name": "LED"},
            ],
            "connections": [
                # Board to Regulator
                {"from": {"board_pin": 2}, "to": {"device": "Regulator", "device_pin": "VIN"}},
                {"board_pin": 6, "device": "Regulator", "device_pin": "GND"},
                # Regulator to Sensor
                {
                    "from": {"device": "Regulator", "device_pin": "VOUT"},
                    "to": {"device": "Sensor", "device_pin": "VCC"},
                },
                # Regulator to LED
                {
                    "from": {"device": "Regulator", "device_pin": "VOUT"},
                    "to": {"device": "LED", "device_pin": "VCC"},
                },
            ],
        }

        loader = ConfigLoader()
        diagram = loader.load_from_dict(config)

        assert len(diagram.connections) == 4

        # Count connection types
        board_connections = [c for c in diagram.connections if c.is_board_connection()]
        device_connections = [c for c in diagram.connections if c.is_device_connection()]

        assert len(board_connections) == 2
        assert len(device_connections) == 2

        # Verify device-to-device connections
        for conn in device_connections:
            assert conn.source_device == "Regulator"
            assert conn.source_pin == "VOUT"
            assert conn.device_name in ["Sensor", "LED"]
