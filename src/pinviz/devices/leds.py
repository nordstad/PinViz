"""LED device templates."""

from ..model import Device, DevicePin, PinRole, Point
from .registry import get_registry


def simple_led(color_name: str = "Red") -> Device:
    """
    Simple LED module.

    Pinout:
    - +: Anode (positive terminal, connects to GPIO)
    - -: Cathode (negative terminal, connects to GND)

    Note: Use inline resistor components in connections to add current-limiting
    resistors. Typical values: 220Ω-330Ω for 3.3V, 470Ω-1kΩ for 5V.

    Args:
        color_name: LED color for display
    """
    pin_spacing = 12.0
    pin_x = 5.0

    pins = [
        DevicePin("+", PinRole.GPIO, Point(pin_x, 15)),
        DevicePin("-", PinRole.GROUND, Point(pin_x, 15 + pin_spacing)),
    ]

    return Device(
        name=f"{color_name} LED",
        pins=pins,
        width=50.0,
        height=40.0,
        color="#E74C3C",
    )


def ir_led_ring(num_leds: int = 12) -> Device:
    """
    IR LED ring module with control pin.

    Pinout:
    - VCC: 5V power
    - GND: Ground
    - CTRL: Control signal (GPIO)

    Args:
        num_leds: Number of LEDs in the ring (for display purposes)
    """
    pin_spacing = 10.0
    pin_x = 5.0

    pins = [
        DevicePin("VCC", PinRole.POWER_5V, Point(pin_x, 15)),
        DevicePin("CTRL", PinRole.GPIO, Point(pin_x, 15 + pin_spacing)),
        DevicePin("GND", PinRole.GROUND, Point(pin_x, 15 + pin_spacing * 2)),
    ]

    return Device(
        name=f"IR LED Ring ({num_leds})",
        pins=pins,
        width=80.0,
        height=50.0,
        color="#E24A4A",
    )


# Register LED devices
def _register_leds():
    """Register all LED devices with the global registry."""
    registry = get_registry()

    registry.register(
        type_id="led",
        name="Simple LED",
        description="Simple LED with anode/cathode pins",
        category="leds",
        factory=simple_led,
        parameters={"color_name": "Red"},
        url="https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header",
    )

    registry.register(
        type_id="ir_led_ring",
        name="IR LED Ring",
        description="IR LED ring module with control pin",
        category="leds",
        factory=ir_led_ring,
        parameters={"num_leds": 12},
        url="https://www.electrokit.com/led-ring-for-raspberry-pi-kamera-ir-leds",
    )


_register_leds()
