# Contributing Devices to PinViz Database

Thank you for contributing to the PinViz device database! This guide explains how to add new Raspberry Pi-compatible devices.

## Quick Start

There are three ways to add devices:

1. **Automated (Recommended)**: Use the MCP `parse_device_from_url` tool
2. **Manual**: Edit `user_devices.json` directly
3. **Contribution**: Submit a PR to add devices to the main database

## Method 1: Automated Device Addition (Recommended)

### Using Claude Desktop with PinViz MCP Server

The easiest way is to let Claude extract device specifications automatically:

```
Add this sensor to my database: https://www.adafruit.com/product/2652
```

Claude will:
1. Fetch the datasheet/product page
2. Extract device specifications using AI
3. Validate against the schema
4. Optionally save to your user database

**Example conversation:**

```
You: Add this BME680 sensor to my user database:
     https://www.adafruit.com/product/3660

Claude: I'll parse the device specifications from that URL.

[Uses parse_device_from_url tool]

Found: BME680 Gas, Temperature, Humidity, Pressure Sensor
- Category: sensor
- Protocols: I2C, SPI
- Voltage: 3.3V
- I2C Address: 0x76
- 4 pins: VCC, GND, SCL, SDA

Would you like me to save this to your user database?

You: Yes, save it

Claude: ✓ Saved to user_devices.json
```

### Supported Vendor URLs

The automated parser works best with these vendors:

- **Adafruit**: https://www.adafruit.com/product/*
- **SparkFun**: https://www.sparkfun.com/products/*
- **Waveshare**: https://www.waveshare.com/*
- **Pimoroni**: https://shop.pimoroni.com/products/*
- **Seeed Studio**: https://www.seeedstudio.com/*
- **Pololu**: https://www.pololu.com/product/*
- **DFRobot**: https://www.dfrobot.com/*

**Note:** PDF datasheets work but HTML pages are preferred (faster, better extraction).

### Manual Override with URL Parser

If auto-detection isn't perfect, you can provide additional details:

```
Parse https://www.adafruit.com/product/1234
and set the device ID to "my-custom-sensor"
with I2C address 0x68
```

## Method 2: Manual Device Entry

### Step 1: Locate user_devices.json

```bash
# The file is created in your project:
src/pinviz_mcp/devices/user_devices.json
```

If the file doesn't exist, create it with this structure:

```json
{
  "version": "1.0.0",
  "devices": []
}
```

### Step 2: Add Your Device

Add a device entry following this template:

```json
{
  "id": "my-device-id",
  "name": "Human Readable Device Name",
  "category": "sensor",
  "description": "Brief description of the device",
  "pins": [
    {
      "name": "VCC",
      "role": "3V3",
      "position": 0
    },
    {
      "name": "GND",
      "role": "GND",
      "position": 1
    },
    {
      "name": "SCL",
      "role": "I2C_SCL",
      "position": 2
    },
    {
      "name": "SDA",
      "role": "I2C_SDA",
      "position": 3
    }
  ],
  "protocols": ["I2C"],
  "voltage": "3.3V",
  "i2c_address": "0x76",
  "datasheet_url": "https://example.com/datasheet.pdf",
  "manufacturer": "Company Name",
  "current_draw": "100mA",
  "tags": ["sensor", "temperature", "i2c"],
  "notes": "Optional usage notes"
}
```

### Step 3: Validate Your Entry

Run the validation test:

```bash
uv run pytest tests/test_device_manager.py::test_user_devices_loading -v
```

Or validate in Python:

```python
from pinviz.mcp.device_manager import DeviceManager

dm = DeviceManager()
device = dm.get_device_by_id("my-device-id")
print(f"✓ Device loaded: {device.name}")
```

### Step 4: Test Diagram Generation

```bash
# Using Claude Desktop:
"Connect my-device-id to raspberry pi 5"
```

## Method 3: Contributing to Main Database

### Prerequisites

1. Fork the PinViz repository
2. Clone your fork
3. Install development dependencies: `uv sync --dev`

### Contribution Workflow

#### Step 1: Add Device to database.json

Edit `src/pinviz_mcp/devices/database.json`:

```json
{
  "version": "1.0.0",
  "devices": [
    // ... existing devices ...
    {
      "id": "your-new-device",
      // ... your device spec ...
    }
  ]
}
```

#### Step 2: Validate Against Schema

```bash
# Run device manager tests
uv run pytest tests/test_device_manager.py -v

# Validate all pin roles
uv run python -c "
from pinviz.mcp.device_manager import DeviceManager
from pinviz.model import PinRole

dm = DeviceManager()
device = dm.get_device_by_id('your-new-device')

for pin in device.pins:
    PinRole(pin.role)  # Validates pin role

print('✓ Device validated successfully')
"
```

#### Step 3: Add Integration Test

Create a test in `tests/test_integration_real_world.py`:

```python
def test_your_device_connection():
    """Test wiring diagram for YourDevice."""
    parser = PromptParser(use_llm=False)
    dm = DeviceManager()

    # Parse prompt
    parsed = parser.parse("connect your-new-device to my pi")

    # Get device
    device = dm.get_device_by_id("your-new-device")
    assert device is not None

    # Generate pin assignment
    assigner = PinAssigner()
    assignments = assigner.assign_pins([device], "raspberry_pi_5")

    # Verify key pins
    assert any(a.device_id == "your-new-device" for a in assignments)
```

#### Step 4: Run Full Test Suite

```bash
# Run all tests
uv run pytest tests/ -v

# Check coverage
uv run pytest tests/ --cov=src/pinviz_mcp --cov-report=term-missing

# Lint and format
uv run ruff check src/pinviz_mcp/
uv run ruff format src/pinviz_mcp/
```

#### Step 5: Submit Pull Request

1. Commit your changes:
   ```bash
   git add src/pinviz_mcp/devices/database.json tests/
   git commit -m "Add YourDevice to device database"
   ```

2. Push to your fork:
   ```bash
   git push origin add-your-device
   ```

3. Create a Pull Request on GitHub with:
   - Device name and description
   - Link to datasheet
   - Test results (pytest output)
   - Example usage (prompt + generated diagram)

## Device Entry Reference

### Required Fields

```json
{
  "id": "string",           // Unique identifier (lowercase, hyphens)
  "name": "string",         // Human-readable name
  "category": "string",     // One of: sensor, display, hat, component, actuator, breakout
  "description": "string",  // Brief description
  "pins": [...],            // Array of pin objects (see below)
  "protocols": [...],       // Array of protocol strings
  "voltage": "string"       // "3.3V", "5V", or "3.3V-5V"
}
```

### Pin Object Structure

```json
{
  "name": "string",    // Pin name (VCC, GND, SDA, etc.)
  "role": "string",    // Pin role (see valid roles below)
  "position": number   // Relative position on device (0-indexed)
}
```

### Valid Pin Roles

From `pinviz.model.PinRole` enum:

- **Power:** `3V3`, `5V`
- **Ground:** `GND`
- **I2C:** `I2C_SDA`, `I2C_SCL`
- **SPI:** `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1`
- **UART:** `UART_TX`, `UART_RX`
- **PWM:** `PWM`
- **GPIO:** `GPIO` (generic digital I/O)

**Important:** Use these exact values. Invalid roles will fail validation.

### Valid Categories

- `sensor` - Environmental, motion, light sensors
- `display` - OLED, LCD, E-Paper, TFT displays
- `hat` - Raspberry Pi HATs (full-size add-on boards)
- `component` - LEDs, buttons, basic components
- `actuator` - Motors, relays, buzzers, servo
- `breakout` - Breakout boards, ADCs, DACs, IO expanders

### Valid Protocols

- `I2C` - Inter-Integrated Circuit
- `SPI` - Serial Peripheral Interface
- `UART` - Universal Asynchronous Receiver-Transmitter
- `GPIO` - General Purpose Input/Output
- `1-Wire` - Dallas 1-Wire protocol
- `PWM` - Pulse Width Modulation

### Optional Fields

```json
{
  "i2c_address": "0x76",                    // For I2C devices
  "spi_max_speed": "10MHz",                 // For SPI devices
  "datasheet_url": "https://...",           // Official datasheet
  "product_url": "https://...",             // Where to buy
  "manufacturer": "Company Name",           // Manufacturer
  "current_draw": "3.6µA @ 1Hz",           // Typical current
  "dimensions": "2.5mm x 2.5mm x 0.93mm",  // Physical size
  "tags": ["sensor", "environmental"],      // Searchable tags
  "notes": "Additional usage information"   // Special notes
}
```

## Device Naming Guidelines

### Device IDs

- **Lowercase only**: `bme280` not `BME280`
- **Use hyphens**: `ssd1306-oled` not `ssd1306_oled`
- **Be specific**: `dht22` not `dht` (if multiple variants exist)
- **Include size for displays**: `lcd-16x2` not just `lcd`
- **Include model**: `mcp3008` not just `adc`

### Device Names

- **Include model number**: "BME280" not "Bosch Sensor"
- **Add key specs**: "SSD1306 0.96\" OLED Display"
- **Use manufacturer names**: "Adafruit Motor HAT" if it's specific

## Common Device Types

### I2C Sensor Template

```json
{
  "id": "sensor-name",
  "name": "Sensor Display Name",
  "category": "sensor",
  "description": "What it measures",
  "pins": [
    {"name": "VCC", "role": "3V3", "position": 0},
    {"name": "GND", "role": "GND", "position": 1},
    {"name": "SCL", "role": "I2C_SCL", "position": 2},
    {"name": "SDA", "role": "I2C_SDA", "position": 3}
  ],
  "protocols": ["I2C"],
  "voltage": "3.3V",
  "i2c_address": "0xXX",
  "tags": ["sensor", "i2c"]
}
```

### SPI Device Template

```json
{
  "id": "device-name",
  "name": "Device Display Name",
  "category": "display",
  "pins": [
    {"name": "VCC", "role": "3V3", "position": 0},
    {"name": "GND", "role": "GND", "position": 1},
    {"name": "SCK", "role": "SPI_SCLK", "position": 2},
    {"name": "MOSI", "role": "SPI_MOSI", "position": 3},
    {"name": "MISO", "role": "SPI_MISO", "position": 4},
    {"name": "CS", "role": "SPI_CE0", "position": 5}
  ],
  "protocols": ["SPI"],
  "voltage": "3.3V",
  "spi_max_speed": "10MHz",
  "tags": ["display", "spi"]
}
```

### GPIO Component Template

```json
{
  "id": "component-name",
  "name": "Component Display Name",
  "category": "component",
  "pins": [
    {"name": "VCC", "role": "3V3", "position": 0},
    {"name": "GND", "role": "GND", "position": 1},
    {"name": "SIG", "role": "GPIO", "position": 2}
  ],
  "protocols": ["GPIO"],
  "voltage": "3.3V",
  "tags": ["component", "gpio"]
}
```

### HAT Template

```json
{
  "id": "hat-name",
  "name": "HAT Display Name",
  "category": "hat",
  "description": "What the HAT provides",
  "pins": [
    // HATs typically use multiple pins
    {"name": "3V3", "role": "3V3", "position": 0},
    {"name": "5V", "role": "5V", "position": 1},
    {"name": "GND", "role": "GND", "position": 2},
    {"name": "SDA", "role": "I2C_SDA", "position": 3},
    {"name": "SCL", "role": "I2C_SCL", "position": 4}
    // ... more pins as needed
  ],
  "protocols": ["I2C", "GPIO"],  // Multiple protocols common
  "voltage": "3.3V-5V",
  "tags": ["hat"]
}
```

## Pin Role Guidelines

### When to use GPIO vs specific roles:

- **Use I2C_SDA/I2C_SCL**: When device explicitly uses I2C protocol
- **Use SPI_***: When device explicitly uses SPI protocol
- **Use GPIO**: For generic digital pins (buttons, LEDs, 1-Wire, DHT sensors)
- **Use PWM**: Only when device requires PWM-capable pins
- **Use UART_TX/UART_RX**: When device uses serial communication

### Pin Position

Number pins from 0 in the order they appear on the device:

```json
"pins": [
  {"name": "VCC", "role": "3V3", "position": 0},   // First pin
  {"name": "GND", "role": "GND", "position": 1},   // Second pin
  {"name": "SDA", "role": "I2C_SDA", "position": 2},  // Third pin
  {"name": "SCL", "role": "I2C_SCL", "position": 3}   // Fourth pin
]
```

## Testing Your Device

### Test 1: Device Loads Successfully

```python
from pinviz.mcp.device_manager import DeviceManager

dm = DeviceManager()
device = dm.get_device_by_id("your-device-id")

assert device is not None
print(f"✓ Device: {device.name}")
print(f"  Category: {device.category}")
print(f"  Protocols: {', '.join(device.protocols)}")
print(f"  Pins: {len(device.pins)}")
```

### Test 2: Fuzzy Matching Works

```python
# Try different variations
variations = [
    "your device id",
    "yourdeviceid",
    "Your Device",
    "YOURDEVICE"
]

for query in variations:
    device = dm.get_device_by_id(query)
    if device:
        print(f"✓ '{query}' matched '{device.id}'")
```

### Test 3: Diagram Generation Works

```bash
# Via Claude Desktop:
"Connect your-device to raspberry pi"

# Should generate valid YAML with no errors
```

### Test 4: Pin Roles Are Valid

```python
from pinviz.model import PinRole

# This will raise ValueError if any role is invalid
for pin in device.pins:
    PinRole(pin.role)

print("✓ All pin roles are valid")
```

## Common Mistakes

### ❌ Invalid Pin Role

```json
"pins": [
  {"name": "DATA", "role": "data", "position": 0}  // WRONG
]
```

✅ **Fix:** Use valid PinRole enum value:

```json
"pins": [
  {"name": "DATA", "role": "GPIO", "position": 0}  // CORRECT
]
```

### ❌ Missing Required Fields

```json
{
  "id": "my-sensor",
  "name": "My Sensor"
  // Missing: category, description, pins, protocols, voltage
}
```

✅ **Fix:** Include all required fields

### ❌ Invalid I2C Address Format

```json
"i2c_address": "118"  // WRONG (decimal)
```

✅ **Fix:** Use hex format with 0x prefix:

```json
"i2c_address": "0x76"  // CORRECT
```

### ❌ Wrong Category

```json
{
  "id": "servo-motor",
  "category": "sensor"  // WRONG
}
```

✅ **Fix:** Use correct category:

```json
{
  "id": "servo-motor",
  "category": "actuator"  // CORRECT
}
```

### ❌ Inconsistent Protocols and Pin Roles

```json
{
  "protocols": ["I2C"],
  "pins": [
    {"name": "TX", "role": "UART_TX", "position": 0}  // MISMATCH
  ]
}
```

✅ **Fix:** Make protocols match pin roles:

```json
{
  "protocols": ["UART"],
  "pins": [
    {"name": "TX", "role": "UART_TX", "position": 0}  // MATCHES
  ]
}
```

## Tips for Quality Contributions

1. **Reference official datasheets**: Link to manufacturer documentation
2. **Test with real hardware**: Verify pinouts if possible
3. **Add comprehensive tags**: Makes devices easier to discover
4. **Include usage notes**: Special configuration, common issues
5. **Specify I2C addresses**: Critical for bus sharing
6. **Indicate voltage ranges**: Prevents damage to devices
7. **Note current draw**: Helps users plan power requirements

## Device Database Structure

```
devices/
├── database.json          # Main database (25 devices)
├── user_devices.json      # User-added devices
└── schema.json            # JSON schema for validation
```

**Priority order:**
1. user_devices.json (highest priority, overrides main database)
2. database.json (default database)

## Support

- Questions: https://github.com/nordstad/PinViz/discussions
- Bugs: https://github.com/nordstad/PinViz/issues
- Device requests: https://github.com/nordstad/PinViz/issues (use "device-request" label)

## License

All contributed devices must have publicly available datasheets.
Contributions are licensed under MIT (same as PinViz).
