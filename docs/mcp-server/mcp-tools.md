# MCP Tool Reference

Full reference for the six tools exposed by the PinViz MCP Server.

→ [MCP Server Overview](index.md) | [Installation](installation.md) | [Usage Guide](usage.md) | [Contributing Devices](contributing.md)

## Tools at a Glance

| Tool | Purpose |
|------|---------|
| [`list_devices`](#1-list_devices) | Browse and filter the device database |
| [`get_device_info`](#2-get_device_info) | Get full specs for a specific device |
| [`search_devices_by_tags`](#3-search_devices_by_tags) | Find devices by tag combination |
| [`generate_diagram`](#4-generate_diagram) | Generate wiring diagram from natural language |
| [`parse_device_from_url`](#5-parse_device_from_url) | Extract device specs from a datasheet URL |
| [`get_database_summary`](#6-get_database_summary) | Get statistics about the device database |

---

## 1. list_devices

List available devices with optional filtering.

**Parameters:**

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| `category` | string | No | `display`, `sensor`, `hat`, `component`, `actuator`, `breakout` |
| `protocol` | string | No | `I2C`, `SPI`, `UART`, `GPIO`, `1-Wire`, `PWM` |
| `query` | string | No | Free-text search term |

**Example — list all sensors:**

```
Show me all available sensors in the database
```

Claude will call:
```json
{
  "tool": "list_devices",
  "parameters": {
    "category": "sensor"
  }
}
```

Response:
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
  ],
  "total": 10
}
```

**Example — list I2C displays:**

```
What OLED displays do you have that use I2C?
```

Claude will call:
```json
{
  "tool": "list_devices",
  "parameters": {
    "category": "display",
    "protocol": "I2C"
  }
}
```

---

## 2. get_device_info

Get detailed specifications for a specific device.

**Parameters:**

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `device_id` | string | Yes | Device ID or name; fuzzy matching supported |

**Example — exact ID lookup:**

```
Tell me about the BME280 sensor
```

Claude will call:
```json
{
  "tool": "get_device_info",
  "parameters": {
    "device_id": "bme280"
  }
}
```

Response:
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

**Fuzzy matching:** "BH 1750" → "bh1750" (SequenceMatcher threshold 0.6).

---

## 3. search_devices_by_tags

Find devices by tags — all supplied tags must match.

**Parameters:**

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `tags` | list | Yes | All tags must be present on matching devices |

**Example:**

```
Find all devices that are both OLED and use I2C
```

Claude will call:
```json
{
  "tool": "search_devices_by_tags",
  "parameters": {
    "tags": ["oled", "i2c"]
  }
}
```

Response:
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

---

## 4. generate_diagram

Generate a complete wiring diagram from a natural language description.

**Parameters:**

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| `prompt` | string | Yes | Natural language description |
| `output_format` | string | No | `yaml` (default), `json`, `summary` |
| `title` | string | No | Custom diagram title |

### Output Formats

**`yaml`** — human-readable, editable (default):

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

**`json`** — machine-readable, for automation:

```json
{
  "title": "My Project",
  "board": "raspberry_pi_5",
  "devices": [{"id": "bme280", "name": "BME280"}],
  "connections": [
    {"board_pin": 1, "device": "BME280", "device_pin": "VCC"}
  ]
}
```

**`summary`** — plain text for conversation:

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

### Automatic Validation

Every generated diagram is validated automatically. The response includes:

```json
{
  "status": "success",
  "validation_status": "passed",
  "validation_message": "All validation checks passed.",
  "validation": {
    "total_issues": 0,
    "errors": [],
    "warnings": [],
    "info": []
  },
  "yaml_content": "..."
}
```

**Validation status values:**

| Status | Meaning |
|--------|---------|
| `passed` | No issues — safe to use |
| `warning` | Warnings found — review before using |
| `failed` | Errors found — **do not use** (hardware damage risk) |

**Checks performed:**

1. **Pin conflicts** (ERROR) — multiple devices on same GPIO
2. **I2C address conflicts** (WARNING) — same address on same bus
3. **Voltage mismatches** (ERROR/WARNING) — 5V/3.3V incompatibility
4. **Current limits** (WARNING) — GPIO overload (16 mA per pin)
5. **Connection validity** (ERROR) — invalid pins or devices

**Example with a validation error:**

```json
{
  "status": "error",
  "validation_status": "failed",
  "validation_message": "Diagram has 1 validation error(s)...",
  "validation": {
    "total_issues": 2,
    "errors": [
      "⚠️  Error: Pin 11 (GPIO17) used by multiple devices: LED1.+, LED2.+"
    ],
    "warnings": [
      "⚠️  Warning: GPIO GPIO17 driving 2 devices (max current: 16mA per pin)"
    ],
    "info": []
  }
}
```

See the [Validation Guide](../validation.md) for full details on all checks.

---

## 5. parse_device_from_url

Extract device specifications from a datasheet or product page URL.

**Parameters:**

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `url` | string | Yes | Datasheet or product page URL |
| `device_id` | string | No | Override the auto-generated device ID |
| `save_to_database` | boolean | No | Auto-save to user database (default: `false`) |

**Example:**

```
Add this new sensor from Adafruit: https://www.adafruit.com/product/1234
```

Claude will call:
```json
{
  "tool": "parse_device_from_url",
  "parameters": {
    "url": "https://www.adafruit.com/product/1234",
    "save_to_database": false
  }
}
```

Response:
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

**Performance note:** URL parsing takes 3–5 seconds (network fetch + Claude API call).

---

## 6. get_database_summary

Get statistics about the device database.

**Example:**

```
How many devices are in the database?
```

Response:
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

---

## Natural Language Parsing

The `generate_diagram` tool uses a hybrid parsing approach.

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

5. **Custom GPIO specifications**
   ```
   Connect LED to GPIO 17 and button to GPIO 22 with pull-up
   ```

6. **Board aliases**
   - "raspberry pi 5" / "rpi5" / "pi5" → Raspberry Pi 5
   - "raspberry pi 4" / "rpi4" / "pi4" → Raspberry Pi 4
   - "raspberry pi pico" / "pico" / "rpi pico" → Raspberry Pi Pico

### Parsing Method: Hybrid Approach

| Method | Coverage | Notes |
|--------|----------|-------|
| Regex patterns | ~80% of prompts | Fast, no API cost |
| Claude API fallback | ~20% of prompts | Complex prompts, $0.01–0.05 per call |

The Claude API fallback requires `ANTHROPIC_API_KEY` to be set.

---

## Performance Reference

| Operation | Typical latency |
|-----------|----------------|
| Device lookup | < 1 ms (in-memory) |
| Simple prompt (regex) | < 10 ms |
| Complex prompt (Claude API) | 1–3 s |
| Diagram generation (≤8 devices) | < 100 ms |
| URL parsing | 3–5 s |
