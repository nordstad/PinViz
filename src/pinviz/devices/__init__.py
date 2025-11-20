"""Device templates and registry for pinviz."""

# Import registry first
# Import all device modules to trigger registration
from . import generic, io, leds, sensors

# Re-export factory functions for backward compatibility
from .generic import generic_i2c_device, generic_spi_device
from .io import button_switch
from .leds import ir_led_ring, simple_led
from .registry import DeviceRegistry, DeviceTemplate, get_registry
from .sensors import bh1750_light_sensor, ds18b20_temp_sensor

__all__ = [
    # Registry classes and functions
    "DeviceRegistry",
    "DeviceTemplate",
    "get_registry",
    # Factory functions
    "bh1750_light_sensor",
    "ds18b20_temp_sensor",
    "simple_led",
    "ir_led_ring",
    "button_switch",
    "generic_i2c_device",
    "generic_spi_device",
    # Module imports (needed for registration side effects)
    "generic",
    "io",
    "leds",
    "sensors",
]
