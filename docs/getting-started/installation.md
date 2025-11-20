# Installation

PinViz requires Python 3.12 or later.

## Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is the fastest Python package installer:

```bash
uv add pinviz
```

## Using pip

```bash
pip install pinviz
```

## Using pipx

For installing CLI tools in isolated environments:

```bash
pipx install pinviz
```

## Verify Installation

Check that PinViz is installed correctly:

```bash
pinviz --help
```

You should see the command-line help output.

## Development Installation

For contributing to PinViz, clone the repository and install in development mode:

```bash
# Clone repository
git clone https://github.com/nordstad/PinViz.git
cd PinViz

# Install dependencies
uv sync --dev

# Verify installation
uv run pinviz --help
```

## Requirements

- Python 3.12 or later
- Dependencies:
    - `svgwrite>=1.4.3` - SVG generation
    - `pyyaml>=6.0.1` - YAML configuration parsing

All dependencies are installed automatically when you install PinViz.

## Next Steps

- Continue to the [Quick Start Tutorial](quickstart.md)
- Learn about [CLI Usage](../guide/cli.md)
- Explore the [Python API](../guide/python-api.md)
