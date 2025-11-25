# YAML Configuration

Complete reference for YAML configuration files.

## Basic Structure

```yaml
title: "Diagram Title"
board: "raspberry_pi_5"  # or "raspberry_pi_zero_2w"
devices:
  - type: "device_type"
    name: "Device Name"
connections:
  - board_pin: 1
    device: "Device Name"
    device_pin: "Pin Name"
show_legend: true
```

## Supported Boards

- `raspberry_pi_5` (aliases: `rpi5`, `rpi`) - Raspberry Pi 5 with 40-pin GPIO header
- `raspberry_pi_zero_2w` (aliases: `raspberry_pi_zero`, `pizero`, `zero2w`, `zero`, `rpizero`) - Raspberry Pi Zero / Zero 2 W with 40-pin GPIO header

## Configuration Options

See the [Quick Start Guide](../getting-started/quickstart.md) for detailed examples.

Full documentation coming soon.
