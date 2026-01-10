# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.8.0] - 2026-01-10

### Added
- Add Raspberry Pi 4 support and configuration enhancements (https://github.com/nordstad/PinViz/pull/52)
- Fix missing wires in examples and add validation to example command (https://github.com/nordstad/PinViz/pull/53)

### Changed
- Migrate from svgwrite to drawsvg (https://github.com/nordstad/PinViz/pull/44)
- Improve wire clarity with smooth Bezier routing and conflict prevention (https://github.com/nordstad/PinViz/pull/48)
- Standardize board rendering and improve layout controls (https://github.com/nordstad/PinViz/pull/49)
- Improve wire connections to device pins (https://github.com/nordstad/PinViz/pull/50)
- Code quality improvements: test coverage, refactoring, and configuration (https://github.com/nordstad/PinViz/pull/51)
- Streamline README and organize documentation guides (https://github.com/nordstad/PinViz/pull/54)

## [0.8.0] - 2026-01-10

### Added
- **Raspberry Pi 4 Support** (https://github.com/nordstad/PinViz/pull/52)
  - Complete support for Raspberry Pi 4 Model B with 40-pin GPIO header
  - Board configuration JSON system for easy board addition
  - Factory function `raspberry_pi_4()` with proper documentation
  - Board name aliases: `raspberry_pi_4`, `rpi4`, `pi4`
  - Comprehensive test suite with pinout validation
  - All Pi boards share identical 40-pin GPIO pinout (Pi 2, 3, 4, 5, Zero 2 W)
- **User-Facing Documentation Guides** (https://github.com/nordstad/PinViz/pull/54)
  - Created `guides/` directory for user-facing guides
  - `guides/ADDING_BOARDS.md` - Step-by-step board addition guide for maintainers
  - `guides/DEVICE_CONFIG_GUIDE.md` - Device configuration reference
  - Feature Showcase table in examples documentation linking capabilities to examples

### Changed
- **Streamlined README** (https://github.com/nordstad/PinViz/pull/54)
  - Reduced README from 799 to 171 lines (78.6% smaller)
  - Focus on visual impact: logo, demo GIF, example diagram
  - Essential information only: installation, quick start, features
  - All detailed documentation moved to mkdocs
  - PyPI-compatible image formatting with HTML img tags
- **Improved Wire Routing** (https://github.com/nordstad/PinViz/pull/53)
  - Fixed missing wires in example diagrams
  - Enhanced validation for example command
  - Better wire connection handling to device pins
- **Documentation Organization** (https://github.com/nordstad/PinViz/pull/54)
  - Moved detailed configuration docs from README to mkdocs
  - Updated all documentation links to reference proper locations
  - Enhanced examples page with categorized feature showcase
- **Asset Credits Update**
  - Updated SVG asset credits to Wikimedia Commons (from FreeSVG.org)

### Fixed
- Wire connections to device pins properly aligned (https://github.com/nordstad/PinViz/pull/50)
- Missing wires in example diagrams (https://github.com/nordstad/PinViz/pull/53)
- Board rendering standardization across different board types (https://github.com/nordstad/PinViz/pull/49)

### Improved
- Code quality improvements with better test coverage (https://github.com/nordstad/PinViz/pull/51)
- Refactoring for maintainability
- Configuration file structure

## [0.7.0] - 2026-01-07

### Added
- **Hardware Validation System** (https://github.com/nordstad/PinViz/pull/41)
  - Comprehensive wiring diagram validation with 5 check categories
  - Pin conflict detection (multiple devices on same GPIO)
  - I2C address conflict warnings with device recognition
  - Voltage compatibility checks (3.3V vs 5V protection)
  - GPIO current limit warnings (16mA per pin)
  - Connection validity checks (invalid pins, non-existent devices)
  - `pinviz validate` CLI command with `--strict` mode
  - Automatic validation during `render` command
  - Three severity levels: ERROR, WARNING, INFO
  - Clear, actionable error messages with location context
  - Legal disclaimer for validation limitations
  - 12 comprehensive test cases covering all validation scenarios
  - Detailed documentation in `docs/validation.md`
- **Professional Structured Logging** (https://github.com/nordstad/PinViz/pull/42)
  - `structlog>=24.1.0` integration for observability and debugging
  - Centralized logging configuration in `src/pinviz/logging_config.py`
  - JSON format for machine-readable logs (log aggregation tools)
  - Console format for human-readable output with colors
  - Automatic callsite metadata (file, function, line number)
  - Configurable log levels via `--log-level` flag (DEBUG, INFO, WARNING, ERROR)
  - Configurable log format via `--log-format` flag (json|console)
  - Default WARNING level for minimal noise
  - Logs to stderr to avoid interfering with stdout/pipes
  - 19 new tests for logging configuration and behavior
- **MCP Server Validation Integration** (https://github.com/nordstad/PinViz/pull/43)
  - Automatic hardware validation in `generate_diagram` tool
  - Enhanced response format with validation results
  - Validation status field: "passed", "warning", or "failed"
  - Categorized validation issues (errors, warnings, info)
  - Human-readable validation messages
  - Updated MCP server documentation with validation examples
- Google Analytics tracking for documentation site
- Demo video infrastructure with VHS tape files
- Validation demo video (`scripts/demos/validation_demo.tape`)
- JSON configuration examples in documentation

### Changed
- MCP server builds complete `Diagram` objects using `ConnectionBuilder`
- Documentation index now lists validation, MCP server, and structlog features
- CLI guide includes `validate` command and logging options
- MCP server usage docs include automatic validation section

### Documentation
- Added `docs/validation.md` comprehensive validation guide
- Updated `docs/guide/cli.md` with validate command and logging flags
- Updated `docs/index.md` with new features
- Updated `docs/mcp-server/usage.md` with validation examples
- Added Validation page to User Guide navigation in `mkdocs.yml`

## [0.6.1] - 2025-12-29

### Fixed
- Fix broken demo GIF on PyPI by using absolute GitHub raw URL in README

## [0.6.0] - 2025-12-29

### Added
- Professional wire routing system with intelligent spacing and z-order
  (https://github.com/nordstad/PinViz/pull/40)
- Comprehensive wire routing documentation in `docs/wire-routing.md`
- Wire spacing test suite with 5 tests for routing quality assurance
- Collision detection for dynamic rail position adjustment
- Configurable wire spacing parameters (`wire_spacing`, `bundle_spacing`)

### Changed
- Wire routing now uses horizontal rail spreading (8px spacing by default)
- Vertical fan-out at GPIO header for clear visual separation
- Three-level z-order sorting ensures all wires remain visible
- Wires from right GPIO column now properly rendered on top
- Improved wire bundling with natural grouping by destination
- Enhanced `LayoutConfig` with new spacing parameters

### Fixed
- Wire overlap issues eliminated through intelligent spacing
- Wires from even-numbered pins no longer hidden under odd-numbered pins
- Improved wire visibility in dense diagrams
- Deterministic routing for consistent version control

## [0.5.1] - 2025-12-28

### Dependencies
- Bump ruff from 0.14.6 to 0.14.7 (https://github.com/nordstad/PinViz/pull/28)
- Bump beautifulsoup4 from 4.14.2 to 4.14.3 (https://github.com/nordstad/PinViz/pull/29)
- Bump ruff from 0.14.7 to 0.14.8 (https://github.com/nordstad/PinViz/pull/30)
- Bump pytest from 9.0.1 to 9.0.2 (https://github.com/nordstad/PinViz/pull/31)
- Bump mcp from 1.22.0 to 1.23.1 (https://github.com/nordstad/PinViz/pull/32)
- Bump mkdocstrings-python from 2.0.0 to 2.0.1 (https://github.com/nordstad/PinViz/pull/33)
- Bump mcp from 1.23.1 to 1.24.0 (https://github.com/nordstad/PinViz/pull/35)
- Bump ruff from 0.14.8 to 0.14.9 (https://github.com/nordstad/PinViz/pull/34)
- Bump ruff from 0.14.9 to 0.14.10 (https://github.com/nordstad/PinViz/pull/38)
- Bump mkdocs-material from 9.7.0 to 9.7.1 (https://github.com/nordstad/PinViz/pull/37)
- Bump mcp from 1.24.0 to 1.25.0 (https://github.com/nordstad/PinViz/pull/36)
- bump version (https://github.com/nordstad/PinViz/pull/39)

## [0.5.0] - 2025-11-30

### Added
- Add documentation links to all built-in device types (https://github.com/nordstad/PinViz/pull/27)

### Changed
- Improve README.md structure and user experience (https://github.com/nordstad/PinViz/pull/26)

### Fixed
- Fix docstring formatting: Change 'Example:' to 'Examples:' (https://github.com/nordstad/PinViz/pull/25)

### Dependencies
- Bump ruff from 0.14.5 to 0.14.6 (https://github.com/nordstad/PinViz/pull/22)
- Bump mkdocstrings from 0.30.1 to 1.0.0 (https://github.com/nordstad/PinViz/pull/24)
- Bump mkdocstrings-python from 1.19.0 to 2.0.0 (https://github.com/nordstad/PinViz/pull/23)

## [0.4.0] - 2025-11-25

### Added
- Raspberry Pi Zero 2 W board support with full 40-pin GPIO header
- Custom Pi Zero SVG board asset (scaled 1.6x for optimal visibility)
- Board-specific pin sizing for better clarity on compact boards
- Accurate pin positions extracted and scaled from official dimensions
- All standard pin roles supported (GPIO, I2C, SPI, UART, PWM, power, ground)

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

[Unreleased]: https://github.com/nordstad/PinViz/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/nordstad/PinViz/compare/v0.8.0...v0.8.0
[0.7.0]: https://github.com/nordstad/PinViz/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/nordstad/PinViz/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/nordstad/PinViz/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/nordstad/PinViz/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/nordstad/PinViz/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/nordstad/PinViz/compare/v0.3.0...v0.4.0
[0.1.5]: https://github.com/nordstad/PinViz/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/nordstad/PinViz/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/nordstad/PinViz/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/nordstad/PinViz/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/nordstad/PinViz/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nordstad/PinViz/releases/tag/v0.1.0
