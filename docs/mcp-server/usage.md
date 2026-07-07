# MCP Server Usage Guide

Practical examples and workflows for using the PinViz MCP Server through Claude Desktop or any MCP-compatible client.

→ [MCP Server Overview](index.md) | [Installation](installation.md) | [Tool Reference](mcp-tools.md) | [Contributing Devices](contributing.md)

## Quick Start Examples

### Example 1: Simple Sensor Connection

**Prompt:**
```
Connect a BME280 temperature sensor to my Raspberry Pi 5
```

**What happens:**

1. Parser extracts "BME280" and "Raspberry Pi 5"
2. Device lookup finds BME280 (I2C sensor)
3. Pin assignment allocates I2C pins (SDA=pin 3, SCL=pin 5) + power/ground
4. Generates YAML diagram specification

**Output:**
```yaml
title: "BME280 Wiring"
board: raspberry_pi_5
devices:
  - id: bme280
    name: BME280
connections:
  - board_pin: 1
    device: BME280
    device_pin: VCC
    color: "#FF0000"
  - board_pin: 3
    device: BME280
    device_pin: SDA
    color: "#0000FF"
  - board_pin: 5
    device: BME280
    device_pin: SCL
    color: "#FFFF00"
  - board_pin: 9
    device: BME280
    device_pin: GND
    color: "#000000"
```

### Example 2: Multiple Devices with Bus Sharing

**Prompt:**
```
Wire a BH1750 light sensor and BME280 to my pi
```

**What happens:**

1. Parser extracts two I2C devices
2. Pin assignment recognises I2C bus sharing
3. Both devices share SDA (pin 3) and SCL (pin 5)
4. Each gets separate power and ground

**Key feature:** I2C bus sharing — multiple devices on the same bus without conflict.

### Example 3: Mixed Protocols

**Prompt:**
```
Connect BME280 sensor, LED on GPIO 17, and MCP3008 ADC
```

**What happens:**

1. BME280: I2C (pins 3, 5)
2. LED: GPIO (pin 11 = GPIO17)
3. MCP3008: SPI (CE0, MISO, MOSI, SCLK)

**Key feature:** Handles multiple protocols in one diagram automatically.

---

## Real-World Use Cases

### Home Automation Dashboard

**Goal:** Environmental monitoring with LED indicators

**Prompt:**
```
Set up a home automation system with:
- BME280 for temperature/humidity/pressure
- BH1750 for light level
- Two LEDs (one on GPIO 17, one on GPIO 27) for status indicators
```

**Result:** Complete wiring diagram with I2C bus sharing for sensors, separate GPIO pins for LEDs.

### Weather Station

**Prompt:**
```
Create a weather station with BME280, DHT22, wind speed sensor (pulse counter), and SSD1306 OLED display
```

**Result:** Mixed protocol diagram — I2C for BME280 and OLED, GPIO for DHT22 and wind sensor.

### Robotics Project

**Prompt:**
```
Wire up motor control: Motor HAT, two ultrasonic sensors, and a relay for power management
```

**Result:** HAT-based wiring with additional sensors on remaining GPIO pins.

### Plant Monitor

**Prompt:**
```
Plant monitoring system:
- Soil moisture sensor on ADC channel 0 (MCP3008)
- DHT22 for air temp/humidity
- Relay to control water pump
```

**Result:** SPI ADC, GPIO sensor, GPIO relay control — all pin assignments handled automatically.

---

## Advanced Features

### I2C Bus Sharing

The pin assignment algorithm automatically shares I2C buses:

```
Prompt: "Connect BME280, BH1750, and SSD1306 display"

Result:
- All three devices share SDA (pin 3) and SCL (pin 5)
- Each gets individual power and ground
- I2C addresses: BME280 0x76, BH1750 0x23, SSD1306 0x3C
```

### SPI Chip Select Allocation

For SPI devices:

```
Prompt: "Connect MCP3008 ADC and MCP23S17 IO expander"

Result:
- Both share MISO, MOSI, SCLK
- MCP3008 gets CE0 (pin 24)
- MCP23S17 gets CE1 (pin 26)
```

### Power Distribution

The system intelligently distributes power pins:

- **3.3V devices**: Cycle through pins 1 and 17
- **5V devices**: Cycle through pins 2 and 4
- **Ground**: Cycle through 8 available GND pins

### Conflict Detection

```
Prompt: "Connect 5 devices that all need 3.3V power"

Result:
- Assigns pins 1 and 17 for 3.3V
- Warns: "Limited 3.3V pins available (2), sharing recommended"
- Provides wiring with voltage rail sharing notes
```

---

## Tips and Best Practices

### Be specific with device names

✅ Good: `"Connect BME280 sensor"`
❌ Vague: `"Connect temperature sensor"`

Fuzzy matching helps, but exact names give reliable results.

### Specify protocols when ambiguous

✅ Good: `"Connect BME280 using I2C"`
❌ Ambiguous: `"Connect BME280"` — device supports both I2C and SPI; defaults to I2C

### Use board aliases

All of these are equivalent:
- `"raspberry pi 5"` / `"rpi5"` / `"pi5"`

### Request specific output formats

- For editing: `output_format: yaml`
- For automation: `output_format: json`
- For quick review: `output_format: summary`

See [Tool Reference → Output Formats](mcp-tools.md#output-formats) for examples.

### Check the device database first

```
What sensors are available?
```

This tells you what devices the system knows about before you write your prompt.

### Use tags for discovery

```
Find all environmental sensors
```

The `search_devices_by_tags` tool matches on any combination of tags.

### Add custom devices via URL

```
Add this sensor: https://www.sparkfun.com/products/12345
```

The `parse_device_from_url` tool extracts specs and can save to your user database.

---

## Troubleshooting

### "Device not found"

Parser couldn't match the device name.

1. Check spelling: `get_device_info(device_id="bme280")`
2. List similar devices: `list_devices(query="bme")`
3. Add from a datasheet URL: `parse_device_from_url(...)`

### "Pin conflict detected"

Multiple devices need the same exclusive pin. The system usually auto-resolves, but check:

- Too many SPI devices? (max 2 with CE0/CE1)
- Do devices require specific GPIO pins?

### "Parsing failed"

The natural language prompt is too ambiguous.

- Be more specific: `"Connect BME280 sensor"` vs `"Connect sensor"`
- Use a structured format: `"BME280 and BH1750"`
- Check that `ANTHROPIC_API_KEY` is set (required for complex prompts)

---

## Next Steps

- [Tool Reference](mcp-tools.md) — full parameter docs and response schemas for all 6 tools
- [Contributing Devices](contributing.md) — add devices to the database
- [Validation Guide](../validation.md) — understand validation checks
- [Device database](https://github.com/nordstad/PinViz/blob/main/src/pinviz/mcp/devices/database.json) on GitHub
