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

For more examples, see the [Quick Start Guide](../getting-started/quickstart.md).
