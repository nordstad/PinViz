"""Device templates and registry for pinviz.

All devices are now loaded from JSON configurations in device_configs/.
Use the registry to create device instances:

    from pinviz.devices import get_registry

    registry = get_registry()
    sensor = registry.create('bh1750')
    led = registry.create('led', color_name='Blue')
    display = registry.create('ssd1306')

Available devices are automatically discovered from JSON configs.
"""

from .registry import DeviceRegistry, DeviceTemplate, get_registry

__all__ = [
    "DeviceRegistry",
    "DeviceTemplate",
    "get_registry",
]
