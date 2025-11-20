# API Reference

This section provides detailed documentation for all PinViz modules and classes.

## Core Modules

### [Model](model.md)
Core data structures and types:

- `Board`, `Device`, `HeaderPin`, `DevicePin` - Component definitions
- `Connection`, `Diagram` - Diagram structure
- `PinRole`, `WireStyle`, `WireColor` - Enums and constants
- `Component`, `ComponentType` - Inline component support

### [Boards](boards.md)
Predefined board templates:

- `raspberry_pi_5()` - Raspberry Pi 5 board factory
- Board pin configuration and layout

### [Devices](devices.md)
Device templates and registry:

- `bh1750_light_sensor()` - BH1750 I2C light sensor
- `ir_led_ring()` - IR LED ring module
- `simple_led()`, `button_switch()` - Basic components
- `generic_i2c_device()`, `generic_spi_device()` - Generic templates
- `DeviceRegistry` - Device template management

### [Config Loader](config_loader.md)
YAML/JSON configuration parsing:

- `ConfigLoader` - Parse configuration files into diagram objects
- `load_diagram()` - Convenience function

### [Layout](layout.md)
Diagram layout engine:

- `LayoutEngine` - Position devices and route wires
- `LayoutConfig` - Layout configuration options
- `RoutedWire` - Wire routing information

### [Rendering](render_svg.md)
SVG rendering:

- `SVGRenderer` - Convert diagrams to SVG files
- `RenderConfig` - Rendering configuration options

### [CLI](cli.md)
Command-line interface:

- `main()` - CLI entry point
- Command implementations

## Quick Links

- [GitHub Repository](https://github.com/nordstad/PinViz)
- [Issue Tracker](https://github.com/nordstad/PinViz/issues)
- [PyPI Package](https://pypi.org/project/pinviz/)

## Usage Examples

### Creating a Simple Diagram

```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

board = boards.raspberry_pi_5()
led = devices.simple_led("Red LED", color="#FF0000")

connections = [
    Connection(11, "Red LED", "+", color="#FF0000"),
    Connection(9, "Red LED", "-", color="#000000"),
]

diagram = Diagram(
    title="Simple LED",
    board=board,
    devices=[led],
    connections=connections
)

renderer = SVGRenderer()
renderer.render(diagram, "led.svg")
```

### Custom Device

```python
from pinviz import Device, DevicePin, PinRole

custom_device = Device(
    name="Custom Sensor",
    width=80.0,
    height=50.0,
    color="#4A90E2",
    pins=[
        DevicePin("VCC", PinRole.V3_3, position=(5.0, 10.0)),
        DevicePin("GND", PinRole.GND, position=(5.0, 20.0)),
        DevicePin("DATA", PinRole.GPIO, position=(5.0, 30.0)),
    ]
)
```
