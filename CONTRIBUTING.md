# Contributing to PinViz

Thank you for your interest in contributing to PinViz! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to create a welcoming environment for all contributors.

## Development Setup

### Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- Git

### Getting Started

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/nordstad/PinViz.git
   cd PinViz
   ```

3. **Install dependencies**:
   ```bash
   uv sync --dev
   ```

4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests

Run the test suite to ensure everything works:

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=pinviz --cov-report=term

# Run tests in verbose mode
uv run pytest -v
```

### Code Quality

All code must pass linting and formatting checks:

```bash
# Check code with ruff
uv run ruff check .

# Format code with ruff
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .
```

### Type Checking

PinViz uses type annotations. Ensure your code includes proper type hints:

```python
def example_function(name: str, count: int) -> list[str]:
    return [name] * count
```

### Dependency Management

PinViz uses `uv.lock` to ensure reproducible builds. GitHub Dependabot monitors this file for security updates.

**Important**: Always commit the updated `uv.lock` file when modifying dependencies in `pyproject.toml`.

#### Adding/Updating Dependencies

When you modify dependencies in `pyproject.toml`:

```bash
# Update the lock file
uv lock

# Sync your environment
uv sync --dev

# Verify the lock file is in sync
uv lock --check
```

#### Pre-commit Hooks (Recommended)

Set up pre-commit hooks to automatically validate `uv.lock`:

```bash
# Install pre-commit hooks
uvx pre-commit install

# Test the hooks
uvx pre-commit run --all-files
```

The pre-commit hooks will:

- Automatically update `uv.lock` if out of sync
- Run ruff linting and formatting
- Check for common issues

#### CI Validation

The CI pipeline automatically checks that `uv.lock` is in sync with `pyproject.toml`. If you get a CI failure about the lock file:

1. Run `uv lock` locally
2. Commit the updated `uv.lock`
3. Push the changes

## Contribution Guidelines

### What We're Looking For

- Bug fixes
- New device templates
- New board support
- Documentation improvements
- Performance improvements
- Test coverage improvements
- Example diagrams

### Before You Start

- **Check existing issues** to see if your idea is already being discussed
- **Open an issue** to discuss new features before implementing them
- **Keep changes focused** - one feature or fix per pull request

### Code Style

- Follow existing code patterns and conventions
- Use descriptive variable and function names
- Add docstrings to public functions and classes
- Keep functions small and focused
- Avoid unnecessary complexity

### Docstring Format

Use Google-style docstrings:

```python
def create_device(name: str, pins: list[DevicePin]) -> Device:
    """
    Create a new device instance.

    Args:
        name: The device name
        pins: List of device pins

    Returns:
        Device instance

    Raises:
        ValueError: If name is empty
    """
    if not name:
        raise ValueError("Device name cannot be empty")
    return Device(name=name, pins=pins)
```

### Writing Tests

All tests should follow these guidelines:

- Add tests for new features
- Ensure existing tests still pass
- Aim for high test coverage (85%+)
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

#### Test Structure Guidelines

PinViz uses a consistent test structure across the codebase. Follow these patterns:

**Use test classes when:**

1. Testing a specific class from the source code
2. Grouping related tests that share common setup or test a coherent feature area
3. Tests need shared fixtures or setup methods

**Use plain test functions when:**

1. Testing simple, independent module-level functions
2. Each test is self-contained and doesn't benefit from grouping
3. Testing CLI commands or straightforward integrations

#### Test Class Example

```python
"""Tests for the PinAssigner class."""

from pinviz.mcp.pin_assignment import PinAssigner, PinAssignment
from pinviz.model import PinRole


class TestPinAssigner:
    """Test suite for PinAssigner class."""

    def test_initialization(self):
        """Test that assigner initializes correctly."""
        # Arrange & Act
        assigner = PinAssigner()

        # Assert
        assert isinstance(assigner.state, PinAllocationState)
        assert len(assigner.assignments) == 0

    def test_single_i2c_device(self):
        """Test assigning pins for a single I2C device."""
        # Arrange
        assigner = PinAssigner()
        device = {
            "name": "BME280 Sensor",
            "protocols": ["I2C"],
            "pins": [
                {"name": "VCC", "role": "3V3"},
                {"name": "GND", "role": "GND"},
            ],
        }

        # Act
        assignments, warnings = assigner.assign_pins([device])

        # Assert
        assert len(assignments) == 2
        assert len(warnings) == 0
```

#### Plain Function Example

```python
"""Tests for device factory functions."""

from pinviz import devices
from pinviz.model import PinRole


def test_bh1750_creation():
    """Test creating a BH1750 light sensor device."""
    # Arrange & Act
    device = devices.bh1750_light_sensor()

    # Assert
    assert device.name == "BH1750"
    assert device.width == 60.0
    assert device.height == 50.0


def test_bh1750_has_correct_pins():
    """Test BH1750 device has all required pins."""
    # Arrange & Act
    device = devices.bh1750_light_sensor()

    # Assert
    assert len(device.pins) == 4
    pin_names = [p.name for p in device.pins]
    assert "VCC" in pin_names
    assert "GND" in pin_names
```

#### Required Documentation

Every test file must include:

1. **Module docstring** - Describe what's being tested
2. **Class docstrings** - For test classes, describe the test suite purpose
3. **Function docstrings** - For each test, describe what behavior is verified

Example module docstring:

```python
"""Tests for wire routing spacing and non-overlap guarantees.

This module verifies that:
- Wires maintain minimum spacing when routed in parallel
- Vertical rails are properly separated
- Multiple wires from the same pin don't overlap
"""
```

#### Test Organization

- **Group by feature**: Related tests should be in the same test class
- **Logical ordering**: Arrange tests from simple to complex
- **One assertion focus**: Each test should verify one specific behavior
- **Descriptive names**: Test names should clearly state what they verify

### Adding New Devices

PinViz uses a JSON-based device configuration system with smart defaults. Creating a new device takes about 5 minutes and requires **68% less configuration** compared to the old Python approach.

#### Quick Steps

1. **Create JSON file** in appropriate category folder (e.g., `src/pinviz/device_configs/sensors/bme280.json`)
2. **Define minimal required fields** (id, name, category, pins)
3. **Let smart defaults handle** positions, dimensions, and colors
4. **Test and validate** your device

#### Example Device Configuration

```json
{
  "id": "bme280",
  "name": "BME280 Environmental Sensor",
  "category": "sensors",
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"},
    {"name": "SCL", "role": "I2C_SCL"},
    {"name": "SDA", "role": "I2C_SDA"}
  ],
  "i2c_address": "0x76",
  "datasheet_url": "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf",
  "description": "Precision sensor for pressure, temperature and humidity",
  "notes": "Default I2C address is 0x76, can be changed to 0x77"
}
```

**That's it!** No manual coordinates, no complex calculations - just list your pins.

#### Available Categories

Choose the appropriate category for your device:

- `sensors` - Temperature, light, pressure, motion sensors (color: turquoise)
- `displays` - LCDs, OLEDs, e-paper displays (color: blue)
- `leds` - Individual LEDs, LED strips, rings (color: red)
- `actuators` - Motors, servos, relays (color: orange)
- `io` - Buttons, switches, encoders (color: gray)
- `generic` - Generic I2C/SPI/UART devices (color: gray)

#### Smart Defaults

The device loader automatically provides:

- **Pin positions**: Vertical layout (top to bottom) or horizontal layout (left to right)
- **Device dimensions**: Auto-sized to fit all pins with padding
- **Colors**: Category-based defaults (see categories above)
- **Wire colors**: Based on pin roles (I2C=yellow, SPI=cyan, power=red, ground=black)

#### Device Submission Checklist

Before submitting your device, ensure:

- [ ] Created JSON config in appropriate category folder (`device_configs/{category}/your-device.json`)
- [ ] Used minimal config (let smart defaults work)
- [ ] Added `i2c_address` field (if applicable)
- [ ] Added `datasheet_url` with link to manufacturer datasheet
- [ ] Added `description` explaining what the device does
- [ ] Added `notes` for setup requirements (pull-up resistors, jumpers, etc.)
- [ ] Tested device loads correctly:
  ```bash
  uv run python -c "from pinviz.devices import get_registry; print(get_registry().create('your-device-id').name)"
  ```
- [ ] Created example diagram using the device (optional but encouraged):
  ```bash
  # Create example YAML in examples/ directory
  uv run pinviz render examples/your-device.yaml -o images/your-device.svg
  ```
- [ ] All tests passing: `uv run pytest`
- [ ] Code formatted: `uv run ruff format .` and `uv run ruff check .`

#### Optional: Device Parameters

For device variants (e.g., different LED colors, different chip selects), use parameters:

```json
{
  "id": "led",
  "name": "{color_name} LED",
  "category": "leds",
  "pins": [
    {"name": "+", "role": "GPIO"},
    {"name": "-", "role": "GND"}
  ],
  "parameters": {
    "color_name": {
      "type": "string",
      "default": "Red",
      "description": "LED color for display name"
    }
  }
}
```

Use with: `registry.create('led', color_name='Blue')` → Creates "Blue LED"

#### Need Help?

- **Full guide**: See [plans/DEVICE_CONFIG_GUIDE.md](plans/DEVICE_CONFIG_GUIDE.md) for detailed configuration options
- **Examples**: Browse `src/pinviz/device_configs/` for real device examples
- **Questions**: Open a [GitHub Discussion](https://github.com/nordstad/PinViz/discussions)

### Documentation

- Update documentation for new features
- Add examples for new functionality
- Keep README.md and docs/ in sync
- Use clear, concise language

To build documentation locally:

```bash
# Install docs dependencies
uv sync --group docs

# Serve docs with live reload
uv run mkdocs serve

# Build docs
uv run mkdocs build
```

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass**:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```

2. **Update documentation** if needed

3. **Write a clear commit message**:
   ```
   Add support for DHT22 temperature sensor

   - Add DHT22 device template with 3 pins
   - Register device in device registry
   - Add tests for DHT22 creation
   - Update examples documentation
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub

### Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Include screenshots for visual changes
- Ensure CI passes
- Be responsive to feedback
- Keep PRs reasonably sized

### Pull Request Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass locally
- [ ] Ruff linting passes

## Documentation
- [ ] Documentation updated
- [ ] Examples added/updated (if applicable)

## Related Issues
Closes #123
```

## Release Process

(For maintainers)

The release process is fully automated via GitHub Actions. Simply:

1. **Update version** in `pyproject.toml`

   ```bash
   # Edit pyproject.toml and update version = "0.x.x"
   git add pyproject.toml
   git commit -m "Bump version from 0.x.x to 0.y.y"
   git push origin main
   ```

2. **Create and push a git tag**

   ```bash
   git tag v0.y.y
   git push origin v0.y.y
   ```

3. **GitHub Actions automatically**:
   - Builds and publishes to PyPI
   - Creates GitHub release with auto-generated notes
   - Updates CHANGELOG.md from the release notes
   - Commits CHANGELOG.md back to main
   - Runs post-publish tests

That's it! GitHub releases are the single source of truth, and CHANGELOG.md syncs automatically.

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/nordstad/PinViz/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/nordstad/PinViz/issues)
- **Documentation**: Check the [docs site](https://nordstad.github.io/PinViz/)

## Recognition

Contributors will be recognized in:

- Git commit history
- GitHub contributors page
- Release notes (for significant contributions)

Thank you for contributing to PinViz! 🎉
