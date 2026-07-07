# PinViz MCP Server

The PinViz MCP Server brings natural language diagram generation to PinViz through the [Model Context Protocol](https://modelcontextprotocol.io/). Generate Raspberry Pi GPIO wiring diagrams using conversational prompts with Claude.

## What is an MCP Server?

Model Context Protocol (MCP) is a standard that allows AI assistants like Claude to interact with external tools and data sources. The PinViz MCP Server enables Claude to:

- Parse natural language requests for GPIO connections
- Intelligently assign pins based on device requirements
- Generate complete wiring diagrams in SVG format
- Manage a database of 25+ popular Raspberry Pi components

## Features

### 🤖 Natural Language Processing
Generate diagrams from simple prompts like:
- "Connect a BME280 sensor and BH1750 light sensor to my Raspberry Pi"
- "Wire an OLED display and a temperature sensor"
- "I need a weather station with BME280, BH1750, and a DHT22"

### 🧠 Intelligent Pin Assignment
- Automatic I2C bus sharing for multiple sensors
- SPI chip select allocation
- Power rail distribution (3.3V vs 5V)
- GPIO conflict detection and resolution
- Pull-up resistor insertion for I2C

### 📚 Device Database
- 25+ pre-configured devices (sensors, displays, HATs, components)
- Add custom devices via URL parsing (Adafruit, SparkFun, Waveshare)
- User device database for personal collections
- Fuzzy device name matching

### 🎨 Output Formats
- SVG diagrams with automatic wire routing
- YAML configuration files
- JSON structured data
- Summary reports

## Quick Start

Get started with the MCP server in minutes:

```bash
# Install PinViz (using uv recommended, or pip)
uv tool install pinviz
# OR: pip install pinviz

# Configure Claude Desktop automatically
claude mcp add pinviz pinviz-mcp

# Restart Claude Desktop and start creating diagrams!
```

Then in Claude Desktop, simply ask:
> "Connect a BME280 sensor to my Raspberry Pi 5"

For manual configuration or other MCP clients, see the [Installation Guide](installation.md).

## Documentation

- **[Installation Guide](installation.md)** - Setup instructions for macOS, Linux, and Windows
- **[Usage Guide](usage.md)** - Examples, MCP tools, and advanced features
- **[Contributing Devices](contributing.md)** - Add your own devices to the database

## Example Workflow

1. **Ask Claude**: "I want to connect a BME280 and an OLED display"
2. **Claude uses MCP tools** to:
   - Parse your request
   - Look up device specifications
   - Assign pins intelligently
   - Generate the diagram
3. **Get results**: SVG diagram, YAML config, or summary

## Technical Details

- **Protocol**: MCP (Model Context Protocol) via stdio transport
- **Language**: Python 3.12+
- **Dependencies**: anthropic, mcp, beautifulsoup4, httpx
- **Database**: JSON-based device catalog with JSON schema validation
- **Pin Assignment**: Constraint-solving algorithm with conflict detection

## Support

- [GitHub Issues](https://github.com/nordstad/PinViz/issues) - Report bugs or request features
- [Repository](https://github.com/nordstad/PinViz) - View source code
- [Main Documentation](../index.md) - Learn about PinViz CLI and Python API

## Next Steps

Ready to get started? Head to the [Installation Guide](installation.md) to set up the MCP server.
