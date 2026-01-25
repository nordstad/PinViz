"""Tests for device creation using JSON-based registry."""

from urllib.parse import urlparse

import pytest

from pinviz.devices import get_registry
from pinviz.model import PinRole


def test_bh1750_creation():
    """Test creating a BH1750 device."""
    registry = get_registry()
    device = registry.create("bh1750")
    assert device is not None
    assert "BH1750" in device.name


def test_bh1750_has_correct_pins():
    """Test that BH1750 has the expected pins."""
    registry = get_registry()
    device = registry.create("bh1750")
    pin_names = [pin.name for pin in device.pins]
    assert "VCC" in pin_names
    assert "GND" in pin_names
    assert "SCL" in pin_names
    assert "SDA" in pin_names
    assert "ADDR" in pin_names


def test_bh1750_pin_roles():
    """Test BH1750 pin roles."""
    registry = get_registry()
    device = registry.create("bh1750")
    vcc = device.get_pin_by_name("VCC")
    assert vcc.role == PinRole.POWER_3V3

    gnd = device.get_pin_by_name("GND")
    assert gnd.role == PinRole.GROUND

    scl = device.get_pin_by_name("SCL")
    assert scl.role == PinRole.I2C_SCL

    sda = device.get_pin_by_name("SDA")
    assert sda.role == PinRole.I2C_SDA


def test_bh1750_dimensions():
    """Test BH1750 device dimensions."""
    registry = get_registry()
    device = registry.create("bh1750")
    assert device.width > 0
    assert device.height > 0


def test_ds18b20_creation():
    """Test creating a DS18B20 device."""
    registry = get_registry()
    device = registry.create("ds18b20")
    assert device is not None
    assert "DS18B20" in device.name


def test_ds18b20_has_correct_pins():
    """Test that DS18B20 has the expected pins."""
    registry = get_registry()
    device = registry.create("ds18b20")
    pin_names = [pin.name for pin in device.pins]
    assert "VCC" in pin_names
    assert "GND" in pin_names
    assert "DATA" in pin_names


def test_ds18b20_pin_roles():
    """Test DS18B20 pin roles."""
    registry = get_registry()
    device = registry.create("ds18b20")
    vcc = device.get_pin_by_name("VCC")
    assert vcc.role == PinRole.POWER_3V3

    gnd = device.get_pin_by_name("GND")
    assert gnd.role == PinRole.GROUND

    data = device.get_pin_by_name("DATA")
    assert data.role == PinRole.GPIO


def test_simple_led_creation():
    """Test creating a simple LED device."""
    registry = get_registry()
    device = registry.create("led")
    assert device is not None
    assert "LED" in device.name


def test_simple_led_has_correct_pins():
    """Test that LED has the expected pins."""
    registry = get_registry()
    device = registry.create("led")
    pin_names = [pin.name for pin in device.pins]
    assert "+" in pin_names
    assert "-" in pin_names


def test_simple_led_pin_roles():
    """Test LED pin roles."""
    registry = get_registry()
    device = registry.create("led")
    anode = device.get_pin_by_name("+")
    assert anode.role == PinRole.GPIO

    cathode = device.get_pin_by_name("-")
    assert cathode.role == PinRole.GROUND


def test_ir_led_ring_creation():
    """Test creating an IR LED ring device."""
    registry = get_registry()
    device = registry.create("ir_led_ring")
    assert device is not None
    assert "IR LED Ring" in device.name


def test_ir_led_ring_has_correct_pins():
    """Test that IR LED ring has the expected pins."""
    registry = get_registry()
    device = registry.create("ir_led_ring")
    pin_names = [pin.name for pin in device.pins]
    assert "VCC" in pin_names
    assert "GND" in pin_names
    assert "EN" in pin_names


def test_button_creation():
    """Test creating a button device."""
    registry = get_registry()
    device = registry.create("button")
    assert device is not None
    assert "Button" in device.name


def test_button_has_correct_pins():
    """Test that button has the expected pins."""
    registry = get_registry()
    device = registry.create("button")
    pin_names = [pin.name for pin in device.pins]
    assert "SIG" in pin_names
    assert "GND" in pin_names


def test_button_pin_roles():
    """Test button pin roles."""
    registry = get_registry()
    device = registry.create("button")
    sig = device.get_pin_by_name("SIG")
    assert sig.role == PinRole.GPIO

    gnd = device.get_pin_by_name("GND")
    assert gnd.role == PinRole.GROUND


def test_generic_i2c_creation():
    """Test creating a generic I2C device."""
    registry = get_registry()
    device = registry.create("i2c_device", name="Test I2C")
    assert device is not None
    assert device.name == "Test I2C"


def test_generic_i2c_has_correct_pins():
    """Test that generic I2C has the expected pins."""
    registry = get_registry()
    device = registry.create("i2c_device", name="Test I2C")
    pin_names = [pin.name for pin in device.pins]
    assert "VCC" in pin_names
    assert "GND" in pin_names
    assert "SDA" in pin_names
    assert "SCL" in pin_names


def test_generic_i2c_pin_roles():
    """Test generic I2C pin roles."""
    registry = get_registry()
    device = registry.create("i2c_device", name="Test I2C")
    sda = device.get_pin_by_name("SDA")
    assert sda.role == PinRole.I2C_SDA

    scl = device.get_pin_by_name("SCL")
    assert scl.role == PinRole.I2C_SCL


def test_generic_spi_creation():
    """Test creating a generic SPI device."""
    registry = get_registry()
    device = registry.create("spi_device", name="Test SPI")
    assert device is not None
    assert device.name == "Test SPI"


def test_generic_spi_has_correct_pins():
    """Test that generic SPI has the expected pins."""
    registry = get_registry()
    device = registry.create("spi_device", name="Test SPI")
    pin_names = [pin.name for pin in device.pins]
    assert "VCC" in pin_names
    assert "GND" in pin_names
    assert "MOSI" in pin_names
    assert "MISO" in pin_names
    assert "SCLK" in pin_names
    assert "CS" in pin_names


def test_generic_spi_pin_roles():
    """Test generic SPI pin roles."""
    registry = get_registry()
    device = registry.create("spi_device", name="Test SPI")
    mosi = device.get_pin_by_name("MOSI")
    assert mosi.role == PinRole.SPI_MOSI

    miso = device.get_pin_by_name("MISO")
    assert miso.role == PinRole.SPI_MISO

    sclk = device.get_pin_by_name("SCLK")
    assert sclk.role == PinRole.SPI_SCLK

    cs = device.get_pin_by_name("CS")
    assert cs.role == PinRole.SPI_CE0


def test_registry_exists():
    """Test that the device registry exists."""
    registry = get_registry()
    assert registry is not None


def test_registry_get_template():
    """Test getting a device template from the registry."""
    registry = get_registry()
    template = registry.get("bh1750")
    assert template is not None
    assert template.name == "BH1750 Light Sensor"


def test_registry_get_nonexistent_device():
    """Test getting a non-existent device from the registry."""
    registry = get_registry()
    template = registry.get("nonexistent_device")
    assert template is None


def test_registry_create_device():
    """Test creating a device from the registry."""
    registry = get_registry()
    device = registry.create("led", color_name="Blue")
    assert device is not None
    assert "LED" in device.name


@pytest.mark.parametrize(
    "device_id,device_args",
    [
        ("bh1750", {}),
        ("ds18b20", {}),
        ("led", {"color_name": "Red"}),
        ("ir_led_ring", {}),
        ("button", {}),
        ("i2c_device", {"name": "Test I2C"}),
        ("spi_device", {"name": "Test SPI"}),
    ],
)
def test_device_pins_have_positions(device_id, device_args):
    """Test that all device pins have position information."""
    registry = get_registry()
    device = registry.create(device_id, **device_args)
    for pin in device.pins:
        assert pin.position is not None
        assert hasattr(pin.position, "x")
        assert hasattr(pin.position, "y")


def test_registry_template_has_url_field():
    """Test that device templates include URL field."""
    registry = get_registry()
    template = registry.get("bh1750")
    assert hasattr(template, "url")


def test_registry_template_url_for_bh1750():
    """Test that BH1750 template has correct URL."""
    registry = get_registry()
    template = registry.get("bh1750")
    assert template.url is not None
    parsed = urlparse(template.url)
    assert parsed.netloc == "www.mouser.com" or "datasheet" in parsed.path.lower()


def test_registry_template_url_for_ds18b20():
    """Test that DS18B20 template has correct URL."""
    registry = get_registry()
    template = registry.get("ds18b20")
    assert template.url is not None
    parsed = urlparse(template.url)
    assert parsed.netloc == "www.analog.com" or "DS18B20" in parsed.path


def test_registry_template_url_for_ir_led_ring():
    """Test that IR LED ring template has correct URL."""
    registry = get_registry()
    template = registry.get("ir_led_ring")
    assert template.url is not None
    parsed = urlparse(template.url)
    assert parsed.netloc == "www.electrokit.com"


def test_registry_template_url_for_generic_devices():
    """Test that generic device templates have URLs."""
    registry = get_registry()

    i2c_template = registry.get("i2c_device")
    assert i2c_template.url is not None
    parsed_i2c = urlparse(i2c_template.url)
    assert parsed_i2c.netloc == "www.raspberrypi.com"

    spi_template = registry.get("spi_device")
    assert spi_template.url is not None
    parsed_spi = urlparse(spi_template.url)
    assert parsed_spi.netloc == "www.raspberrypi.com"


def test_registry_all_devices_have_urls():
    """Test that all registered devices have documentation URLs."""
    registry = get_registry()
    all_templates = registry.list_all()

    for template in all_templates:
        assert template.url is not None, f"Device {template.type_id} missing URL"
        assert len(template.url) > 0, f"Device {template.type_id} has empty URL"
        assert template.url.startswith("http"), (
            f"Device {template.type_id} URL should start with http"
        )
