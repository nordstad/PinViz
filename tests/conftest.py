"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path

import pytest

from pinviz import boards
from pinviz.devices import (
    bh1750_light_sensor,
    button_switch,
    generic_i2c_device,
    simple_led,
)
from pinviz.model import (
    Board,
    Connection,
    Device,
    DevicePin,
    Diagram,
    HeaderPin,
    PinRole,
)


@pytest.fixture
def sample_board():
    """Create a simple test board."""
    from pinviz.model import Point

    return Board(
        name="Test Board",
        pins=[
            HeaderPin(
                number=1,
                name="3V3",
                role=PinRole.POWER_3V3,
                gpio_bcm=None,
                position=Point(10, 20),
            ),
            HeaderPin(
                number=2,
                name="5V",
                role=PinRole.POWER_5V,
                gpio_bcm=None,
                position=Point(10, 40),
            ),
            HeaderPin(
                number=3,
                name="GPIO2",
                role=PinRole.I2C_SDA,
                gpio_bcm=2,
                position=Point(10, 60),
            ),
            HeaderPin(
                number=5,
                name="GPIO3",
                role=PinRole.I2C_SCL,
                gpio_bcm=3,
                position=Point(10, 80),
            ),
            HeaderPin(
                number=6,
                name="GND",
                role=PinRole.GROUND,
                gpio_bcm=None,
                position=Point(10, 100),
            ),
            HeaderPin(
                number=7,
                name="GPIO4",
                role=PinRole.GPIO,
                gpio_bcm=4,
                position=Point(10, 120),
            ),
        ],
        svg_asset_path="test.svg",
        width=200,
        height=150,
    )


@pytest.fixture
def sample_device():
    """Create a simple test device."""
    from pinviz.model import Point

    return Device(
        name="Test Device",
        pins=[
            DevicePin(name="VCC", role=PinRole.POWER_3V3, position=Point(0, 0)),
            DevicePin(name="GND", role=PinRole.GROUND, position=Point(0, 10)),
            DevicePin(name="SDA", role=PinRole.I2C_SDA, position=Point(0, 20)),
            DevicePin(name="SCL", role=PinRole.I2C_SCL, position=Point(0, 30)),
        ],
        width=60,
        height=40,
        color="#4A90E2",
    )


@pytest.fixture
def sample_connections():
    """Create sample connections."""
    return [
        Connection(board_pin=1, device_name="Test Device", device_pin_name="VCC"),
        Connection(board_pin=6, device_name="Test Device", device_pin_name="GND"),
        Connection(board_pin=3, device_name="Test Device", device_pin_name="SDA"),
        Connection(board_pin=5, device_name="Test Device", device_pin_name="SCL"),
    ]


@pytest.fixture
def sample_diagram(sample_board, sample_device, sample_connections):
    """Create a complete test diagram."""
    return Diagram(
        title="Test Diagram",
        board=sample_board,
        devices=[sample_device],
        connections=sample_connections,
        show_legend=True,
    )


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_yaml_config(temp_output_dir):
    """Create a sample YAML config file."""
    config_content = """title: "Test Configuration"
board: "raspberry_pi_5"
devices:
  - type: "bh1750"
    name: "Light Sensor"
  - type: "led"
    name: "Status LED"
connections:
  - board_pin: 1
    device: "Light Sensor"
    device_pin: "VCC"
  - board_pin: 6
    device: "Light Sensor"
    device_pin: "GND"
  - board_pin: 3
    device: "Light Sensor"
    device_pin: "SDA"
  - board_pin: 5
    device: "Light Sensor"
    device_pin: "SCL"
  - board_pin: 2
    device: "Status LED"
    device_pin: "Anode"
  - board_pin: 9
    device: "Status LED"
    device_pin: "Cathode"
show_legend: true
"""
    config_path = temp_output_dir / "test_config.yaml"
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def rpi5_board():
    """Get the Raspberry Pi 5 board."""
    return boards.raspberry_pi_5()


@pytest.fixture
def bh1750_device():
    """Get the BH1750 light sensor device."""
    return bh1750_light_sensor()


@pytest.fixture
def led_device():
    """Get a simple LED device."""
    return simple_led()


@pytest.fixture
def button_device():
    """Get a button device."""
    return button_switch()


@pytest.fixture
def generic_i2c_device_fixture():
    """Get a generic I2C device."""
    return generic_i2c_device()
