# PinViz MCP Server

An MCP (Model Context Protocol) server that provides natural language access to Raspberry Pi GPIO device information and wiring diagram generation.

## Overview

The PinViz MCP Server exposes a comprehensive database of Raspberry Pi compatible devices (sensors, displays, HATs, components) through standardized MCP tools and resources. This enables AI assistants and other MCP clients to:

- Query device specifications and pinouts
- Search for devices by category, protocol, or tags
- Access detailed device information with fuzzy name matching
- Generate GPIO wiring diagrams (Phase 2 feature)

## Installation

The MCP server is included with PinViz. Install the package:

```bash
pip install pinviz
```

Or if using `uv`:

```bash
uv add pinviz
```

## Running the Server

Start the MCP server with stdio transport:

```bash
pinviz-mcp
```

Or with `uv`:

```bash
uv run pinviz-mcp
```

## Configuration for MCP Clients

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pinviz": {
      "command": "pinviz-mcp"
    }
  }
}
```

Or if using `uv`:

```json
{
  "mcpServers": {
    "pinviz": {
      "command": "uv",
      "args": ["run", "pinviz-mcp"]
    }
  }
}
```

## Available Tools

### `list_devices`

List available devices with optional filtering.

**Parameters:**
- `category` (optional): Filter by category (display, sensor, hat, component, actuator, breakout)
- `protocol` (optional): Filter by protocol (I2C, SPI, UART, GPIO, 1-Wire, PWM)
- `query` (optional): Search query for device name, description, or tags

**Returns:** JSON with list of matching devices

**Example:**
```python
# List all I2C sensors
result = await session.call_tool("list_devices", {
    "category": "sensor",
    "protocol": "I2C"
})
```

### `get_device_info`

Get detailed information about a specific device.

**Parameters:**
- `device_id` (required): Device ID or name (supports fuzzy matching)

**Returns:** JSON with complete device specifications including pins, protocols, voltage requirements

**Example:**
```python
# Get BH1750 light sensor specifications
result = await session.call_tool("get_device_info", {
    "device_id": "bh1750"
})
```

### `search_devices_by_tags`

Search for devices by tags.

**Parameters:**
- `tags` (required): List of tags to search for (all must match)

**Returns:** JSON with list of matching devices

**Example:**
```python
# Find all devices with "oled" and "i2c" tags
result = await session.call_tool("search_devices_by_tags", {
    "tags": ["oled", "i2c"]
})
```

### `get_database_summary`

Get statistics about the device database.

**Returns:** JSON with total device count and breakdown by category

**Example:**
```python
result = await session.call_tool("get_database_summary", {})
```

### `generate_diagram` (Phase 2)

Generate a GPIO wiring diagram from a natural language prompt.

**Status:** Placeholder in Phase 1, full implementation in Phase 2

**Parameters:**
- `prompt` (required): Natural language description of the wiring
- `output_format` (optional): Output format - 'yaml' or 'svg' (default: yaml)

**Returns:** YAML configuration or SVG diagram as string

## Available Resources

### `device://database`

Exposes the complete device database as JSON.

**Example:**
```python
result = await session.read_resource("device://database")
database = json.loads(result.contents[0].text)
```

### `device://schema`

Exposes the JSON schema for device entries.

**Example:**
```python
result = await session.read_resource("device://schema")
schema = json.loads(result.contents[0].text)
```

### `device://categories`

Get list of all device categories.

**Example:**
```python
result = await session.read_resource("device://categories")
categories = json.loads(result.contents[0].text)
```

### `device://protocols`

Get list of all supported protocols.

**Example:**
```python
result = await session.read_resource("device://protocols")
protocols = json.loads(result.contents[0].text)
```

## Device Database

The server includes a comprehensive database of 25+ devices:

### Categories

- **Displays** (5): OLED (SSD1306, SH1106), LCD 16x2, E-Paper, TFT
- **Sensors** (10): BME280, DHT22, BH1750, DS18B20, PIR, Ultrasonic, Photoresistor, MQ-2, MPU6050, TCS34725
- **HATs** (4): Terminal Block, Sense HAT, Motor HAT, Servo HAT
- **Breakouts** (1): 4-Channel Relay Board
- **Components** (3): LED, RGB LED, Push Button
- **Actuators** (2): Relay Module, Buzzer

### Device Information

Each device includes:
- Unique ID and name
- Category and description
- Pin definitions with roles
- Supported protocols
- Voltage requirements
- I2C addresses (where applicable)
- Datasheet URLs
- Tags for searchability
- Usage notes

## Device Database Schema

Devices are validated against a JSON schema. Key fields:

```json
{
  "id": "unique-device-id",
  "name": "Display Name",
  "category": "sensor|display|hat|component|actuator|breakout",
  "description": "Device description",
  "pins": [
    {
      "name": "VCC",
      "role": "3V3|5V|GND|I2C_SDA|I2C_SCL|SPI_*|GPIO|PWM",
      "position": 0
    }
  ],
  "protocols": ["I2C", "SPI", "UART", "GPIO", "1-Wire", "PWM"],
  "voltage": "3.3V|5V|3.3V-5V",
  "i2c_address": "0x23",
  "tags": ["sensor", "light", "i2c"]
}
```

## Development

### Running Tests

```bash
# Run device manager tests
uv run pytest tests/test_device_manager.py -v

# Run MCP server integration test
uv run python test_mcp_server.py
```

### Project Structure

```
src/pinviz_mcp/
├── __init__.py           # Package initialization
├── server.py             # MCP server implementation
├── device_manager.py     # Device database management
└── devices/
    ├── database.json     # Device catalog (25+ devices)
    └── schema.json       # JSON schema for validation
```

## Roadmap

### Phase 1: Core MCP Server + Device Database ✅
- [x] MCP server with stdio transport
- [x] 25+ device database with validation
- [x] Device query and search tools
- [x] Fuzzy name matching
- [x] Comprehensive test suite

### Phase 2: Natural Language Parsing (Planned)
- [ ] Natural language prompt parser
- [ ] Intelligent pin assignment algorithm
- [ ] I2C bus sharing and SPI CS allocation
- [ ] Connection conflict detection
- [ ] YAML/SVG diagram generation

### Phase 3: URL-Based Device Discovery (Planned)
- [ ] Datasheet URL parsing
- [ ] Claude API integration for spec extraction
- [ ] Interactive device registration
- [ ] User device database

### Phase 4: Testing & Refinement (Planned)
- [ ] Integration tests for diagram generation
- [ ] Performance optimization
- [ ] Documentation completion
- [ ] Community contribution workflow

## Contributing

Contributions are welcome! To add a new device to the database:

1. Follow the JSON schema in `src/pinviz_mcp/devices/schema.json`
2. Add your device entry to `src/pinviz_mcp/devices/database.json`
3. Run validation: `uv run pytest tests/test_device_manager.py`
4. Submit a pull request

## License

MIT License - see main PinViz repository for details.

## Links

- Main PinViz Repository: https://github.com/nordstad/PinViz
- Documentation: https://nordstad.github.io/PinViz/
- MCP Specification: https://spec.modelcontextprotocol.io/
