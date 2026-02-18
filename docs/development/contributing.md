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

## Adding Device Configurations

When contributing new device configurations:

1. Use the interactive wizard: `uv run pinviz add-device`
2. Validate your configuration: `uv run pinviz validate-devices`
3. Test loading the device programmatically:
   ```python
   from pinviz.devices import get_registry
   registry = get_registry()
   device = registry.create('your_device_id')
   ```
4. Ensure validation passes with no errors

The device validator checks:
- Schema compliance (required fields, valid types)
- Pin configuration correctness
- I2C address format (if applicable)
- No duplicate device IDs

**Example workflow:**

```bash
# Create device configuration interactively
uv run pinviz add-device

# Validate all device configs
uv run pinviz validate-devices

# Run tests to ensure nothing broke
uv run pytest
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. For device configs, run `pinviz validate-devices`
6. Submit a pull request

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

## Docs Release Checklist

Run these checks before publishing docs or cutting a release that includes documentation changes:

```bash
# 1. Build docs — confirms no broken nav or missing pages
uv run mkdocs build --strict

# 2. Check CLI docs are in sync with pinviz --help output
uv run python scripts/check_cli_docs.py

# 3. Manually verify any board/device list pages match pinviz list output
pinviz list
```

Manual checks:

- [ ] `docs/guide/cli.md` board list matches `pinviz list` output
- [ ] `docs/guide/yaml-config.md` board list matches `pinviz list` output
- [ ] `docs/troubleshooting.md` board alias table matches `pinviz list` output
- [ ] `CHANGELOG.md` has an entry for any user-facing changes in this release
- [ ] New features have corresponding docs pages added to `mkdocs.yml` nav
- [ ] Any new CLI commands or options are documented in `docs/guide/cli.md`

The `check_cli_docs.py` script catches drift between `pinviz --help` and `cli.md`
automatically. It exits 1 if any documented options are missing from the docs.
