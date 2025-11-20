# Contributing

Contributions are welcome! This guide will help you get started.

## Development Setup

```bash
# Clone repository
git clone https://github.com/nordstad/PinViz.git
cd PinViz

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .
```

## Code Quality

All code must pass:

- Ruff linting and formatting
- All unit tests
- Type checking

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Documentation

Update documentation when adding new features. Documentation is built with MkDocs.

```bash
# Install docs dependencies
uv sync --group docs

# Serve docs locally
uv run mkdocs serve

# Build docs
uv run mkdocs build
```
