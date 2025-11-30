"""Input/Output device templates."""

from ..model import Device, DevicePin, PinRole, Point
from .registry import get_registry


def button_switch(pull_up: bool = True) -> Device:
    """
    Push button or switch.

    Args:
        pull_up: True for pull-up configuration, False for pull-down

    Pinout:
    - SIG: Signal to GPIO
    - GND or VCC: Ground (pull-up) or VCC (pull-down)
    """
    pin_spacing = 12.0
    pin_x = 5.0

    if pull_up:
        pins = [
            DevicePin("SIG", PinRole.GPIO, Point(pin_x, 15)),
            DevicePin("GND", PinRole.GROUND, Point(pin_x, 15 + pin_spacing)),
        ]
    else:
        pins = [
            DevicePin("SIG", PinRole.GPIO, Point(pin_x, 15)),
            DevicePin("VCC", PinRole.POWER_3V3, Point(pin_x, 15 + pin_spacing)),
        ]

    config = "Pull-up" if pull_up else "Pull-down"

    return Device(
        name=f"Button ({config})",
        pins=pins,
        width=60.0,
        height=40.0,
        color="#95A5A6",
    )


# Register I/O devices
def _register_io():
    """Register all I/O devices with the global registry."""
    registry = get_registry()

    registry.register(
        type_id="button",
        name="Push Button",
        description="Push button or switch with pull-up/pull-down configuration",
        category="io",
        factory=button_switch,
        parameters={"pull_up": True},
        url="https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header",
    )


_register_io()
