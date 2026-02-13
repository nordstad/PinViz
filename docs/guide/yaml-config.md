# YAML Configuration

Complete reference for YAML configuration files.

## Basic Structure

```yaml
title: "Diagram Title"
board: "raspberry_pi_5"  # or "raspberry_pi_4"
theme: "light"  # optional: "light" (default) or "dark"
devices:
  - type: "device_type"
    name: "Device Name"
connections:
  - board_pin: 1
    device: "Device Name"
    device_pin: "Pin Name"
show_legend: true
```

## Supported Boards

- `raspberry_pi_5` (aliases: `rpi5`) - Raspberry Pi 5 with 40-pin GPIO header
- `raspberry_pi_4` (aliases: `rpi4`, `pi4`) - Raspberry Pi 4 Model B with 40-pin GPIO header
- `raspberry_pi` (aliases: `rpi`) - Default board (currently Raspberry Pi 5)

## Built-in Device Types

PinViz includes several pre-configured device templates that you can use in your YAML files.

### Sensors

**`bh1750`** - BH1750 I2C ambient light sensor
📖 [Datasheet](https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf)

```yaml
devices:
  - type: "bh1750"
    name: "BH1750"
```

**`ds18b20`** - DS18B20 waterproof 1-Wire temperature sensor
📖 [Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf)

```yaml
devices:
  - type: "ds18b20"
    name: "DS18B20"
```

### LEDs

**`led`** - Simple LED with anode/cathode pins
📖 [Raspberry Pi GPIO Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header)

```yaml
devices:
  - type: "led"
    name: "Red LED"
```

**`ir_led_ring`** - IR LED ring module with control pin
📖 [Product Page](https://www.electrokit.com/led-ring-for-raspberry-pi-kamera-ir-leds)

```yaml
devices:
  - type: "ir_led_ring"
    name: "IR LED Ring"
```

### I/O

**`button`** - Push button or switch with pull-up/pull-down configuration
📖 [Raspberry Pi GPIO Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header)

```yaml
devices:
  - type: "button"
    name: "Button"
```

### Generic

**`i2c_device`** - Generic I2C device with standard pinout
📖 [Raspberry Pi I2C Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#i2c)

```yaml
devices:
  - type: "i2c_device"
    name: "My I2C Device"
```

**`spi_device`** - Generic SPI device with standard pinout
📖 [Raspberry Pi SPI Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#spi)

```yaml
devices:
  - type: "spi_device"
    name: "My SPI Device"
```

### Listing Available Devices

To see all available device types with their documentation links, run:

```bash
pinviz list
```

## Configuration Options

### Top-Level Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | `"GPIO Diagram"` | Diagram title displayed at the top |
| `board` | string | `"raspberry_pi_5"` | Board type (see Supported Boards above) |
| `theme` | string | `"light"` | Theme: `"light"` or `"dark"` |
| `show_legend` | boolean | `false` | Show device specifications table |
| `show_gpio_diagram` | boolean | `false` | Show GPIO pin reference diagram |
| `show_title` | boolean | `true` | Display the diagram title |
| `show_board_name` | boolean | `true` | Display the board name |

### Themes

PinViz supports light and dark themes. See the [Themes Guide](themes.md) for detailed documentation.

```yaml
# Light theme (default)
theme: "light"

# Dark theme
theme: "dark"
```

### Device Colors

Devices can be customized using either named colors or hex codes. This makes it easy to color-code devices without having to look up hex values.

```yaml
devices:
  - name: "Sensor"
    color: "turquoise"  # Named color (case-insensitive)
    pins:
      - name: "VCC"
        role: "3V3"
      - name: "GND"
        role: "GND"

  - name: "LED"
    color: "#E74C3C"  # Hex code (traditional format)
    pins:
      - name: "Anode"
        role: "GPIO"
      - name: "Cathode"
        role: "GND"

  - name: "Button"
    color: "GREEN"  # Case-insensitive
    pins:
      - name: "+"
        role: "GPIO"
      - name: "-"
        role: "GND"
```

**Available named colors:**

| Color | Hex Code | Preview |
|-------|----------|---------|
| `red` | #FF0000 | 🔴 |
| `green` | #00FF00 | 🟢 |
| `blue` | #0000FF | 🔵 |
| `yellow` | #FFFF00 | 🟡 |
| `orange` | #FF8C00 | 🟠 |
| `purple` | #9370DB | 🟣 |
| `black` | #000000 | ⚫ |
| `white` | #FFFFFF | ⚪ |
| `gray` | #808080 | ⚫ |
| `brown` | #8B4513 | 🟤 |
| `pink` | #FF69B4 | 🩷 |
| `cyan` | #00CED1 | 🩵 |
| `magenta` | #FF00FF | 🩷 |
| `lime` | #32CD32 | 🟢 |
| `turquoise` | #40E0D0 | 🩵 |

**Notes:**

- Color names are **case-insensitive**: `"Red"`, `"RED"`, and `"red"` all work
- Invalid colors fall back to default blue (#4A90E2)
- Both formats work in the same config file
- Named colors also work for wire colors in connections

**Connection wire colors:**

```yaml
connections:
  - board_pin: 1
    device: "LED"
    device_pin: "Anode"
    color: "red"  # Named color for wire

  - board_pin: 6
    device: "LED"
    device_pin: "Cathode"
    color: "#000000"  # Hex code for wire
```

**Pin Spacing Standards:**

When defining custom devices with manual pin positions, use **10px vertical spacing** between pins for consistency with registry devices:

```yaml
devices:
  - name: "Custom Device"
    pins:
      - name: "VCC"
        role: "3V3"
        position: {x: 10, y: 10}  # First pin at y: 10
      - name: "GND"
        role: "GND"
        position: {x: 10, y: 20}  # Second pin at y: 20 (10px gap)
      - name: "SDA"
        role: "I2C_SDA"
        position: {x: 10, y: 30}  # Third pin at y: 30 (10px gap)
    width: 80
    height: 50
```

This ensures visual consistency across all diagrams.

For more examples, see the [Quick Start Guide](../getting-started/quickstart.md).

## Inline Components

PinViz supports adding electronic components directly on wires. This is useful for showing resistors, capacitors, and diodes in your circuit diagrams.

### Supported Component Types

**Resistor** - Current-limiting or pull-up/down resistors
```yaml
connections:
  - board_pin: 11  # GPIO17
    device: "LED"
    device_pin: "Anode"
    components:
      - type: "resistor"
        value: "220Ω"
        position: 0.55  # 55% along wire (optional, default: 0.55)
```

**Capacitor** - Decoupling or filtering capacitors
```yaml
connections:
  - board_pin: 1  # 3.3V
    device: "Sensor"
    device_pin: "VCC"
    components:
      - type: "capacitor"
        value: "100µF"
        position: 0.4  # Closer to board for decoupling
```

**Diode** - Flyback protection or rectification diodes
```yaml
connections:
  - board_pin: 2  # 5V
    device: "Relay"
    device_pin: "VCC"
    components:
      - type: "diode"
        value: "1N4148"
        position: 0.5  # Centered on wire
```

### Multiple Components on One Wire

You can add multiple components to a single wire:

```yaml
connections:
  - board_pin: 11
    device: "Motor Driver"
    device_pin: "IN1"
    components:
      - type: "resistor"
        value: "10kΩ"
        position: 0.3
      - type: "capacitor"
        value: "10nF"
        position: 0.7
```

### Component Position

The `position` field specifies where along the wire to place the component:

- `0.0` = At the board pin (start of wire)
- `0.5` = Middle of wire (default for most components)
- `1.0` = At the device pin (end of wire)

**Best practices:**
- **Resistors**: `0.55-0.6` (slightly toward device)
- **Capacitors**: `0.3-0.4` (closer to power source for decoupling)
- **Diodes**: `0.5` (centered, direction matters for polarity)

### Complete Example

```yaml
title: "LED with Current-Limiting Resistor"
board: "raspberry_pi_5"

devices:
  - type: "led"
    name: "Red LED"
    color: "red"

connections:
  # LED anode with current-limiting resistor
  - board_pin: 11  # GPIO17
    device: "Red LED"
    device_pin: "+"
    color: "#FF0000"
    components:
      - type: "resistor"
        value: "220Ω"

  # LED cathode to ground
  - board_pin: 9  # GND
    device: "Red LED"
    device_pin: "-"
    color: "#000000"
```

See the [examples directory](https://github.com/nordstad/PinViz/tree/main/examples) for more component usage examples:
- `led_with_capacitor.yaml` - Decoupling capacitor example
- `relay_with_diode.yaml` - Flyback diode protection
- `all_components.yaml` - All three component types together
