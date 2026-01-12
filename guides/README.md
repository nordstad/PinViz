# PinViz Development Guides

This directory contains detailed step-by-step guides for extending and maintaining PinViz.

## Available Guides

### [cli-development.md](cli-development.md)

How to add new CLI commands, work with JSON output, configure logging, and test commands.

**Topics covered:**

- CLI structure and architecture
- Adding new commands with Typer
- JSON output schemas
- Configuration management
- Shell completion

### [adding-boards.md](adding-boards.md)

How to add support for new board types (standard and dual-sided layouts).

**Topics covered:**

- Board JSON configuration structure
- Standard boards (Pi 4, Pi 5)
- Dual-sided boards (Pico)
- SVG asset requirements
- Testing and validation

### [adding-devices.md](adding-devices.md)

How to add new device templates with smart defaults.

**Topics covered:**

- Device JSON configuration structure
- Smart defaults system
- Device categories and colors
- Parametric devices
- Pin roles and wire colors

### [publishing.md](publishing.md)

How to publish new versions to PyPI using GitHub Actions.

**Topics covered:**

- Correct publishing workflow (tag-only)
- Common mistakes to avoid
- Workflow stages and testing
- Troubleshooting failed releases
- Version numbering

## Quick Start

For most development tasks, you'll want to:

1. Read the relevant guide above
2. Check the main [CLAUDE.md](../CLAUDE.md) for architecture overview
3. Look at existing examples in the codebase
4. Run tests to verify your changes

## Getting Help

- Check the [main README](../README.md) for project overview
- See [CLAUDE.md](../CLAUDE.md) for architecture and design patterns
- Browse [docs/](../docs/) for user-facing documentation
- Look at test files for usage examples
