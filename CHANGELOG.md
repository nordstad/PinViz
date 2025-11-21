# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
