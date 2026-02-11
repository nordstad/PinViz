"""Unit tests for pin side placement with device-to-device connections."""

import pytest

from pinviz.config_loader import ConfigLoader
from pinviz.devices.loader import load_device_from_config


class TestDeviceToDeviceWithSidePlacement:
    """Test device-to-device connections with explicit side placement."""

    def test_relay_led_device_chain(self):
        """Test relay switching LED with device-to-device connection."""
        loader = ConfigLoader()
        config = {
            "title": "Relay LED Chain",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "relay_module", "name": "Relay"},
                {"type": "led", "name": "LED"},
            ],
            "connections": [
                # Board to relay
                {"board_pin": 2, "device": "Relay", "device_pin": "VCC"},
                {"board_pin": 11, "device": "Relay", "device_pin": "IN"},
                # Relay to LED (device-to-device)
                {
                    "from": {"device": "Relay", "device_pin": "NO"},
                    "to": {"device": "LED", "device_pin": "+"},
                },
            ],
        }

        diagram = loader.load_from_dict(config)

        # Verify devices are created
        assert len(diagram.devices) == 2
        assert diagram.devices[0].name == "Relay"
        assert diagram.devices[1].name == "LED"

        # Verify connections include device-to-device
        assert len(diagram.connections) == 3
        device_to_device = [c for c in diagram.connections if c.is_device_connection()]
        assert len(device_to_device) == 1

        # Verify relay has correct pin sides
        relay = diagram.devices[0]
        relay_center = relay.width / 2
        pins_by_name = {pin.name: pin for pin in relay.pins}

        # Control pins on left
        assert pins_by_name["IN"].position.x < relay_center
        # Output pins on right
        assert pins_by_name["NO"].position.x > relay_center

    def test_two_relays_cascaded(self):
        """Test two relay modules connected device-to-device."""
        loader = ConfigLoader()
        config = {
            "title": "Cascaded Relays",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "relay_module", "name": "Relay 1"},
                {"type": "relay_module", "name": "Relay 2"},
            ],
            "connections": [
                # Board to Relay 1
                {"board_pin": 2, "device": "Relay 1", "device_pin": "VCC"},
                {"board_pin": 11, "device": "Relay 1", "device_pin": "IN"},
                # Relay 1 to Relay 2 (device-to-device)
                {
                    "from": {"device": "Relay 1", "device_pin": "NO"},
                    "to": {"device": "Relay 2", "device_pin": "COM"},
                },
                # Board to Relay 2
                {"board_pin": 4, "device": "Relay 2", "device_pin": "VCC"},
                {"board_pin": 12, "device": "Relay 2", "device_pin": "IN"},
            ],
        }

        diagram = loader.load_from_dict(config)

        # Verify two relays created
        assert len(diagram.devices) == 2

        # Both should have correct pin placement
        for relay in diagram.devices:
            center = relay.width / 2
            pins = {pin.name: pin for pin in relay.pins}

            # Control pins on left
            assert pins["VCC"].position.x < center
            assert pins["IN"].position.x < center

            # Output pins on right
            assert pins["NO"].position.x > center
            assert pins["COM"].position.x > center

        # Verify device-to-device connection
        d2d_connections = [c for c in diagram.connections if c.is_device_connection()]
        assert len(d2d_connections) == 1
        assert d2d_connections[0].source_device == "Relay 1"
        assert d2d_connections[0].source_pin == "NO"
        assert d2d_connections[0].device_name == "Relay 2"
        assert d2d_connections[0].device_pin_name == "COM"

    def test_mixed_sides_device_chain(self):
        """Test device chain with mixed explicit and automatic side placement."""
        loader = ConfigLoader()
        config = {
            "title": "Mixed Device Chain",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "mixed_sides", "name": "Source"},
                {"type": "single_pin_each_side", "name": "Sink"},
            ],
            "connections": [
                {"board_pin": 2, "device": "Source", "device_pin": "VCC"},
                {
                    "from": {"device": "Source", "device_pin": "OUT"},
                    "to": {"device": "Sink", "device_pin": "IN"},
                },
            ],
        }

        diagram = loader.load_from_dict(config)

        # Verify devices
        assert len(diagram.devices) == 2
        source = diagram.devices[0]
        sink = diagram.devices[1]

        # Source should have mixed sides
        source_pins = {pin.name: pin for pin in source.pins}
        source_center = source.width / 2
        assert source_pins["VCC"].position.x < source_center  # Left (explicit)
        assert source_pins["OUT"].position.x > source_center  # Right (automatic)

        # Sink should have one pin per side
        sink_pins = {pin.name: pin for pin in sink.pins}
        sink_center = sink.width / 2
        assert sink_pins["IN"].position.x < sink_center  # Left (explicit)
        assert sink_pins["OUT"].position.x > sink_center  # Right (explicit)

    def test_three_device_chain_with_sides(self):
        """Test three devices connected in a chain with explicit sides."""
        loader = ConfigLoader()
        config = {
            "title": "Three Device Chain",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "all_left", "name": "Source"},
                {"type": "relay_module", "name": "Switch"},
                {"type": "all_right", "name": "Load"},
            ],
            "connections": [
                {"board_pin": 2, "device": "Source", "device_pin": "P1"},
                {
                    "from": {"device": "Source", "device_pin": "OUT"},
                    "to": {"device": "Switch", "device_pin": "IN"},
                },
                {"board_pin": 4, "device": "Switch", "device_pin": "VCC"},
                {
                    "from": {"device": "Switch", "device_pin": "NO"},
                    "to": {"device": "Load", "device_pin": "VCC"},
                },
            ],
        }

        diagram = loader.load_from_dict(config)

        # Verify all devices created
        assert len(diagram.devices) == 3

        # Verify source has all pins on left
        source = diagram.devices[0]
        source_center = source.width / 2
        for pin in source.pins:
            assert pin.position.x < source_center, f"Source pin {pin.name} should be on left"

        # Verify load has all pins on right
        load = diagram.devices[2]
        load_center = load.width / 2
        for pin in load.pins:
            assert pin.position.x > load_center, f"Load pin {pin.name} should be on right"

        # Verify two device-to-device connections
        d2d = [c for c in diagram.connections if c.is_device_connection()]
        assert len(d2d) == 2

    def test_side_placement_with_connection_graph(self):
        """Test that side placement works correctly with connection graph analysis."""
        loader = ConfigLoader()
        config = {
            "title": "Side Placement Graph Test",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "relay_module", "name": "R1"},
                {"type": "relay_module", "name": "R2"},
            ],
            "connections": [
                {"board_pin": 2, "device": "R1", "device_pin": "VCC"},
                {
                    "from": {"device": "R1", "device_pin": "NO"},
                    "to": {"device": "R2", "device_pin": "IN"},
                },
            ],
        }

        diagram = loader.load_from_dict(config)

        # Both relays should maintain their side placement
        for relay in diagram.devices:
            pins = {pin.name: pin for pin in relay.pins}
            center = relay.width / 2

            # Verify control pins on left
            assert pins["VCC"].position.x < center
            assert pins["IN"].position.x < center

            # Verify output pins on right
            assert pins["NO"].position.x > center

    def test_device_to_device_preserves_pin_roles(self):
        """Test that device-to-device connections preserve pin roles and sides."""
        # Load devices directly
        relay = load_device_from_config("relay_module")

        # Check that relay pins maintain their roles and positions
        pins = {pin.name: pin for pin in relay.pins}
        center = relay.width / 2

        # Control pins should be on left with correct roles
        assert pins["VCC"].role.value == "5V"
        assert pins["VCC"].position.x < center

        assert pins["IN"].role.value == "GPIO"
        assert pins["IN"].position.x < center

        # Output pins should be on right with correct roles
        assert pins["NO"].role.value == "5V"
        assert pins["NO"].position.x > center

        assert pins["COM"].role.value == "5V"
        assert pins["COM"].position.x > center


class TestDeviceToDeviceEdgeCases:
    """Test edge cases for device-to-device with side placement."""

    def test_all_left_to_all_right_connection(self):
        """Test connecting a device with all pins left to one with all pins right."""
        loader = ConfigLoader()
        config = {
            "title": "Left to Right",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "all_left", "name": "Left Device"},
                {"type": "all_right", "name": "Right Device"},
            ],
            "connections": [
                {"board_pin": 2, "device": "Left Device", "device_pin": "P1"},
                {
                    "from": {"device": "Left Device", "device_pin": "OUT"},
                    "to": {"device": "Right Device", "device_pin": "VCC"},
                },
            ],
        }

        diagram = loader.load_from_dict(config)

        # Verify unusual but valid configuration
        left_dev = diagram.devices[0]
        right_dev = diagram.devices[1]

        # All pins of left device should be on left
        for pin in left_dev.pins:
            assert pin.position.x < left_dev.width / 2

        # All pins of right device should be on right
        for pin in right_dev.pins:
            assert pin.position.x > right_dev.width / 2

    def test_single_pin_device_to_device(self):
        """Test minimal single-pin-per-side devices connected."""
        loader = ConfigLoader()
        config = {
            "title": "Minimal Connection",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "single_pin_each_side", "name": "D1"},
                {"type": "single_pin_each_side", "name": "D2"},
            ],
            "connections": [
                {"board_pin": 11, "device": "D1", "device_pin": "IN"},
                {
                    "from": {"device": "D1", "device_pin": "OUT"},
                    "to": {"device": "D2", "device_pin": "IN"},
                },
                {"board_pin": 12, "device": "D2", "device_pin": "OUT"},
            ],
        }

        diagram = loader.load_from_dict(config)

        # Both devices should have correct pin placement
        for device in diagram.devices:
            pins = {pin.name: pin for pin in device.pins}
            center = device.width / 2

            assert pins["IN"].position.x < center
            assert pins["OUT"].position.x > center

    def test_device_to_device_with_automatic_detection(self):
        """Test device-to-device where one uses automatic, one uses explicit."""
        loader = ConfigLoader()
        config = {
            "title": "Auto vs Explicit",
            "board": "raspberry_pi_5",
            "devices": [
                {"type": "relay_auto", "name": "Auto"},  # Automatic detection
                {"type": "relay_module", "name": "Explicit"},  # Explicit sides
            ],
            "connections": [
                {"board_pin": 2, "device": "Auto", "device_pin": "VCC"},
                {
                    "from": {"device": "Auto", "device_pin": "COM"},
                    "to": {"device": "Explicit", "device_pin": "COM"},
                },
            ],
        }

        diagram = loader.load_from_dict(config)

        # Both should have COM on the right (automatic and explicit should agree)
        for device in diagram.devices:
            pins = {pin.name: pin for pin in device.pins}
            center = device.width / 2

            # COM should be on right in both cases
            assert pins["COM"].position.x > center
