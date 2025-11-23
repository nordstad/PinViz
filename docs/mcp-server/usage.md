# PinViz MCP Server Usage Guide

This guide provides comprehensive examples of using the PinViz MCP Server through MCP-compatible clients like Claude Desktop.

## Overview

The PinViz MCP Server provides two main capabilities:

1. **Device Database Queries**: Search and retrieve information about 25+ Raspberry Pi devices
2. **Diagram Generation**: Convert natural language prompts into GPIO wiring diagrams

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
4. Generates YAML/JSON diagram specification

**Expected output:**
```yaml
title: "BME280 Wiring"
board: raspberry_pi_5
devices:
  - id: bme280
    name: BME280
    category: sensor
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
2. Pin assignment recognizes I2C bus sharing
3. Both devices share SDA (pin 3) and SCL (pin 5)
4. Each gets separate power and ground

**Key feature:** Intelligent I2C bus sharing - multiple devices on same bus

### Example 3: Mixed Protocols

**Prompt:**
```
Connect BME280 sensor, LED on GPIO 17, and MCP3008 ADC
```

**What happens:**
1. BME280: I2C (pins 3, 5)
2. LED: GPIO (pin 11 = GPIO17)
3. MCP3008: SPI (CE0, MISO, MOSI, SCLK)

**Key feature:** Handles multiple protocols in one diagram

## MCP Tools Reference

### 1. list_devices

**Description:** List available devices with optional filtering

**Parameters:**
- `category` (optional): display, sensor, hat, component, actuator, breakout
- `protocol` (optional): I2C, SPI, UART, GPIO, 1-Wire, PWM
- `query` (optional): Search term

**Example 1: List all sensors**
```
Show me all available sensors in the database
```

Claude will use:
```json
{
  "tool": "list_devices",
  "parameters": {
    "category": "sensor"
  }
}
```

**Response:**
```json
{
  "devices": [
    {
      "id": "bme280",
      "name": "BME280 Temperature/Humidity/Pressure Sensor",
      "category": "sensor",
      "protocols": ["I2C", "SPI"],
      "voltage": "3.3V"
    },
    {
      "id": "dht22",
      "name": "DHT22 Temperature/Humidity Sensor",
      "category": "sensor",
      "protocols": ["GPIO"],
      "voltage": "3.3V-5V"
    }
    // ... more sensors
  ],
  "total": 10
}
```

**Example 2: List I2C displays**
```
What OLED displays do you have that use I2C?
```

Claude will use:
```json
{
  "tool": "list_devices",
  "parameters": {
    "category": "display",
    "protocol": "I2C"
  }
}
```

### 2. get_device_info

**Description:** Get detailed specifications for a specific device

**Parameters:**
- `device_id` (required): Device ID or name (fuzzy matching supported)

**Example 1: Exact ID lookup**
```
Tell me about the BME280 sensor
```

Claude will use:
```json
{
  "tool": "get_device_info",
  "parameters": {
    "device_id": "bme280"
  }
}
```

**Response:**
```json
{
  "id": "bme280",
  "name": "BME280 Temperature/Humidity/Pressure Sensor",
  "category": "sensor",
  "description": "Combined environmental sensor with I2C/SPI interface",
  "pins": [
    {"name": "VCC", "role": "3V3", "position": 0},
    {"name": "GND", "role": "GND", "position": 1},
    {"name": "SCL", "role": "I2C_SCL", "position": 2},
    {"name": "SDA", "role": "I2C_SDA", "position": 3}
  ],
  "protocols": ["I2C", "SPI"],
  "voltage": "3.3V",
  "i2c_address": "0x76",
  "current_draw": "3.6µA @ 1Hz",
  "datasheet_url": "https://www.bosch-sensortec.com/bst/products/all_products/bme280",
  "tags": ["sensor", "temperature", "humidity", "pressure", "environmental", "i2c", "spi"]
}
```

**Example 2: Fuzzy name matching**
```
What's the pinout for the BH 1750 light sensor?
```

Claude will match "BH 1750" → "bh1750" using fuzzy matching (SequenceMatcher threshold 0.6)

### 3. search_devices_by_tags

**Description:** Find devices by tags (all must match)

**Parameters:**
- `tags` (required): List of tags

**Example:**
```
Find all devices that are both OLED and use I2C
```

Claude will use:
```json
{
  "tool": "search_devices_by_tags",
  "parameters": {
    "tags": ["oled", "i2c"]
  }
}
```

**Response:**
```json
{
  "devices": [
    {
      "id": "ssd1306",
      "name": "SSD1306 0.96\" OLED Display",
      "tags": ["display", "oled", "i2c", "spi", "128x64"]
    },
    {
      "id": "sh1106",
      "name": "SH1106 1.3\" OLED Display",
      "tags": ["display", "oled", "i2c", "spi", "128x64"]
    }
  ],
  "matched_tags": ["oled", "i2c"],
  "total": 2
}
```

### 4. generate_diagram

**Description:** Generate wiring diagram from natural language

**Parameters:**
- `prompt` (required): Natural language description
- `output_format` (optional): "yaml", "json", or "summary" (default: yaml)
- `title` (optional): Custom diagram title

**Example 1: Basic sensor connection**
```
Connect a BH1750 light sensor to my raspberry pi
```

Claude will use:
```json
{
  "tool": "generate_diagram",
  "parameters": {
    "prompt": "Connect a BH1750 light sensor to my raspberry pi",
    "output_format": "yaml"
  }
}
```

**Response:**
```yaml
title: "BH1750 Wiring"
board: raspberry_pi_5
devices:
  - id: bh1750
    name: BH1750 Light Sensor
connections:
  - board_pin: 1
    device: BH1750 Light Sensor
    device_pin: VCC
  - board_pin: 3
    device: BH1750 Light Sensor
    device_pin: SDA
  - board_pin: 5
    device: BH1750 Light Sensor
    device_pin: SCL
  - board_pin: 6
    device: BH1750 Light Sensor
    device_pin: GND
```

**Example 2: Multiple devices**
```
Create a weather station with BME280, BH1750, and an LED indicator on GPIO 17
```

**Example 3: Summary format**
```
Connect BME280 and show me just the summary
```

Claude will use:
```json
{
  "tool": "generate_diagram",
  "parameters": {
    "prompt": "Connect BME280",
    "output_format": "summary"
  }
}
```

**Response:**
```
Diagram: BME280 Wiring

Devices:
  • BME280 Temperature/Humidity/Pressure Sensor (I2C, 3.3V)

Connections:
  • Pin 1 (3.3V) → BME280 VCC [red]
  • Pin 3 (GPIO2/SDA) → BME280 SDA [blue]
  • Pin 5 (GPIO3/SCL) → BME280 SCL [yellow]
  • Pin 9 (GND) → BME280 GND [black]

Notes:
  - I2C address: 0x76
  - Total devices: 1
  - Conflicts: None
```

### 5. parse_device_from_url

**Description:** Extract device specifications from a datasheet URL

**Parameters:**
- `url` (required): Datasheet or product page URL
- `device_id` (optional): Override device ID
- `save_to_database` (optional): Auto-save to user database (default: false)

**Example:**
```
Add this new sensor from Adafruit: https://www.adafruit.com/product/1234
```

Claude will use:
```json
{
  "tool": "parse_device_from_url",
  "parameters": {
    "url": "https://www.adafruit.com/product/1234",
    "save_to_database": false
  }
}
```

**Response:**
```json
{
  "device": {
    "id": "adafruit-1234",
    "name": "Adafruit Sensor Name",
    "category": "sensor",
    "pins": [...],
    "protocols": ["I2C"],
    "voltage": "3.3V"
  },
  "confidence": "high",
  "extraction_method": "claude_api",
  "warnings": []
}
```

### 6. get_database_summary

**Description:** Get statistics about the device database

**Example:**
```
How many devices are in the database?
```

**Response:**
```json
{
  "total_devices": 25,
  "by_category": {
    "display": 5,
    "sensor": 10,
    "hat": 4,
    "component": 3,
    "actuator": 2,
    "breakout": 1
  },
  "by_protocol": {
    "I2C": 12,
    "SPI": 6,
    "GPIO": 8,
    "UART": 2,
    "1-Wire": 1,
    "PWM": 3
  },
  "voltage_distribution": {
    "3.3V": 15,
    "5V": 5,
    "3.3V-5V": 5
  }
}
```

## Real-World Use Cases

### Use Case 1: Home Automation Dashboard

**Goal:** Environmental monitoring with LED indicators

**Prompt:**
```
Set up a home automation system with:
- BME280 for temperature/humidity/pressure
- BH1750 for light level
- Two LEDs (one on GPIO 17, one on GPIO 27) for status indicators
```

**Result:** Complete wiring diagram with I2C bus sharing for sensors, separate GPIO pins for LEDs

### Use Case 2: Weather Station

**Prompt:**
```
Create a weather station with BME280, DHT22, wind speed sensor (pulse counter), and SSD1306 OLED display
```

**Result:** Mixed protocol diagram (I2C for BME280 and OLED, GPIO for DHT22 and wind sensor)

### Use Case 3: Robotics Project

**Prompt:**
```
Wire up motor control: Motor HAT, two ultrasonic sensors, and a relay for power management
```

**Result:** HAT-based wiring with additional sensors

### Use Case 4: Plant Monitor

**Prompt:**
```
Plant monitoring system:
- Soil moisture sensor on ADC channel 0 (MCP3008)
- DHT22 for air temp/humidity
- Relay to control water pump
```

**Result:** SPI ADC, GPIO sensor, GPIO relay control

## Advanced Features

### I2C Bus Sharing

The pin assignment algorithm automatically shares I2C buses:

```
Prompt: "Connect BME280, BH1750, and SSD1306 display"

Result:
- All three devices share SDA (pin 3) and SCL (pin 5)
- Each gets individual power and ground
- I2C addresses managed automatically (BME280: 0x76, BH1750: 0x23, SSD1306: 0x3C)
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

The system intelligently distributes power:

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

## Natural Language Parsing

### Supported Prompt Patterns

1. **"Connect X and Y"**
   ```
   Connect BME280 and LED
   ```

2. **"Wire X to my pi"**
   ```
   Wire a BH1750 light sensor to my raspberry pi 5
   ```

3. **"X, Y, and Z"**
   ```
   BME280, DHT22, and SSD1306 display
   ```

4. **"Set up X with Y"**
   ```
   Set up a weather station with BME280 and BH1750
   ```

5. **Custom specifications**
   ```
   Connect LED to GPIO 17 and button to GPIO 22 with pull-up
   ```

6. **Board aliases**
   - "raspberry pi 5" / "rpi5" / "pi5" → Raspberry Pi 5
   - "raspberry pi 4" / "rpi4" / "pi4" → Raspberry Pi 4 (future)

### Parsing Method: Hybrid Approach

1. **Regex patterns (80% of cases)**: Fast, no API costs
2. **Claude API fallback (20% of cases)**: Complex prompts, $0.01-0.05 per parse

## Output Formats

### YAML (default)

Human-readable, editable configuration:

```yaml
title: "My Project"
board: raspberry_pi_5
devices:
  - id: bme280
    name: BME280
connections:
  - board_pin: 1
    device: BME280
    device_pin: VCC
```

### JSON

Machine-readable, programmatic access:

```json
{
  "title": "My Project",
  "board": "raspberry_pi_5",
  "devices": [{"id": "bme280", "name": "BME280"}],
  "connections": [
    {
      "board_pin": 1,
      "device": "BME280",
      "device_pin": "VCC"
    }
  ]
}
```

### Summary (text)

Quick overview for conversation:

```
Diagram: My Project

Devices:
  • BME280 (I2C, 3.3V)

Connections:
  • Pin 1 → BME280 VCC
  • Pin 3 → BME280 SDA
  ...
```

## Tips and Best Practices

### 1. Be specific with device names

✅ Good: "Connect BME280 sensor"
❌ Vague: "Connect temperature sensor"

The fuzzy matcher helps, but exact names work best.

### 2. Specify protocols when ambiguous

✅ Good: "Connect BME280 using I2C"
❌ Ambiguous: "Connect BME280" (device supports both I2C and SPI)

Default is I2C, but being explicit helps.

### 3. Use board aliases

All equivalent:
- "raspberry pi 5"
- "rpi5"
- "pi5"

### 4. Request specific output formats

- For editing: `output_format: yaml`
- For automation: `output_format: json`
- For quick review: `output_format: summary`

### 5. Check device database first

Before requesting a diagram:
```
What sensors are available?
```

This helps you know what devices the system supports.

### 6. Use tags for discovery

```
Find all environmental sensors
→ search_devices_by_tags(tags=["environmental"])
```

### 7. Add custom devices via URL

```
Add this sensor: https://www.sparkfun.com/products/12345
```

System will extract specs and add to user database.

## Troubleshooting

### "Device not found"

**Problem:** Parser couldn't match device name

**Solution:**
1. Check spelling: `get_device_info(device_id="bme280")`
2. List similar devices: `list_devices(query="bme")`
3. Add device via URL: `parse_device_from_url(...)`

### "Pin conflict detected"

**Problem:** Multiple devices need same exclusive pin

**Solution:** System usually auto-resolves, but check:
- Are you using too many SPI devices? (max 2 with CE0/CE1)
- Do devices need specific GPIO pins?

### "Parsing failed"

**Problem:** Natural language prompt too ambiguous

**Solution:**
- Be more specific: "Connect BME280 sensor" vs "Connect sensor"
- Use structured format: "BME280 and BH1750"
- Check if ANTHROPIC_API_KEY is set (for complex prompts)

## Performance Notes

- **Device lookup**: < 1ms (in-memory database)
- **Simple prompts** (regex): < 10ms
- **Complex prompts** (Claude API): 1-3 seconds
- **Diagram generation**: < 100ms (up to 8 devices)
- **URL parsing**: 3-5 seconds (includes network fetch + Claude API)

## Next Steps

- Learn how to [contribute devices](CONTRIBUTING_DEVICES.md)
- Check the [installation guide](INSTALLATION.md) for setup
- Explore the [device database](../devices/database.json)
- Read the [device schema](../devices/schema.json)

## Support

- Report issues: https://github.com/nordstad/PinViz/issues
- Documentation: https://nordstad.github.io/PinViz/
- MCP Specification: https://spec.modelcontextprotocol.io/
