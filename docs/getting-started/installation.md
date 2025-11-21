# Installation

PinViz requires Python 3.12 or later.

## For CLI Usage (Recommended)

Install as a standalone tool with global access to the CLI using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install pinviz
```

After installation, `pinviz` will be available globally in your terminal.

**Alternative:** You can also use `pipx` for isolated CLI tool installations:

```bash
pipx install pinviz
```

## As a Project Dependency

If you want to use PinViz as a library in your Python project:

```bash
# Using uv
uv add pinviz

# Using pip
pip install pinviz
```

!!! note
    If you install with `uv add`, the CLI tool will only be available via `uv run pinviz`. For direct CLI access, use `uv tool install` instead.

## Verify Installation

Check that PinViz is installed correctly:

```bash
pinviz --help
```

You should see the command-line help output.

!!! tip
    If you installed with `uv add`, use `uv run pinviz --help` instead.

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
