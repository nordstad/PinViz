# Device Configuration Guide

This guide shows how to create user-friendly device configurations.

## Philosophy: Simple by Default, Flexible When Needed

Device configs should be **as simple as possible** with smart defaults, but allow customization when needed.

## Minimal Example (Recommended)

```json
{
  "id": "bh1750",
  "name": "BH1750 Light Sensor",
  "category": "sensors",
  "description": "BH1750 I2C ambient light sensor",

  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"},
    {"name": "SCL", "role": "I2C_SCL"},
    {"name": "SDA", "role": "I2C_SDA"}
  ],

  "i2c_address": "0x23",
  "datasheet_url": "https://example.com/datasheet.pdf"
}
```

**What gets auto-calculated:**
- ✅ Pin positions (vertical layout, 8px spacing)
- ✅ Device dimensions (fits all pins + padding)
- ✅ Device color (based on category)

## Required Fields

```json
{
  "id": "unique-id",           // Unique identifier (lowercase, no spaces)
  "name": "Display Name",      // Human-readable name
  "pins": [                    // At least one pin required
    {"name": "VCC", "role": "3V3"}
  ]
}
```

## Optional But Recommended

```json
{
  "category": "sensors",                    // sensors, displays, leds, actuators, io
  "description": "Brief description",       // What the device does
  "i2c_address": "0x23",                   // For I2C devices
  "datasheet_url": "https://...",          // Link to documentation
  "notes": "Additional information"         // Setup notes, warnings, etc.
}
```

## Layout Options

### Default: Vertical Layout (Auto)

Pins are arranged vertically with automatic spacing.

```json
{
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"}
  ]
  // No layout section needed!
  // Result: VCC at (5, 10), GND at (5, 18)
}
```

### Horizontal Layout

```json
{
  "layout": {
    "type": "horizontal",
    "pin_spacing": 12.0
  },
  "pins": [
    {"name": "D0", "role": "GPIO"},
    {"name": "D1", "role": "GPIO"},
    {"name": "D2", "role": "GPIO"}
  ]
  // Result: D0 at (5, 10), D1 at (17, 10), D2 at (29, 10)
}
```

### Custom Spacing

```json
{
  "layout": {
    "type": "vertical",
    "pin_spacing": 12.0,   // Larger spacing
    "pin_x": 10.0,         // Different x position
    "start_y": 15.0        // Different starting y
  },
  "pins": [...]
}
```

### Explicit Positions (Advanced)

Only use for complex layouts:

```json
{
  "pins": [
    {"name": "VCC", "role": "3V3", "position": {"x": 5, "y": 10}},
    {"name": "GND", "role": "GND", "position": {"x": 75, "y": 10}}
  ]
}
```

## Display Properties

Auto-calculated by default, but can override:

```json
{
  "display": {
    "width": 100.0,       // Default: 80.0
    "height": 70.0,       // Default: auto (based on pins)
    "color": "#FF5733"    // Default: category color
  }
}
```

### Category Colors (Defaults)

| Category | Color | Hex |
|----------|-------|-----|
| sensors | Turquoise | #50E3C2 |
| displays | Blue | #4A90E2 |
| leds | Red | #E74C3C |
| actuators | Orange | #F5A623 |
| io | Gray | #95A5A6 |

## Pin Roles

Common pin roles (use exact values):

- Power: `3V3`, `5V`
- Ground: `GND`
- GPIO: `GPIO`
- I2C: `I2C_SDA`, `I2C_SCL`
- SPI: `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1`
- UART: `UART_TX`, `UART_RX`
- PWM: `PWM`

## Optional Pin Fields

```json
{
  "name": "ADDR",
  "role": "GPIO",
  "optional": true,           // Mark as optional
  "description": "Address select pin"  // Pin description
}
```

## Complete Example (All Features)

```json
{
  "id": "ssd1306",
  "name": "SSD1306 OLED Display",
  "category": "displays",
  "description": "128x64 monochrome OLED display with I2C interface",
  "manufacturer": "Solomon Systech",

  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"},
    {"name": "SCL", "role": "I2C_SCL"},
    {"name": "SDA", "role": "I2C_SDA"}
  ],

  "layout": {
    "type": "vertical",
    "pin_spacing": 8.0
  },

  "display": {
    "width": 90.0,
    "height": 55.0,
    "color": "#4A90E2"
  },

  "i2c_address": "0x3C",
  "datasheet_url": "https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf",
  "notes": "Requires I2C pull-up resistors (usually built-in). Address can be 0x3C or 0x3D."
}
```

## Parameterized Devices

For devices with variants (like colored LEDs):

```json
{
  "id": "led",
  "name": "{color_name} LED",    // Template substitution
  "category": "leds",

  "parameters": {
    "color_name": {
      "type": "string",
      "default": "Red",          // Default value
      "description": "LED color for display name",
      "allowed_values": ["Red", "Green", "Blue", "Yellow", "White"]
    }
  },

  "pins": [
    {"name": "+", "role": "GPIO"},
    {"name": "-", "role": "GND"}
  ]
}
```

Usage: `registry.create("led", color_name="Blue")` → "Blue LED"

## I2C Address Formats

Both are supported:

```json
"i2c_address": "0x23"     // Hex string (recommended)
"i2c_address": "35"       // Decimal string
```

## Best Practices

### ✅ DO:
- Use minimal required fields
- Let auto-calculation handle positions and dimensions
- Include datasheet URL for reference
- Add notes for setup requirements
- Use descriptive names

### ❌ DON'T:
- Don't specify explicit positions unless necessary
- Don't duplicate metadata (e.g., protocols can be inferred)
- Don't add fields that aren't used for diagram generation
- Don't use overly technical descriptions

## Validation

Your config will be validated for:
- Required fields present
- Valid pin roles
- Valid I2C addresses
- Unique pin names
- Reasonable dimensions

## Examples By Device Type

### I2C Sensor (Minimal)
```json
{
  "id": "bme280",
  "name": "BME280 Environmental Sensor",
  "category": "sensors",
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"},
    {"name": "SCL", "role": "I2C_SCL"},
    {"name": "SDA", "role": "I2C_SDA"}
  ],
  "i2c_address": "0x76"
}
```

### Simple Component (LED)
```json
{
  "id": "red_led",
  "name": "Red LED",
  "category": "leds",
  "pins": [
    {"name": "+", "role": "GPIO"},
    {"name": "-", "role": "GND"}
  ]
}
```

### Button/Switch
```json
{
  "id": "button",
  "name": "Push Button",
  "category": "io",
  "pins": [
    {"name": "SIG", "role": "GPIO"},
    {"name": "GND", "role": "GND"}
  ]
}
```

## Migration from Python

Converting a Python factory function to JSON:

**Before (Python):**
```python
def bh1750_light_sensor() -> Device:
    pins = [
        DevicePin("VCC", PinRole.POWER_3V3, Point(5.0, 10)),
        DevicePin("GND", PinRole.GROUND, Point(5.0, 18)),
        DevicePin("SCL", PinRole.I2C_SCL, Point(5.0, 26)),
        DevicePin("SDA", PinRole.I2C_SDA, Point(5.0, 34)),
    ]
    return Device(name="BH1750", pins=pins, width=70.0, height=60.0)
```

**After (JSON):**
```json
{
  "id": "bh1750",
  "name": "BH1750",
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"},
    {"name": "SCL", "role": "I2C_SCL"},
    {"name": "SDA", "role": "I2C_SDA"}
  ]
}
```

**Result:** 15 lines of code → 10 lines of JSON (and much simpler!)

## Contributing

To add a new device:
1. Create JSON file in appropriate category folder
2. Use minimal config (let defaults work)
3. Test: `uv run python -c "from pinviz.devices import get_registry; get_registry().create('your-device')"`
4. Submit PR!

Or use the CLI wizard (coming soon):
```bash
pinviz add-device
```
