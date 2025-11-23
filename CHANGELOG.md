# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-01-23

### Changed
- **BREAKING**: CLI now requires explicit command for rendering diagrams
  - Old: `pinviz diagram.yaml -o output.svg`
  - New: `pinviz render diagram.yaml -o output.svg`
  - Reason: Improved clarity and consistency with modern CLI tools (AWS, kubectl, etc.)
- Improved CLI help formatting with professional output
  - Removed confusing `{render,example,list}` syntax from help
  - Added properly formatted examples section with line breaks
  - Added default values to all options (`--gpio`/`--no-gpio`)
  - Made `--gpio`/`--no-gpio` mutually exclusive groups
  - Better metavar names: `CONFIG_FILE`, `PATH`, `NAME`
- Enhanced CLI structure
  - Changed "Positional Arguments" to "Commands:" section
  - Added descriptions to each subcommand
  - Custom help formatter preserves examples formatting

### Fixed
- CLI help examples now display on separate lines (no wrapping)
- MCP server documentation updated with correct CLI commands
- All documentation updated to use new CLI format

### Documentation
- Updated `docs/guide/cli.md` to show only new format
- Updated MCP server docstrings with correct command syntax
- All examples in documentation now use `pinviz render` format

## [0.2.1] - 2025-01-23

### Fixed
- Logo display on PyPI by using absolute GitHub URL instead of relative path

## [0.2.0] - 2025-01-23

### Added
- **MCP Server Integration**: AI-powered GPIO diagram generation via Model Context Protocol
  - Natural language parsing: Generate diagrams from prompts like "connect BME280 sensor"
  - Intelligent pin assignment: Automatic I2C bus sharing, SPI chip selects, power distribution
  - URL-based device discovery: Parse device specs directly from documentation URLs
  - 25-device database with I2C, SPI, GPIO, and UART devices
  - User device database for custom devices
  - MCP tools: `generate_diagram`, `parse_device_from_url`, `list_devices`, `get_device_info`
- Supported domains for URL parsing: Adafruit, SparkFun, Waveshare, Pimoroni, Raspberry Pi, Seeed Studio, peppe8o.com
- `pinviz-mcp` command line entry point for MCP server
- Comprehensive test suite with 325+ tests (71% code coverage)

### Changed
- Restructured package as namespace package for better MCP server integration
- Moved assets into `src/pinviz/` for proper packaging with `uv build`
- Enhanced YAML generation with explicit `yaml_content` field for Claude Desktop
- Improved MCP tool documentation with clear usage instructions

### Fixed
- YAML reconstruction errors when using MCP server through Claude Desktop
- Asset packaging issues with `uv_build` backend

## [0.1.5] - 2025-01-21

### Added
- Modern CLI with rich-argparse for beautiful, colorful help formatting
- `--version` / `-v` flag to display package version
- Automatic version detection from package metadata using importlib.metadata

### Changed
- CLI help output now uses RichHelpFormatter for improved readability and visual appeal
- Enhanced user experience with color-coded help text and better formatting

## [0.1.3] - 2025-01-21

### Changed
- Improved installation instructions in README and documentation
  - Recommend `uv tool install pinviz` as primary method for CLI usage
  - Clearly explain difference between `uv tool install` and `uv add`
  - Add note about `uv run` prefix requirement for `uv add` installations
- Restructured Quick Start guide with progressive learning path
  - Step 1: Try built-in examples (immediate success)
  - Step 2: Create custom YAML diagrams
  - Step 3: Use Python API for programmatic control
- Updated GitHub Pages documentation (docs/getting-started/) to match README improvements

### Fixed
- Installation confusion where users couldn't find `pinviz` command after `uv add`

## [0.1.2] - 2025-01-21

### Fixed
- Fixed image URLs in README to use raw.githubusercontent.com for proper display on PyPI

## [0.1.1] - 2025-01-21

### Added
- PyPI publishing workflow with GitHub Actions following uv best practices
- Comprehensive CONTRIBUTING.md guide for contributors
- JUnit XML test result reporting to CI pipeline

### Changed
- Moved example diagrams from `out/` to `images/` directory
- Removed Codecov badge (will be re-added later with proper token)
- Consolidated dev dependencies to fix CI failures

### Fixed
- Fixed test result publishing permissions in GitHub Actions

## [0.1.0] - 2025-01-20

### Added
- Initial release of PinViz (formerly pi-diagrammer)
- Declarative YAML/JSON configuration for diagram creation
- Programmatic Python API for creating diagrams
- Automatic wire routing with configurable styles (orthogonal, curved, mixed)
- Inline component support (resistors, capacitors, diodes)
- Color-coded wires with automatic assignment based on pin function
- Built-in templates for Raspberry Pi 5 board
- Pre-configured device templates:
  - BH1750 I2C light sensor
  - IR LED ring module
  - Generic I2C/SPI devices
  - LED and button components
- Optional GPIO pin reference diagram
- SVG output for scalable, high-quality vector graphics
- CLI tool with commands:
  - `pinviz render` - Generate diagrams from config files
  - `pinviz example` - Generate built-in examples
  - `pinviz list` - List available templates
- Comprehensive documentation with MkDocs + Material theme
- GitHub Actions CI workflow with automated testing
- Project badges (CI, docs, license, Python version, PyPI)
- Full test coverage (85%+) with pytest
- Type hints throughout codebase
- Ruff linting and formatting configuration

### Documentation
- Complete README with installation, quick start, and examples
- CONTRIBUTING.md with development guidelines
- CLAUDE.md for AI assistant context
- Example configurations and diagrams

[Unreleased]: https://github.com/nordstad/PinViz/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/nordstad/PinViz/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/nordstad/PinViz/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/nordstad/PinViz/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/nordstad/PinViz/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/nordstad/PinViz/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nordstad/PinViz/releases/tag/v0.1.0
