# Quick Start

This guide will walk you through using PinViz, from generating built-in examples to creating your own custom diagrams.

## Step 1: Try a Built-in Example

The fastest way to get started is to generate one of the built-in examples:

```bash
# Generate a BH1750 light sensor wiring diagram
pinviz example bh1750 -o bh1750.svg

# See all available examples
pinviz list
```

This creates an SVG file you can open in any web browser or vector graphics editor.

!!! tip "Using uv add"
    If you installed with `uv add` instead of `uv tool install`, prefix commands with `uv run`:
    ```bash
    uv run pinviz example bh1750 -o bh1750.svg
    ```

### Explore Available Examples

PinViz includes several built-in examples:

```bash
# List all available examples
pinviz list

# BH1750 light sensor
pinviz example bh1750 -o bh1750.svg

# IR LED ring
pinviz example ir_led -o ir_led.svg

# Multiple I2C and SPI devices
pinviz example i2c_spi -o i2c_spi.svg
```

## Step 2: Create Your Own Diagram

Once you've seen what PinViz can do, create your own configuration file `light-sensor.yaml`:

```yaml
title: "BH1750 Light Sensor Wiring"
board: "raspberry_pi_5"

devices:
  - type: "bh1750"
    name: "BH1750"

connections:
  - board_pin: 1     # 3V3 Power
    device: "BH1750"
    device_pin: "VCC"

  - board_pin: 6     # Ground
    device: "BH1750"
    device_pin: "GND"

  - board_pin: 5     # GPIO3 (I2C SCL)
    device: "BH1750"
    device_pin: "SCL"

  - board_pin: 3     # GPIO2 (I2C SDA)
    device: "BH1750"
    device_pin: "SDA"
```

### Generate Your Diagram

Run the following command:

```bash
pinviz render light-sensor.yaml -o light-sensor.svg
```

This creates `light-sensor.svg` in the current directory.

### View Your Diagram

Open the SVG file in your web browser or image viewer. You'll see a professionally formatted wiring diagram with:

- The Raspberry Pi GPIO header
- The BH1750 sensor
- Color-coded wires connecting the pins
- A legend showing what each wire color represents

## Step 3: Using the Python API

For programmatic diagram generation in your Python projects:

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
    connections=connections
)

renderer = SVGRenderer()
renderer.render(diagram, "light-sensor.svg")
```

## Adding Custom Wire Colors

Customize wire colors using the `color` parameter:

```yaml
connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
    color: "#FF0000"  # Red

  - board_pin: 6
    device: "BH1750"
    device_pin: "GND"
    color: "#000000"  # Black
```

Or use the `WireColor` enum in Python:

```python
from pinviz import Connection, WireColor

connections = [
    Connection(1, "BH1750", "VCC", color=WireColor.RED),
    Connection(6, "BH1750", "GND", color=WireColor.BLACK),
]
```

## Adding Inline Components

Add a resistor to an LED connection:

```yaml
connections:
  - board_pin: 11
    device: "Red LED"
    device_pin: "+"
    color: "#FF0000"
    components:
      - type: "resistor"
        value: "220Ω"
```

## Next Steps

- Learn more about [CLI usage](../guide/cli.md)
- Read the [YAML configuration guide](../guide/yaml-config.md)
- Explore the [Python API guide](../guide/python-api.md)
- Check out [more examples](../guide/examples.md)
- Browse the [API reference](../api/index.md)
