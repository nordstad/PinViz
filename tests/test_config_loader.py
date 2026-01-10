"""Tests for configuration loading."""

import json

import pytest

from pinviz.config_loader import ConfigLoader, load_diagram
from pinviz.model import ComponentType, WireStyle


def test_config_loader_creation():
    """Test creating a ConfigLoader instance."""
    loader = ConfigLoader()
    assert loader is not None


def test_load_from_yaml_file(sample_yaml_config):
    """Test loading a diagram from a YAML file."""
    loader = ConfigLoader()
    diagram = loader.load_from_file(sample_yaml_config)

    assert diagram is not None
    assert diagram.title == "Test Configuration"
    assert diagram.board.name == "Raspberry Pi 5"
    assert len(diagram.devices) == 2
    assert len(diagram.connections) == 6


def test_load_from_nonexistent_file():
    """Test loading from a non-existent file raises error."""
    loader = ConfigLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_from_file("/nonexistent/path/config.yaml")


def test_load_from_unsupported_format(temp_output_dir):
    """Test loading from unsupported file format raises error."""
    config_path = temp_output_dir / "test.txt"
    config_path.write_text("some content")

    loader = ConfigLoader()
    with pytest.raises(ValueError, match="Unsupported file format"):
        loader.load_from_file(config_path)


def test_load_from_json_file(temp_output_dir):
    """Test loading a diagram from a JSON file."""
    config = {
        "title": "JSON Test",
        "board": "raspberry_pi_5",
        "devices": [{"type": "bh1750", "name": "Sensor"}],
        "connections": [
            {
                "board_pin": 1,
                "device": "Sensor",
                "device_pin": "VCC",
            }
        ],
    }
    config_path = temp_output_dir / "test.json"
    config_path.write_text(json.dumps(config))

    loader = ConfigLoader()
    diagram = loader.load_from_file(config_path)

    assert diagram.title == "JSON Test"
    assert len(diagram.devices) == 1


def test_load_minimal_config():
    """Test loading a minimal configuration."""
    config = {
        "title": "Minimal",
        "board": "raspberry_pi_5",
        "devices": [],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert diagram.title == "Minimal"
    assert len(diagram.devices) == 0
    assert len(diagram.connections) == 0
    assert diagram.show_legend is True


def test_load_with_predefined_device():
    """Test loading a configuration with a predefined device."""
    config = {
        "title": "Test",
        "board": "raspberry_pi_5",
        "devices": [{"type": "bh1750"}],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert len(diagram.devices) == 1
    assert diagram.devices[0].name == "BH1750"


def test_load_with_device_name_override():
    """Test overriding device name."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "bh1750", "name": "My Sensor"}],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert diagram.devices[0].name == "My Sensor"


def test_load_with_custom_device():
    """Test loading a custom device definition."""
    config = {
        "title": "Custom Device Test",
        "board": "raspberry_pi",
        "devices": [
            {
                "name": "Custom Module",
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "DATA", "role": "GPIO"},
                ],
                "width": 60,
                "height": 30,
                "color": "#FF0000",
            }
        ],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert len(diagram.devices) == 1
    device = diagram.devices[0]
    assert device.name == "Custom Module"
    assert len(device.pins) == 3
    assert device.width == 60
    assert device.height == 30
    assert device.color == "#FF0000"


def test_load_with_show_legend_false():
    """Test loading with legend disabled."""
    config = {
        "title": "Test",
        "board": "rpi",
        "devices": [],
        "connections": [],
        "show_legend": False,
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert diagram.show_legend is False


@pytest.mark.parametrize(
    "board_name",
    ["raspberry_pi_5", "raspberry_pi", "rpi5", "rpi", "RPI5", "RPi"],
)
def test_load_board_by_name(board_name):
    """Test loading boards by various name aliases."""
    config = {
        "title": "Test",
        "board": board_name,
        "devices": [],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert diagram.board is not None
    assert diagram.board.name == "Raspberry Pi 5"


@pytest.mark.parametrize(
    "board_name",
    ["raspberry_pi_4", "rpi4", "pi4", "RPI4", "PI4"],
)
def test_load_raspberry_pi_4_by_name(board_name):
    """Test loading Raspberry Pi 4 board by various name aliases."""
    config = {
        "title": "Test",
        "board": board_name,
        "devices": [],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert diagram.board is not None
    assert diagram.board.name == "Raspberry Pi 4 Model B"


def test_load_unknown_board():
    """Test loading an unknown board raises error."""
    config = {
        "title": "Test",
        "board": "unknown_board",
        "devices": [],
        "connections": [],
    }
    loader = ConfigLoader()
    with pytest.raises(ValueError, match="Invalid board name"):
        loader.load_from_dict(config)


def test_load_led_with_color():
    """Test loading LED with color parameter."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "led", "color": "Blue"}],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert len(diagram.devices) == 1
    # Device should be created successfully


def test_load_button_with_pull_up():
    """Test loading button with pull_up parameter."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "button", "pull_up": False}],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert len(diagram.devices) == 1


def test_load_ir_led_ring_with_num_leds():
    """Test loading IR LED ring with num_leds parameter."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "ir_led_ring", "num_leds": 16}],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert len(diagram.devices) == 1


def test_load_generic_i2c_device():
    """Test loading generic I2C device."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "i2c_device", "name": "My I2C Module"}],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert len(diagram.devices) == 1
    assert diagram.devices[0].name == "My I2C Module"


def test_load_unknown_device_type():
    """Test loading an unknown device type raises error."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "unknown_device"}],
        "connections": [],
    }
    loader = ConfigLoader()
    with pytest.raises(ValueError, match="Invalid device type"):
        loader.load_from_dict(config)


def test_load_basic_connection():
    """Test loading a basic connection."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "led", "name": "LED1"}],
        "connections": [{"board_pin": 1, "device": "LED1", "device_pin": "Anode"}],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert len(diagram.connections) == 1
    conn = diagram.connections[0]
    assert conn.board_pin == 1
    assert conn.device_name == "LED1"
    assert conn.device_pin_name == "Anode"


def test_load_connection_with_color():
    """Test loading a connection with custom color."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "led", "name": "LED1"}],
        "connections": [
            {
                "board_pin": 1,
                "device": "LED1",
                "device_pin": "Anode",
                "color": "#FF0000",
            }
        ],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    conn = diagram.connections[0]
    assert conn.color == "#FF0000"


def test_load_connection_with_style():
    """Test loading a connection with wire style."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "led", "name": "LED1"}],
        "connections": [
            {
                "board_pin": 1,
                "device": "LED1",
                "device_pin": "Anode",
                "style": "curved",
            }
        ],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    conn = diagram.connections[0]
    assert conn.style == WireStyle.CURVED


def test_load_connection_with_net_name():
    """Test loading a connection with net name."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "led", "name": "LED1"}],
        "connections": [
            {
                "board_pin": 1,
                "device": "LED1",
                "device_pin": "Anode",
                "net": "VCC",
            }
        ],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    conn = diagram.connections[0]
    assert conn.net_name == "VCC"


def test_load_connection_with_component():
    """Test loading a connection with inline component."""
    config = {
        "title": "Test",
        "board": "rpi5",
        "devices": [{"type": "led", "name": "LED1"}],
        "connections": [
            {
                "board_pin": 7,
                "device": "LED1",
                "device_pin": "Anode",
                "components": [{"type": "resistor", "value": "220Ω", "position": 0.6}],
            }
        ],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    conn = diagram.connections[0]
    assert len(conn.components) == 1
    assert conn.components[0].type == ComponentType.RESISTOR
    assert conn.components[0].value == "220Ω"
    assert conn.components[0].position == 0.6


def test_load_diagram_function(sample_yaml_config):
    """Test the load_diagram convenience function."""
    diagram = load_diagram(sample_yaml_config)
    assert diagram is not None
    assert diagram.title == "Test Configuration"
