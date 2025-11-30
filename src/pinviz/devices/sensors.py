"""Sensor device templates."""

from ..model import Device, DevicePin, PinRole, Point
from .registry import get_registry


def bh1750_light_sensor() -> Device:
    """
    BH1750 I2C ambient light sensor.

    Pinout (top to bottom):
    - VCC: 3.3V power
    - GND: Ground
    - SCL: I2C clock
    - SDA: I2C data
    - ADDR: I2C address select (optional)
    """
    pin_spacing = 8.0
    pin_x = 5.0  # Pins on left side of device

    pins = [
        DevicePin("VCC", PinRole.POWER_3V3, Point(pin_x, 10)),
        DevicePin("GND", PinRole.GROUND, Point(pin_x, 10 + pin_spacing)),
        DevicePin("SCL", PinRole.I2C_SCL, Point(pin_x, 10 + pin_spacing * 2)),
        DevicePin("SDA", PinRole.I2C_SDA, Point(pin_x, 10 + pin_spacing * 3)),
        DevicePin("ADDR", PinRole.GPIO, Point(pin_x, 10 + pin_spacing * 4)),
    ]

    return Device(
        name="BH1750",
        pins=pins,
        width=70.0,
        height=60.0,
        color="#4A90E2",
    )


def ds18b20_temp_sensor() -> Device:
    """
    DS18B20 waterproof digital temperature sensor (1-Wire protocol).

    Pinout (typical wire colors):
    - VCC: 3.3V power (red wire)
    - GND: Ground (black wire)
    - DATA: 1-Wire data line (yellow/white wire)

    Note: Requires a 4.7kΩ pull-up resistor between DATA and VCC.
    Use inline resistor components in connections to add the pull-up resistor.

    The DATA pin connects to any available GPIO pin on the Raspberry Pi.
    Enable 1-Wire in raspi-config and load the w1-gpio kernel module.
    """
    pin_spacing = 10.0
    pin_x = 5.0

    pins = [
        DevicePin("VCC", PinRole.POWER_3V3, Point(pin_x, 12)),
        DevicePin("DATA", PinRole.GPIO, Point(pin_x, 12 + pin_spacing)),
        DevicePin("GND", PinRole.GROUND, Point(pin_x, 12 + pin_spacing * 2)),
    ]

    return Device(
        name="DS18B20",
        pins=pins,
        width=75.0,
        height=45.0,
        color="#F39C12",
    )


# Register sensor devices
def _register_sensors():
    """Register all sensor devices with the global registry."""
    registry = get_registry()

    registry.register(
        type_id="bh1750",
        name="BH1750 Light Sensor",
        description="BH1750 I2C ambient light sensor",
        category="sensors",
        factory=bh1750_light_sensor,
        url="https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf",
    )

    registry.register(
        type_id="ds18b20",
        name="DS18B20 Temperature Sensor",
        description="DS18B20 waterproof 1-Wire temperature sensor",
        category="sensors",
        factory=ds18b20_temp_sensor,
        url="https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf",
    )


_register_sensors()
