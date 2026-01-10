"""Tests for device configuration loader."""

import pytest

from pinviz.devices import get_registry
from pinviz.devices.loader import load_device_from_config
from pinviz.model import PinRole


def test_load_bh1750_from_config():
    """Test loading BH1750 sensor from JSON configuration."""
    device = load_device_from_config("bh1750")

    assert device is not None
    assert device.name == "BH1750 Light Sensor"
    assert device.type_id == "bh1750"
    assert device.description == "BH1750 I2C ambient light sensor"
    assert device.url == "https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf"
    assert device.category == "sensors"
    assert device.i2c_address == 0x23
    assert len(device.pins) == 5
    # Dimensions and color use smart defaults now (no need to specify in config)
    assert device.width == 80.0  # Default width
    assert device.height == 60.0  # Auto-calculated based on 5 pins
    assert device.color == "#50E3C2"  # Sensors category color


def test_load_bh1750_pins():
    """Test that BH1750 pins are correctly configured."""
    device = load_device_from_config("bh1750")

    # Check pin names
    pin_names = [pin.name for pin in device.pins]
    assert pin_names == ["VCC", "GND", "SCL", "SDA", "ADDR"]

    # Check pin roles
    vcc_pin = device.get_pin_by_name("VCC")
    assert vcc_pin.role == PinRole.POWER_3V3

    scl_pin = device.get_pin_by_name("SCL")
    assert scl_pin.role == PinRole.I2C_SCL

    sda_pin = device.get_pin_by_name("SDA")
    assert sda_pin.role == PinRole.I2C_SDA


def test_load_led_from_config_default():
    """Test loading simple LED with default parameters."""
    device = load_device_from_config("led")

    assert device is not None
    assert device.name == "Red LED"  # Default color
    assert device.type_id == "led"
    assert device.category == "leds"
    assert len(device.pins) == 2


def test_load_led_from_config_custom_color():
    """Test loading simple LED with custom color parameter."""
    device = load_device_from_config("led", color_name="Blue")

    assert device is not None
    assert device.name == "Blue LED"
    assert len(device.pins) == 2


def test_load_nonexistent_device():
    """Test that loading non-existent device raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_device_from_config("nonexistent_device")


def test_registry_loads_json_device():
    """Test that registry can load devices from JSON configs."""
    registry = get_registry()

    # All devices now loaded from JSON configs only
    device = registry.create("bh1750")

    assert device is not None
    # Name comes from JSON config
    assert device.name == "BH1750 Light Sensor"
    assert device.description is not None
    assert device.url is not None


def test_registry_loads_python_device_with_metadata():
    """Test that registry loads devices with full metadata from JSON."""
    registry = get_registry()

    # DS18B20 is loaded from JSON config
    device = registry.create("ds18b20")

    assert device is not None
    assert device.name == "DS18B20 Temperature Sensor"
    # Metadata should be enriched from registry
    assert device.type_id == "ds18b20"
    assert device.description is not None
    assert device.url is not None
    assert device.category == "sensors"


def test_registry_fallback_to_json():
    """Test that registry loads parameterized devices from JSON."""
    registry = get_registry()

    # LED loaded from JSON with parameter substitution
    device = registry.create("led", color_name="Green")

    assert device is not None
    assert device.name == "Green LED"


def test_device_metadata_preserved():
    """Test that device metadata is preserved through registry."""
    registry = get_registry()

    device = registry.create("bh1750")

    # All metadata should be present
    assert device.type_id is not None
    assert device.description is not None
    assert device.url is not None
    assert device.category is not None
    assert device.i2c_address is not None
