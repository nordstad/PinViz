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

- Add tests for new features
- Ensure existing tests still pass
- Aim for high test coverage (85%+)
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

```python
def test_device_creation():
    # Arrange
    name = "Test Device"
    pins = [DevicePin("VCC", PinRole.V3_3)]

    # Act
    device = Device(name=name, pins=pins)

    # Assert
    assert device.name == name
    assert len(device.pins) == 1
```

### Adding Device Templates

To add a new device template:

1. Add the factory function to `src/pinviz/devices/__init__.py`
2. Register it in the `DEVICE_REGISTRY`
3. Add tests to `tests/test_devices.py`
4. Update documentation in `docs/guide/examples.md`

Example:

```python
def my_sensor() -> Device:
    """Create a My Sensor device template."""
    return Device(
        name="My Sensor",
        width=80.0,
        height=60.0,
        color="#4A90E2",
        pins=[
            DevicePin("VCC", PinRole.V3_3, position=(5.0, 10.0)),
            DevicePin("GND", PinRole.GND, position=(5.0, 20.0)),
            DevicePin("SDA", PinRole.I2C_SDA, position=(5.0, 30.0)),
            DevicePin("SCL", PinRole.I2C_SCL, position=(5.0, 40.0)),
        ]
    )

# Register in DEVICE_REGISTRY
DEVICE_REGISTRY.register("my_sensor", my_sensor, "My Sensor I2C Module")
```

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

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create and push a git tag
4. Build and publish to PyPI
5. Create GitHub release

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
