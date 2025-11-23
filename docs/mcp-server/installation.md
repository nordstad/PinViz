# PinViz MCP Server Installation Guide

This guide walks you through installing and configuring the PinViz MCP Server for use with MCP-compatible clients like Claude Desktop.

## Prerequisites

- Python 3.10 or higher
- pip or uv package manager
- An MCP-compatible client (e.g., Claude Desktop, Cline, etc.)

## Installation Methods

### Method 1: Using Claude Desktop CLI (Easiest)

If you have Claude Desktop installed with the CLI tools, this is the quickest way to get started:

1. **Install PinViz:**

```bash
pip install pinviz
```

2. **Add to Claude Desktop:**

```bash
claude mcp add pinviz pinviz-mcp
```

This automatically configures the MCP server in your Claude Desktop settings.

3. **Restart Claude Desktop**

Close and reopen Claude Desktop, and you're ready to use PinViz!

**For uv users:**

```bash
# Install
uv pip install pinviz

# Add to Claude Desktop with uv runner
claude mcp add pinviz uv -- run pinviz-mcp
```

### Method 2: Using pip (Manual configuration)

1. **Install PinViz with MCP server support:**

```bash
pip install pinviz
```

2. **Verify the installation:**

```bash
pinviz-mcp --help
```

You should see the MCP server help message.

Then follow the [Claude Desktop manual configuration](#claude-desktop) steps below.

### Method 3: Using uv (Recommended for developers)

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

### Method 4: From source (For contributors)

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

### GitHub Copilot (VS Code)

GitHub Copilot supports MCP servers through VS Code's Multi-Provider Chat feature.

#### Prerequisites

- VS Code version 1.90 or later
- GitHub Copilot extension installed and activated
- Python 3.10+ installed and available in PATH

#### Configuration

1. **Install PinViz** (if not already installed):

```bash
pip install pinviz
```

2. **Open VS Code Settings**:

   - Press `Cmd+,` (macOS) or `Ctrl+,` (Windows/Linux)
   - Search for "mcp"
   - Or edit your `settings.json` directly: `Cmd+Shift+P` → "Preferences: Open User Settings (JSON)"

3. **Add MCP Server Configuration**:

   Add the following to your VS Code `settings.json`:

**For pip installation:**

```json
{
  "github.copilot.chat.mcp.servers": {
    "pinviz": {
      "command": "pinviz-mcp"
    }
  }
}
```

**For uv installation:**

```json
{
  "github.copilot.chat.mcp.servers": {
    "pinviz": {
      "command": "uv",
      "args": ["run", "pinviz-mcp"]
    }
  }
}
```

**For project-specific configuration (workspace settings):**

Create `.vscode/settings.json` in your project root:

```json
{
  "github.copilot.chat.mcp.servers": {
    "pinviz": {
      "command": "uv",
      "args": ["run", "--directory", "${workspaceFolder}", "pinviz-mcp"]
    }
  }
}
```

4. **Reload VS Code Window**:

   - Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Developer: Reload Window"
   - Press Enter

5. **Verify in Copilot Chat**:

   Open Copilot Chat (click the chat icon in the sidebar) and try:
   ```
   @pinviz List available Raspberry Pi devices
   ```

#### Using PinViz with GitHub Copilot

Once configured, you can interact with PinViz in VS Code's Copilot Chat:

- **Generate diagrams**: `@pinviz Connect BME280 and LED to Raspberry Pi 5`
- **Search devices**: `@pinviz What I2C sensors are available?`
- **Get device info**: `@pinviz Show me the BME280 pinout`
- **Device discovery**: `@pinviz Parse device specs from this URL: [datasheet URL]`

### Other MCP Clients

For other MCP-compatible clients (e.g., Cline, Zed, custom implementations), refer to their documentation for configuring MCP servers. The general pattern is:

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

- Read the [Usage Guide](usage.md) for examples
- Learn how to [contribute devices](contributing.md)
- Explore the [device database](https://github.com/nordstad/PinViz/blob/main/src/pinviz/mcp/devices/database.json)

## Support

- Report issues: https://github.com/nordstad/PinViz/issues
- Documentation: https://nordstad.github.io/PinViz/
- MCP Specification: https://spec.modelcontextprotocol.io/
