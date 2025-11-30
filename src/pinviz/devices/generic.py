"""Generic device templates for common protocols."""

from ..model import Device, DevicePin, PinRole, Point
from .registry import get_registry


def generic_i2c_device(name: str, has_int_pin: bool = False) -> Device:
    """
    Generic I2C device template.

    Args:
        name: Device display name
        has_int_pin: Whether device has an interrupt pin

    Pinout:
    - VCC: 3.3V power
    - GND: Ground
    - SCL: I2C clock
    - SDA: I2C data
    - INT: Interrupt (optional)
    """
    pin_spacing = 8.0
    pin_x = 5.0

    pins = [
        DevicePin("VCC", PinRole.POWER_3V3, Point(pin_x, 10)),
        DevicePin("GND", PinRole.GROUND, Point(pin_x, 10 + pin_spacing)),
        DevicePin("SCL", PinRole.I2C_SCL, Point(pin_x, 10 + pin_spacing * 2)),
        DevicePin("SDA", PinRole.I2C_SDA, Point(pin_x, 10 + pin_spacing * 3)),
    ]

    if has_int_pin:
        pins.append(DevicePin("INT", PinRole.GPIO, Point(pin_x, 10 + pin_spacing * 4)))

    height = 50.0 if has_int_pin else 42.0

    return Device(
        name=name,
        pins=pins,
        width=75.0,
        height=height,
        color="#9B59B6",
    )


def generic_spi_device(name: str) -> Device:
    """
    Generic SPI device template.

    Pinout:
    - VCC: 3.3V power
    - GND: Ground
    - SCLK: SPI clock
    - MOSI: Master Out Slave In
    - MISO: Master In Slave Out
    - CS: Chip Select
    """
    pin_spacing = 8.0
    pin_x = 5.0

    pins = [
        DevicePin("VCC", PinRole.POWER_3V3, Point(pin_x, 10)),
        DevicePin("GND", PinRole.GROUND, Point(pin_x, 10 + pin_spacing)),
        DevicePin("SCLK", PinRole.SPI_SCLK, Point(pin_x, 10 + pin_spacing * 2)),
        DevicePin("MOSI", PinRole.SPI_MOSI, Point(pin_x, 10 + pin_spacing * 3)),
        DevicePin("MISO", PinRole.SPI_MISO, Point(pin_x, 10 + pin_spacing * 4)),
        DevicePin("CS", PinRole.SPI_CE0, Point(pin_x, 10 + pin_spacing * 5)),
    ]

    return Device(
        name=name,
        pins=pins,
        width=75.0,
        height=60.0,
        color="#3498DB",
    )


# Register generic devices
def _register_generic():
    """Register all generic devices with the global registry."""
    registry = get_registry()

    registry.register(
        type_id="i2c_device",
        name="Generic I2C Device",
        description="Generic I2C device with standard pinout",
        category="generic",
        factory=generic_i2c_device,
        parameters={"name": "I2C Device", "has_int_pin": False},
        url="https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#i2c",
    )

    registry.register(
        type_id="i2c",
        name="Generic I2C Device",
        description="Generic I2C device with standard pinout (alias)",
        category="generic",
        factory=generic_i2c_device,
        parameters={"name": "I2C Device", "has_int_pin": False},
        url="https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#i2c",
    )

    registry.register(
        type_id="spi_device",
        name="Generic SPI Device",
        description="Generic SPI device with standard pinout",
        category="generic",
        factory=generic_spi_device,
        parameters={"name": "SPI Device"},
        url="https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#spi",
    )

    registry.register(
        type_id="spi",
        name="Generic SPI Device",
        description="Generic SPI device with standard pinout (alias)",
        category="generic",
        factory=generic_spi_device,
        parameters={"name": "SPI Device"},
        url="https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#spi",
    )


_register_generic()
