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

## Exit Codes

- `0` - Success
- `1` - Error (file not found, invalid configuration, etc.)
- `2` - Command-line usage error

## Environment Variables

Currently, PinViz does not use any environment variables.

## See Also

- [YAML Configuration Guide](yaml-config.md)
- [Python API Guide](python-api.md)
- [Examples](examples.md)
