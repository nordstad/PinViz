# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]




## [0.13.0] - 2026-02-11

### Added
- feat: Add named color support for devices and connections (https://github.com/nordstad/PinViz/pull/156)

### Changed
- chore(deps): bump cryptography from 46.0.3 to 46.0.5 (https://github.com/nordstad/PinViz/pull/154)

## [0.13.0] - 2026-02-11

### Added
- Named color support for devices and connections - can now use color names like "red", "green", "blue" in addition to hex codes (#155)
  - 15 named colors available: red, green, blue, yellow, orange, purple, black, white, gray, brown, pink, cyan, magenta, lime, turquoise
  - Color names are case-insensitive
  - Whitespace is automatically trimmed from color inputs
  - Invalid colors fall back to default gracefully
  - Works for both device colors and wire colors
  - Backward compatible with existing hex code configurations
  - Code quality score: 9.5/10 (comprehensive code review passed)

### Changed
- Schema validation now accepts both named colors and hex codes for device and connection colors
- Color resolution utility with robust error handling and fallback behavior
- Documentation updated with named color examples and reference table

## [0.12.1] - 2026-02-09

### Changed
- chore(deps): bump rich from 14.2.0 to 14.3.2 (#144, #148)
- chore(deps): bump python-multipart from 0.0.20 to 0.0.22 (#147)
- chore(deps): bump mcp from 1.25.0 to 1.26.0 (#145)
- chore(deps-dev): bump hypothesis from 6.150.2 to 6.151.5 (#142, #149, #152)
- chore(deps-dev): bump ruff from 0.14.13 to 0.15.0 (#146, #150)
- chore(deps-dev): bump mkdocstrings from 1.0.0 to 1.0.3 (#143, #153)
- chore(deps-dev): update uv-build requirement (#151)

### Fixed
- fix: update enums to use StrEnum for ruff 0.15.0 compatibility (#150)

## [0.12.0] - 2026-01-25

### Added
- feat: Add dark mode support for diagrams (https://github.com/nordstad/PinViz/pull/141)

### Fixed
- fix: Consistent device pin spacing across all devices (https://github.com/nordstad/PinViz/pull/140)

## [0.12.0] - 2026-01-25

### Added
- feat: Dark mode support for diagrams (https://github.com/nordstad/PinViz/pull/141)
  - New theme system with LIGHT and DARK color schemes
  - Dark canvas background (#1E1E1E) optimized for dark UIs
  - Light text and stroke colors for visibility in dark mode
  - Pin labels inverted for better contrast (white bg, black text in dark mode)
  - Wire colors preserved to maintain electrical conventions
  - Theme support in YAML config: `theme: "dark"`
  - CLI `--theme` flag to override config: `pinviz render config.yaml --theme dark`
  - New examples: `bh1750_dark.yaml`, `pico_led_dark.yaml`, `i2c_spi_dark.yaml`
  - Comprehensive themes guide in documentation
  - 38 new tests (theme unit + integration tests)
  - 8 CLI tests for --theme flag coverage
  - Perfect for dark-themed documentation, presentations, and GitHub dark mode

## [0.11.2] - 2026-01-25

### Changed
- feat: Dynamic halo color for light-colored wires (https://github.com/nordstad/PinViz/pull/139)

## [0.11.2] - 2026-01-25

### Added
- feat: Dynamic halo color for light-colored wires (https://github.com/nordstad/PinViz/pull/139)
  - Automatic visibility detection using WCAG 2.0 luminance calculation
  - Light wires (luminance > 0.7) get dark gray halos for visibility
  - Dark/medium wires keep traditional white halos
  - No configuration needed - works automatically for all wire colors
  - Includes comprehensive test suite with 19 new tests
  - New example: `examples/wire_visibility.yaml` showcasing the feature

## [0.11.1] - 2026-01-25

### Changed
- chore(deps-dev): bump hypothesis from 6.150.0 to 6.150.2 (https://github.com/nordstad/PinViz/pull/136)
- chore(deps-dev): bump ruff from 0.14.11 to 0.14.13 (https://github.com/nordstad/PinViz/pull/137)

### Fixed
- fix: correct IR LED Ring pin name from CTRL to EN (https://github.com/nordstad/PinViz/pull/138)

## [0.11.0] - 2026-01-18

### Added
- feat: Add ConnectionGraph utility class for topology analysis (#72) (https://github.com/nordstad/PinViz/pull/91)
- [Phase 1.5] Add Phase 1 Integration Tests (https://github.com/nordstad/PinViz/pull/94)
- fix: Sync MCP module version with package metadata and add Codecov badge (https://github.com/nordstad/PinViz/pull/95)
- feat: Add Pydantic schemas for multi-level connections (Phase 2.1) (https://github.com/nordstad/PinViz/pull/97)
- docs: Add supported boards table to README (https://github.com/nordstad/PinViz/pull/99)
- [Phase 3.1] Add multi-level connection examples (https://github.com/nordstad/PinViz/pull/102)
- feat: Implement multi-tier device layout positioning (Phase 3.2) (https://github.com/nordstad/PinViz/pull/103)
- feat: Implement canvas sizing and layout validation (Phase 3.3) (#81) (https://github.com/nordstad/PinViz/pull/104)
- test: Add multi-tier canvas sizing integration test (Phase 3.4) (https://github.com/nordstad/PinViz/pull/105)
- [Phase 4.2] Add Comprehensive Integration Tests for Multi-Level Features (https://github.com/nordstad/PinViz/pull/107)
- feat: Add professional example diagrams for Phase 4.3 (https://github.com/nordstad/PinViz/pull/108)
- feat: Add smart vertical device positioning based on pin connections (https://github.com/nordstad/PinViz/pull/113)
- fix: Eliminate wire stubs and add validation (fixes #112) (https://github.com/nordstad/PinViz/pull/114)
- docs: Add multi-tier diagram examples to documentation (fixes #115) (https://github.com/nordstad/PinViz/pull/116)
- docs: Add comprehensive multi-level device support documentation (fixes #86) (https://github.com/nordstad/PinViz/pull/117)
- fix: add bounds checking to wire conflict resolution (fixes #119) (https://github.com/nordstad/PinViz/pull/129)

### Changed
- feat: Extend Connection model for device-to-device connections (https://github.com/nordstad/PinViz/pull/90)
- chore(deps): bump urllib3 from 2.5.0 to 2.6.3 (https://github.com/nordstad/PinViz/pull/92)
- [Phase 1.3] Pin Compatibility Matrix and Validation (https://github.com/nordstad/PinViz/pull/93)
- feat: Update ConfigLoader for multi-level connections (Phase 2.2) (https://github.com/nordstad/PinViz/pull/98)
- [Phase 2.3] Enhance CLI Validation Command (https://github.com/nordstad/PinViz/pull/100)
- feat: Enhance validate command with graph visualization (#78) (https://github.com/nordstad/PinViz/pull/101)
- [Phase 4.1] Comprehensive Integration Tests for Multi-Tier Layout (https://github.com/nordstad/PinViz/pull/106)

### Fixed
- Potential fix for code scanning alert no. 8: Workflow does not contain permissions (https://github.com/nordstad/PinViz/pull/70)
- fix: centralize magic numbers into organized constant classes (fixes #121) (https://github.com/nordstad/PinViz/pull/128)
- perf: optimize device lookups and wire conflict detection (fixes #118, #122) (https://github.com/nordstad/PinViz/pull/130)
- perf: optimize wire conflict detection with early exit (fixes #122) (https://github.com/nordstad/PinViz/pull/131)
- fix: improve error handling and validation messages (fixes #123, #124) (https://github.com/nordstad/PinViz/pull/132)
- refactor: extract pin position calculation methods (fixes #120) (https://github.com/nordstad/PinViz/pull/133)
- feat: decouple layout and rendering via LayoutResult (fixes #125) (https://github.com/nordstad/PinViz/pull/134)
- feat: make device registry instantiable for better testing (fixes #126) (https://github.com/nordstad/PinViz/pull/135)

## [0.10.0] - 2026-01-14

### Changed
- refactor: simplify CLI by removing config and completion bloat (https://github.com/nordstad/PinViz/pull/69)

## [0.10.0] - 2026-01-14

### Removed
- **BREAKING**: Removed config command group (`pinviz config show|path|init|edit`)
- **BREAKING**: Removed shell completion command group (`pinviz completion install|show|uninstall`)
- **BREAKING**: Removed global options: `--log-level` and `--log-format`
- **BREAKING**: Removed TOML configuration file support
- **BREAKING**: Logging is now fixed to ERROR-only output (no verbose option)

### Changed
- Simplified CLI to focus on core functionality (render, validate, example, list, add-device)
- CLI output is now quiet by default, showing only essential messages

### Documentation
- Updated README with link to examples gallery

### Migration Guide
- **Config files**: No longer needed or supported - the tool works without configuration
- **Shell completions**: Typer provides built-in completion support if needed
- **Logging**: If you need debug output, you'll need to modify the source code (rare use case)
- No action needed for most users - the core commands work the same way


## [0.9.2] - 2026-01-13

### Added
- fix: address critical and high-priority code quality issues (https://github.com/nordstad/PinViz/pull/65)
- fix: add pin validation and consolidate exception handling (https://github.com/nordstad/PinViz/pull/66)
- feat: add contribution message to device wizard (https://github.com/nordstad/PinViz/pull/68)

### Fixed
- fix: correct questionary Choice parameter order in device wizard (https://github.com/nordstad/PinViz/pull/67)

## [0.9.1] - 2026-01-13

### Added
- feat: Add smart pin role suggestions to add-device wizard (https://github.com/nordstad/PinViz/pull/64)

### Fixed
- fix: prevent traceback when exiting device wizard (https://github.com/nordstad/PinViz/pull/63)

## [0.9.0] - 2026-01-13

### Added
- **Raspberry Pi Pico Support** - Raspberry Pi Pico board support with horizontal pin layout (https://github.com/nordstad/PinViz/pull/61)
  - Complete support for Raspberry Pi Pico with dual 20-pin headers (40 pins total)
  - New dual-header layout system for boards with GPIO pins on multiple edges
  - Horizontal pin positioning (single row per header) vs traditional vertical columns
  - Reversed pin order on top header (pin 20 on left, pin 1 on right)
  - Factory function `raspberry_pi_pico()` with comprehensive documentation
  - Board name aliases: `raspberry_pi_pico`, `pico`
  - JSON configuration in `board_configs/raspberry_pi_pico.json`
  - 15 new comprehensive tests for Pico board functionality
  - 4 new tests for Pico board alias support
  - Example diagrams: `examples/pico_led.yaml`, `examples/pico_bme280.yaml`, and `examples/pico_leds_with_specs.yaml`
  - Documentation for dual-sided board configuration in `CLAUDE.md`
  - Pico multi-LED example with specifications table demonstrating `--show-legend` flag
- **Extended Schema Support** for dual-sided boards (https://github.com/nordstad/PinViz/pull/61)
  - `BoardLayoutConfigSchema` now supports `top_header` and `bottom_header` configurations
  - `BoardPinConfigSchema` includes optional `header` field for pin placement
  - Board detection logic automatically identifies dual-header vs single-header layouts
  - Pattern established for future boards (ESP32, Arduino Nano, etc.)
- **MCP Server Support** for Raspberry Pi Pico and Pi 4 (https://github.com/nordstad/PinViz/pull/61)
  - Added board aliases to MCP parser: `pico`, `raspberry pi pico`, `rpi pico` → `raspberry_pi_pico`
  - Added board aliases for Pi 4: `pi4`, `rpi4`, `raspberry pi 4` → `raspberry_pi_4`
  - 5 new parser tests for board alias recognition (Pi 4 and Pico)
  - Updated MCP documentation with all supported board aliases
  - MCP server now supports natural language prompts like "Connect LED to pico"
- **Dynamic Board Discovery** in CLI list command (https://github.com/nordstad/PinViz/pull/62)
  - Added `get_available_boards()` function that automatically discovers boards from `board_configs/`
  - No need to manually update CLI when adding new boards
  - Automatically displays all boards: Pi 4, Pi 5, and Pico with their aliases

### Changed
- **Improved Wire Colors** in Pico BME280 example for better visibility (https://github.com/nordstad/PinViz/pull/61)
  - Changed I2C wire colors from yellow to blue (#2196F3) and orange (#FF9800)
  - Yellow wires were hard to see against white background
  - New colors provide better contrast and readability in documentation
- **Enhanced Exception Handling** in completion commands (https://github.com/nordstad/PinViz/pull/62)
  - Replaced broad `except Exception` with specific exception types
  - Added `subprocess.SubprocessError`, `FileNotFoundError`, `PermissionError`, `OSError`
  - Provides actionable error messages with troubleshooting hints
- **Dependency Updates**
  - Bump pydantic from 2.12.4 to 2.12.5 (https://github.com/nordstad/PinViz/pull/57)
  - Bump ruff from 0.14.10 to 0.14.11 (https://github.com/nordstad/PinViz/pull/58)
  - Bump platformdirs from 4.5.0 to 4.5.1 (https://github.com/nordstad/PinViz/pull/59)

### Fixed
- **Layout Spacing Issues** - Fixed title overlap and specs table positioning (https://github.com/nordstad/PinViz/pull/61)
  - Dynamic board margin calculation based on whether title is shown
  - Title now has proper spacing (title_height + title_margin) above board and wires
  - Specs table positioned relative to bottommost device with configurable margin
  - Added `specs_table_top_margin` parameter to LayoutConfig (default: 30px)
  - Renamed `board_margin_top` to `board_margin_top_base` with dynamic calculation
  - Prevents wires from overlapping with title text
  - Prevents devices from being too close to specifications table
  - All layout spacing now calculated dynamically for proper visual separation

### Tests
- **Comprehensive ValidationResult Tests** (https://github.com/nordstad/PinViz/pull/62)
  - Added 9 new test cases for `ValidationResult` class
  - Tests cover success/error/warning scenarios in strict and non-strict modes
  - Tests validate console and JSON output formatting
  - Increased total test count from 33 to 41 tests


## [0.8.1] - 2026-01-11

### Changed
- Move show_legend to CLI flag and improve specs table layout (https://github.com/nordstad/PinViz/pull/55)
- Modernize CLI with Typer + Rich (https://github.com/nordstad/PinViz/pull/56)

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

[Unreleased]: https://github.com/nordstad/PinViz/compare/v0.13.0...HEAD
[0.13.0]: https://github.com/nordstad/PinViz/compare/v0.13.0...v0.13.0
[0.12.1]: https://github.com/nordstad/PinViz/compare/v0.12.1...v0.12.1
[0.12.0]: https://github.com/nordstad/PinViz/compare/v0.12.0...v0.12.0
[0.11.2]: https://github.com/nordstad/PinViz/compare/v0.11.2...v0.11.2
[0.11.1]: https://github.com/nordstad/PinViz/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/nordstad/PinViz/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/nordstad/PinViz/compare/v0.10.0...v0.10.0
[0.9.2]: https://github.com/nordstad/PinViz/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/nordstad/PinViz/compare/v0.9.0...v0.9.1
[0.8.1]: https://github.com/nordstad/PinViz/compare/v0.8.0...v0.8.1
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
