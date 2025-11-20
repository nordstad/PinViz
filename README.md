# PinViz

[![CI](https://github.com/nordstad/PinViz/actions/workflows/ci.yml/badge.svg)](https://github.com/nordstad/PinViz/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://nordstad.github.io/PinViz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/pinviz.svg)](https://pypi.org/project/pinviz/)

Programmatically generate beautiful Raspberry Pi GPIO connection diagrams in
SVG format.

PinViz makes it easy to create clear, professional wiring diagrams for
your Raspberry Pi projects. Define your connections using simple YAML/JSON
files or Python code, and automatically generate publication-ready SVG
diagrams.

## Features

- **Declarative Configuration**: Define diagrams using YAML or JSON
- **Programmatic API**: Create diagrams with Python code
- **Automatic Wire Routing**: Smart wire routing with configurable styles
  (orthogonal, curved, mixed)
- **Inline Components**: Add resistors, capacitors, and diodes directly on wires
- **Color-Coded Wires**: Automatic color assignment based on pin function
  (I2C, SPI, power, ground, etc.)
- **Built-in Templates**: Pre-configured boards (Raspberry Pi 5) and common
  devices (BH1750, IR LED rings, etc.)
- **GPIO Pin Reference**: Optional GPIO pinout diagram for easy reference
- **SVG Output**: Scalable, high-quality vector graphics

## Installation

Using `uv` (recommended):

```bash
uv add pinviz
```

Using `pip`:

```bash
pip install pinviz
```

## Quick Start

### Using YAML Configuration

Create a configuration file `my-diagram.yaml`:

```yaml
title: "BH1750 Light Sensor Wiring"
board: "raspberry_pi_5"

devices:
  - type: "bh1750"
    name: "BH1750"

connections:
  - board_pin: 1     # 3V3
    device: "BH1750"
    device_pin: "VCC"

  - board_pin: 6     # GND
    device: "BH1750"
    device_pin: "GND"

  - board_pin: 5     # GPIO3 (I2C SCL)
    device: "BH1750"
    device_pin: "SCL"

  - board_pin: 3     # GPIO2 (I2C SDA)
    device: "BH1750"
    device_pin: "SDA"

show_gpio_diagram: true  # Optional: include GPIO pin reference
```

Generate the diagram:

```bash
pinviz my-diagram.yaml -o output.svg
```

### Using Python API

```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

# Create board and device
board = boards.raspberry_pi_5()
sensor = devices.bh1750_light_sensor()

# Define connections
connections = [
    Connection(1, "BH1750", "VCC"),  # 3V3 to VCC
    Connection(6, "BH1750", "GND"),  # GND to GND
    Connection(5, "BH1750", "SCL"),  # GPIO3/SCL to SCL
    Connection(3, "BH1750", "SDA"),  # GPIO2/SDA to SDA
]

# Create and render diagram
diagram = Diagram(
    title="BH1750 Light Sensor Wiring",
    board=board,
    devices=[sensor],
    connections=connections,
    show_gpio_diagram=True  # Optional: include GPIO pin reference
)

renderer = SVGRenderer()
renderer.render(diagram, "output.svg")
```

### Custom Wire Colors

Use the `WireColor` enum for standard electronics wire colors:

```python
from pinviz import (
    boards, devices, Connection, Diagram, SVGRenderer, WireColor
)

# Define connections with custom colors
connections = [
    Connection(1, "BH1750", "VCC", color=WireColor.RED),
    Connection(6, "BH1750", "GND", color=WireColor.BLACK),
    Connection(5, "BH1750", "SCL", color=WireColor.BLUE),
    Connection(3, "BH1750", "SDA", color=WireColor.GREEN),
]

# Or use hex colors directly
connections = [
    Connection(1, "BH1750", "VCC", color="#FF0000"),  # Red
]
```

**Available colors**: RED, BLACK, WHITE, GREEN, BLUE, YELLOW, ORANGE, PURPLE,
GRAY, BROWN, PINK, CYAN, MAGENTA, LIME, TURQUOISE

## CLI Commands

### Render a Diagram

```bash
# From YAML/JSON file
pinviz my-diagram.yaml -o output.svg

# Short form (output defaults to <config>.svg)
pinviz my-diagram.yaml
```

## Example Diagrams

### LED with Resistor

Simple LED circuit with inline current-limiting resistor:

![LED with Resistor](https://raw.githubusercontent.com/nordstad/PinViz/main/images/led_with_resistor.svg)

### Multi-Device Setup

BH1750 light sensor + IR LED ring with custom wire colors:

![BH1750 + IR LED Ring](https://raw.githubusercontent.com/nordstad/PinViz/main/images/bh1750_ir_led.svg)

### Traffic Light

Three LEDs with individual resistors:

![Traffic Light](https://raw.githubusercontent.com/nordstad/PinViz/main/images/traffic_light.svg)

### Generate Built-in Examples

```bash
# BH1750 light sensor
pinviz example bh1750 -o bh1750.svg

# IR LED ring
pinviz example ir_led -o ir_led.svg

# Multiple I2C and SPI devices
pinviz example i2c_spi -o i2c_spi.svg
```

### List Available Templates

```bash
pinviz list
```

## Configuration Reference

### Diagram Options

```yaml
show_gpio_diagram: true  # Include GPIO pin reference (default: false)
```

The GPIO pin reference diagram displays all 40 GPIO pins with their functions,
providing a helpful reference when wiring your project.

### Board Selection

Currently supported boards:

- `raspberry_pi_5` (aliases: `rpi5`, `rpi`)

### Built-in Device Types

- `bh1750` - BH1750 I2C light sensor
- `ir_led_ring` - IR LED ring module
- `i2c_device` - Generic I2C device
- `spi_device` - Generic SPI device
- `led` - Simple LED
- `button` - Push button/switch

### Connection Configuration

Connections use **physical pin numbers** (1-40), not BCM GPIO numbers:

```yaml
connections:
  - board_pin: 1           # Physical pin number (required)
    device: "Device Name"  # Device name (required)
    device_pin: "VCC"      # Device pin name (required)
    color: "#FF0000"       # Custom wire color (optional)
    style: "mixed"         # Wire style: orthogonal, curved, mixed (optional)
    components:            # Inline components (optional)
      - type: "resistor"
        value: "220Ω"
        position: 0.55     # Position along wire (0.0-1.0, default: 0.55)
```

### Inline Components

Add resistors, capacitors, or diodes directly on wire connections:

```yaml
connections:
  - board_pin: 11
    device: "Red LED"
    device_pin: "+"
    color: "#FF0000"
    components:
      - type: "resistor"   # Component type: resistor, capacitor, diode
        value: "220Ω"      # Display value (required)
        position: 0.55     # Position along wire path (0.0 = board, 1.0 = device)
```

Python API:

```python
from pinviz import Component, ComponentType, Connection

connection = Connection(
    board_pin=11,
    device_name="Red LED",
    device_pin_name="+",
    color="#FF0000",
    components=[
        Component(
            type=ComponentType.RESISTOR,
            value="220Ω",
            position=0.55
        )
    ]
)
```

### Custom Devices

Define custom devices inline:

```yaml
devices:
  - name: "My Custom Sensor"
    width: 80.0
    height: 50.0
    color: "#4A90E2"
    pins:
      - name: "VCC"
        role: "3V3"
        position: {x: 5.0, y: 10.0}
      - name: "GND"
        role: "GND"
        position: {x: 5.0, y: 20.0}
      - name: "SDA"
        role: "I2C_SDA"
        position: {x: 5.0, y: 30.0}
      - name: "SCL"
        role: "I2C_SCL"
        position: {x: 5.0, y: 40.0}
```

### Pin Roles

Supported pin roles (for automatic color assignment):

- `3V3`, `5V` - Power rails
- `GND` - Ground
- `GPIO` - General purpose I/O
- `I2C_SDA`, `I2C_SCL` - I2C bus
- `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1` - SPI bus
- `UART_TX`, `UART_RX` - UART serial
- `PWM` - PWM output

## Development

### Setup

```bash
# Clone repository
git clone https://gitlab.com/borkempire/pinviz.git
cd pinviz

# Install dependencies
uv sync --dev
```

### Code Quality

```bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Run tests
uv run pytest
```

## Examples

The `examples/` directory contains:

- `bh1750.yaml` / `bh1750_python.py` - I2C light sensor
- `bh1750_ir_led.yaml` / `bh1750_ir_led_python.py` - Light sensor + IR LED ring
- `led_with_resistor.yaml` / `led_with_resistor_python.py` - LED with inline
  resistor
- `traffic_light.yaml` - Traffic light with 3 LEDs and resistors

All generated diagrams are in the `images/` directory.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

Board and GPIO pin SVG assets courtesy of [FreeSVG.org](https://freesvg.org/)

## Author

Even Nordstad
