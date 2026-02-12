# Adding a New Device

Device definitions are stored in JSON files in `src/pinviz/device_configs/` directory, organized by category (sensors/, leds/, displays/, io/, etc.).

**68% less configuration** compared to Python factory functions - most fields have smart defaults!

## Device Configuration Structure

### Minimal Example (Recommended)

Smart defaults handle positions, dimensions, and colors:

```json
{
  "id": "bh1750",
  "name": "BH1750 Light Sensor",
  "category": "sensors",
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"},
    {"name": "SCL", "role": "I2C_SCL"},
    {"name": "SDA", "role": "I2C_SDA"}
  ]
}
```

### With Optional Metadata

```json
{
  "id": "ds18b20",
  "name": "DS18B20 Temperature Sensor",
  "category": "sensors",
  "description": "DS18B20 waterproof 1-Wire temperature sensor",
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "DATA", "role": "GPIO"},
    {"name": "GND", "role": "GND"}
  ],
  "layout": {
    "pin_spacing": 10.0,
    "start_y": 12.0
  },
  "display": {
    "width": 75.0,
    "height": 45.0
  },
  "datasheet_url": "https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf",
  "notes": "Requires a 4.7kΩ pull-up resistor between DATA and VCC."
}
```

### With Parameters (Device Variants)

```json
{
  "id": "led",
  "name": "{color_name} LED",
  "category": "leds",
  "pins": [
    {"name": "+", "role": "GPIO"},
    {"name": "-", "role": "GND"}
  ],
  "parameters": {
    "color_name": {
      "type": "string",
      "default": "Red",
      "description": "LED color for display name"
    }
  }
}
```

## Smart Defaults

The device loader automatically provides:

- **Pin positions**: Vertical layout (top to bottom) or horizontal layout (left to right)
- **Device dimensions**: Auto-sized to fit all pins with padding
- **Colors**: Category-based defaults (sensors=turquoise, LEDs=red, displays=blue, io=gray)
- **Wire colors**: Based on pin roles (I2C=yellow, SPI=cyan, power=red, ground=black)

## Device Categories

Available categories with default colors:

- `sensors` - Turquoise (#40E0D0)
- `leds` - Red (#D32F2F)
- `displays` - Blue (#1976D2)
- `io` - Gray (#757575)
- `communication` - Orange (#FF9800)
- `power` - Green (#4CAF50)

## Quick Start Guide

### Step 1: Create JSON File

Create a new JSON file in the appropriate category folder:

```bash
# For a sensor
touch src/pinviz/device_configs/sensors/bme280.json

# For an LED
touch src/pinviz/device_configs/leds/ws2812b.json

# For a display
touch src/pinviz/device_configs/displays/ssd1306.json
```

### Step 2: Define Device

Add the minimal required fields:

```json
{
  "id": "bme280",
  "name": "BME280 Sensor",
  "category": "sensors",
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"},
    {"name": "SCL", "role": "I2C_SCL"},
    {"name": "SDA", "role": "I2C_SDA"}
  ]
}
```

### Step 3: Use the Device

In YAML config:

```yaml
title: "BME280 Example"
board: "rpi5"
devices:
  - type: "bme280"
connections:
  - board_pin: 1
    device: "BME280 Sensor"
    device_pin: "VCC"
  - board_pin: 3
    device: "BME280 Sensor"
    device_pin: "SDA"
  - board_pin: 5
    device: "BME280 Sensor"
    device_pin: "SCL"
  - board_pin: 6
    device: "BME280 Sensor"
    device_pin: "GND"
```

In Python:

```python
from pinviz.devices import get_registry

registry = get_registry()
sensor = registry.create('bme280')
```

## Advanced Features

### Explicit Pin Side Placement

Control which side of the device each pin appears on:

```json
{
  "id": "relay_module",
  "name": "Relay Module",
  "category": "actuators",
  "pins": [
    {"name": "VCC", "role": "5V", "side": "left"},
    {"name": "GND", "role": "GND", "side": "left"},
    {"name": "IN", "role": "GPIO", "side": "left"},
    {"name": "COM", "role": "5V", "side": "right"},
    {"name": "NO", "role": "5V", "side": "right"},
    {"name": "NC", "role": "5V", "side": "right"}
  ]
}
```

The `"side"` field accepts `"left"` or `"right"`. If not specified, pins are automatically placed based on their names (pins with names like "OUT", "TX", "COM", "NO", "NC" go on the right; others go on the left).

**Precedence order** for pin placement:
1. Explicit `"position"` coordinates (highest priority)
2. Explicit `"side"` field
3. Automatic name-based detection
4. Default to "left" (fallback)

### Custom Pin Positions

Override auto-calculated positions with exact coordinates:

```json
{
  "id": "custom_device",
  "name": "Custom Device",
  "category": "sensors",
  "pins": [
    {"name": "VCC", "role": "3V3", "position": {"x": 0, "y": 0}},
    {"name": "GND", "role": "GND", "position": {"x": 0, "y": 20}}
  ]
}
```

### Custom Dimensions

Override auto-calculated size:

```json
{
  "display": {
    "width": 100.0,
    "height": 60.0
  }
}
```

### Custom Layout

Control pin spacing and starting position:

```json
{
  "layout": {
    "pin_spacing": 15.0,
    "start_y": 10.0,
    "orientation": "vertical"
  }
}
```

### Device Parameters

Create device variants with parameters:

```json
{
  "id": "led_ring",
  "name": "LED Ring ({num_leds})",
  "category": "leds",
  "pins": [
    {"name": "VCC", "role": "5V"},
    {"name": "GND", "role": "GND"},
    {"name": "DIN", "role": "GPIO"}
  ],
  "parameters": {
    "num_leds": {
      "type": "integer",
      "default": 24,
      "description": "Number of LEDs in the ring"
    }
  }
}
```

Usage:

```python
ring_24 = registry.create('led_ring', num_leds=24)  # "LED Ring (24)"
ring_48 = registry.create('led_ring', num_leds=48)  # "LED Ring (48)"
```

## Pin Roles

Available pin roles:

- `GPIO` - General purpose I/O
- `3V3` / `5V` - Power supply
- `GND` - Ground
- `I2C_SDA` / `I2C_SCL` - I2C communication
- `SPI_MOSI` / `SPI_MISO` / `SPI_SCLK` / `SPI_CE0` / `SPI_CE1` - SPI communication
- `UART_TX` / `UART_RX` - Serial communication
- `PWM` - PWM output

## Testing Your Device

```bash
# Test device creation
uv run python -c "from pinviz.devices import get_registry; r = get_registry(); print(r.create('bme280').name)"

# Generate a test diagram
uv run pinviz render your_test_config.yaml -o test_output.svg

# Validate the configuration
uv run pinviz validate your_test_config.yaml

# Run full test suite
uv run pytest
```

## Best Practices

1. **Use minimal configuration** - Let smart defaults handle most fields
2. **Choose appropriate category** - Determines default color
3. **Use descriptive pin names** - Makes diagrams more readable
4. **Add documentation fields** - `description`, `datasheet_url`, `notes`
5. **Test with real diagrams** - Ensure pins align correctly
6. **Follow naming conventions** - Use lowercase IDs, human-readable names

## Examples

See existing devices in `src/pinviz/device_configs/` for reference:

- `sensors/bh1750.json` - Simple I2C sensor
- `sensors/ds18b20.json` - 1-Wire sensor with notes
- `leds/led.json` - Parametric device
- `displays/ssd1306.json` - I2C display
- `io/button.json` - Simple input device
