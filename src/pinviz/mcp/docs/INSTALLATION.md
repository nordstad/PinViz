# PinViz MCP Server Installation Guide

This guide walks you through installing and configuring the PinViz MCP Server for use with MCP-compatible clients like Claude Desktop.

## Prerequisites

- Python 3.10 or higher
- pip or uv package manager
- An MCP-compatible client (e.g., Claude Desktop, Cline, etc.)

## Installation Methods

### Method 1: Using pip (Recommended for most users)

1. **Install PinViz with MCP server support:**

```bash
pip install pinviz
```

2. **Verify the installation:**

```bash
pinviz-mcp --help
```

You should see the MCP server help message.

### Method 2: Using uv (Recommended for developers)

1. **Install uv if you haven't already:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install PinViz:**

```bash
uv pip install pinviz
```

3. **Verify the installation:**

```bash
uv run pinviz-mcp --help
```

### Method 3: From source (For contributors)

1. **Clone the repository:**

```bash
git clone https://github.com/nordstad/PinViz.git
cd PinViz/pi-diagrammer
```

2. **Install dependencies:**

```bash
uv sync --dev
```

3. **Test the MCP server:**

```bash
uv run pinviz-mcp
```

## Configuration for MCP Clients

### Claude Desktop

Claude Desktop is Anthropic's desktop application that supports MCP servers.

#### macOS/Linux

1. **Locate the Claude Desktop config file:**

```bash
# macOS
~/.config/claude/claude_desktop_config.json

# Linux
~/.config/claude/claude_desktop_config.json
```

2. **Edit the configuration file:**

Add the following to your `claude_desktop_config.json`:

**For pip installation:**

```json
{
  "mcpServers": {
    "pinviz": {
      "command": "pinviz-mcp"
    }
  }
}
```

**For uv installation:**

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

**For source installation (development):**

```json
{
  "mcpServers": {
    "pinviz": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/PinViz/pi-diagrammer", "pinviz-mcp"]
    }
  }
}
```

3. **Restart Claude Desktop**

Close and reopen Claude Desktop for the changes to take effect.

#### Windows

1. **Locate the Claude Desktop config file:**

```
%APPDATA%\Claude\claude_desktop_config.json
```

2. **Edit the configuration file:**

Add the following to your `claude_desktop_config.json`:

**For pip installation:**

```json
{
  "mcpServers": {
    "pinviz": {
      "command": "pinviz-mcp"
    }
  }
}
```

**For uv installation:**

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

3. **Restart Claude Desktop**

### Other MCP Clients

For other MCP-compatible clients (e.g., Cline, custom implementations), refer to their documentation for configuring MCP servers. The general pattern is:

- **Command:** `pinviz-mcp` (or `uv run pinviz-mcp`)
- **Transport:** stdio (standard input/output)
- **Protocol:** MCP 1.0

## Verifying the Installation

### Test 1: Check MCP Server Communication

1. Open Claude Desktop
2. Start a new conversation
3. Type: "List available Raspberry Pi devices"
4. Claude should respond with a list of devices from the PinViz database

### Test 2: Generate a Simple Diagram

1. In Claude Desktop, type: "Connect a BME280 sensor to my Raspberry Pi"
2. Claude should generate a wiring diagram showing the connections

### Test 3: Use MCP Tools Directly

In Claude Desktop, you can inspect available MCP tools:

1. Type: "What MCP tools are available?"
2. Look for PinViz tools like:
   - `list_devices`
   - `get_device_info`
   - `generate_diagram`
   - `search_devices_by_tags`
   - `parse_device_from_url`

## Troubleshooting

### Issue: "Command not found: pinviz-mcp"

**Solution:** The installation directory is not in your PATH.

**For pip users:**

```bash
# Find where pip installed the script
pip show pinviz | grep Location
# Add to PATH or use full path in config
```

**For uv users:**

Use the full `uv run` command in your MCP client config.

### Issue: Claude Desktop doesn't show PinViz tools

**Solution:** Check the Claude Desktop logs for errors.

**macOS/Linux:**

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Windows:**

```
%APPDATA%\Claude\logs\mcp*.log
```

Common issues:
- Python version too old (need 3.10+)
- Missing dependencies (run `pip install pinviz` again)
- Incorrect path in config file

### Issue: "Module not found" errors

**Solution:** Ensure all dependencies are installed:

```bash
pip install pinviz --upgrade
```

Or with uv:

```bash
uv sync
```

### Issue: MCP server starts but tools fail

**Solution:** Check that the device database is accessible:

```bash
python -c "from pinviz.mcp.device_manager import DeviceManager; dm = DeviceManager(); print(f'Loaded {len(dm.devices)} devices')"
```

You should see "Loaded 25 devices" (or more if you've added custom devices).

## Environment Variables

The PinViz MCP server supports the following environment variables:

- `ANTHROPIC_API_KEY`: Required for natural language parsing and URL-based device parsing
  - Get your API key from: https://console.anthropic.com/
  - Set in your shell config or `.env` file

Example:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

For Claude Desktop, add to your config:

```json
{
  "mcpServers": {
    "pinviz": {
      "command": "pinviz-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

## Updating

### pip installation:

```bash
pip install --upgrade pinviz
```

### uv installation:

```bash
uv pip install --upgrade pinviz
```

### Source installation:

```bash
cd PinViz/pi-diagrammer
git pull
uv sync
```

## Next Steps

- Read the [Usage Guide](USAGE.md) for examples
- Learn how to [contribute devices](CONTRIBUTING_DEVICES.md)
- Explore the [device database](../devices/database.json)

## Support

- Report issues: https://github.com/nordstad/PinViz/issues
- Documentation: https://nordstad.github.io/PinViz/
- MCP Specification: https://spec.modelcontextprotocol.io/
