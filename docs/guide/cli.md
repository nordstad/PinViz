# CLI Usage

Command-line interface reference for PinViz.

## Basic Usage

```bash
pinviz [OPTIONS] COMMAND [ARGS]
```

## Commands

### Render a Diagram

Generate a diagram from a YAML or JSON configuration file:

```bash
pinviz render CONFIG_FILE [-o OUTPUT_FILE]
```

**Arguments:**

- `CONFIG_FILE` - Path to YAML or JSON configuration file
- `-o, --output OUTPUT_FILE` - Output SVG file path (default: `<config>.svg`)

**Examples:**

```bash
# Generate diagram (output defaults to my-diagram.svg)
pinviz render my-diagram.yaml

# Specify custom output path
pinviz render my-diagram.yaml -o output/wiring.svg

# Works with JSON too
pinviz render my-diagram.json -o output.svg
```

### Generate Built-in Examples

Generate one of the built-in example diagrams:

```bash
pinviz example EXAMPLE_NAME [-o OUTPUT_FILE]
```

**Available examples:**

- `bh1750` - BH1750 I2C light sensor
- `ir_led` - IR LED ring module
- `i2c_spi` - Multiple I2C and SPI devices

**Examples:**

```bash
# Generate BH1750 example
pinviz example bh1750 -o bh1750.svg

# Generate IR LED example
pinviz example ir_led -o ir_led.svg
```

### Validate a Configuration

Check your diagram configuration for wiring errors and safety issues:

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/scripts/demos/output/validation_demo.gif" alt="PinViz Validation Demo" width="800">
</p>

```bash
pinviz validate CONFIG_FILE [--strict]
```

**Arguments:**

- `CONFIG_FILE` - Path to YAML or JSON configuration file
- `--strict` - Treat warnings as errors (exits with code 1)

**Examples:**

```bash
# Validate diagram configuration
pinviz validate my-diagram.yaml

# Strict mode - warnings cause failure
pinviz validate my-diagram.yaml --strict
```

**Validation checks for:**

- Duplicate GPIO pin assignments (ERROR)
- I2C address conflicts (WARNING)
- Voltage mismatches (ERROR/WARNING)
- GPIO current limits (WARNING)
- Invalid pins or devices (ERROR)

See the [Validation Guide](../validation.md) for detailed information.

### List Templates

List all available board and device templates:

```bash
pinviz list
```

This displays:

- Available board templates (Raspberry Pi 5 and Pi Zero 2 W)
- Available device templates
- Available example diagrams

**Supported Boards:**

- `raspberry_pi_5` (aliases: `rpi5`, `rpi`) - Raspberry Pi 5 with 40-pin GPIO header
- `raspberry_pi_zero_2w` (aliases: `raspberry_pi_zero`, `pizero`, `zero2w`, `zero`, `rpizero`) - Raspberry Pi Zero / Zero 2 W with 40-pin GPIO header

## Global Options

- `--help` - Show help message and exit
- `--version` - Show version and exit
- `--log-level LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR; default: WARNING)
- `--log-format FORMAT` - Set log format (`json` or `console`; default: console)

### Logging Examples

```bash
# Enable INFO level logging to see validation details
pinviz --log-level INFO render my-diagram.yaml

# Debug logging for troubleshooting
pinviz --log-level DEBUG validate my-diagram.yaml

# JSON format for machine-readable logs
pinviz --log-format json render my-diagram.yaml
```

PinViz uses [structlog](https://www.structlog.org/) for structured logging. Log messages include:

- Event name and level
- Contextual information (file paths, device names, pin numbers)
- Timestamps
- Call site information (file, function, line number)

## Exit Codes

- `0` - Success
- `1` - Error (file not found, invalid configuration, etc.)
- `2` - Command-line usage error

## Environment Variables

Currently, PinViz does not use any environment variables.

## See Also

- [Validation Guide](../validation.md)
- [YAML Configuration Guide](yaml-config.md)
- [Python API Guide](python-api.md)
- [Examples](examples.md)
- [MCP Server](../mcp-server/index.md)
