# CLI Development Guide

The CLI uses a modern, modular architecture built with **Typer** (type-hint-based CLI) and **Rich** (beautiful terminal output).

## CLI Structure

```text
src/pinviz/cli/
├── __init__.py           # Main Typer app, global options, version
├── config.py             # CLI configuration with TOML support
├── context.py            # AppContext for dependency injection
├── output.py             # Rich output helpers + JSON schemas
└── commands/
    ├── __init__.py       # Command exports
    ├── render.py         # Render diagram from config
    ├── validate.py       # Validate diagram + validate-devices
    ├── example.py        # Generate built-in examples
    ├── list.py           # List available templates
    ├── device.py         # Interactive device wizard
    ├── config.py         # Config management (show, init, edit, path)
    └── completion.py     # Shell completion (install, show, uninstall)
```

## Key Features

- **Type-safe CLI**: Uses Python type hints for automatic validation
- **Rich output**: Progress indicators, tables, panels, and color-coded messages
- **JSON output**: All commands support `--json` flag for machine-readable output
- **Configuration management**: TOML config file support with `pinviz config` commands
- **Shell completion**: Auto-complete for bash/zsh/fish shells
- **Modular commands**: Each command in a separate file for maintainability
- **Global options**: `--log-level`, `--log-format`, `--version` available for all commands
- **Consistent error handling**: Rich tracebacks with `show_locals` support

## Adding a New Command

### Step 1: Create Command File

Create a new file in `src/pinviz/cli/commands/` (e.g., `mycommand.py`):

```python
import typer
from typing import Annotated
from rich.console import Console

console = Console()

def my_command(
    input_file: Annotated[str, typer.Argument(help="Input file path")],
    output: Annotated[str | None, typer.Option("-o", "--output", help="Output path")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
) -> None:
    """
    Brief description of what this command does.

    Longer description with more details about usage and behavior.
    """
    console.print(f"Processing {input_file}...")
    # Command implementation
```

### Step 2: Register Command

In `src/pinviz/cli/__init__.py`:

```python
from .commands import mycommand

app.command(name="my-command")(mycommand.my_command)
```

### Step 3: Add Tests

In `tests/test_cli.py`:

```python
def test_my_command(cli_runner):
    """Test my-command functionality."""
    result = cli_runner.invoke(app, ["my-command", "input.txt"])
    assert result.exit_code == 0
```

## Testing Commands

Use Typer's `CliRunner` for testing:

```python
from typer.testing import CliRunner
from pinviz.cli import app

runner = CliRunner()
result = runner.invoke(app, ["render", "config.yaml"])
assert result.exit_code == 0
assert "Rendering diagram" in result.output
```

## JSON Output

All commands support `--json` flag for machine-readable output:

```bash
# Render command
pinviz render config.yaml --json
# Output: {"status": "success", "output_path": "config.svg", "validation": {...}}

# Validate command
pinviz validate config.yaml --json
# Output: {"status": "success", "validation": {...}, "issues": [...]}

# List command
pinviz list --json
# Output: {"status": "success", "boards": [...], "devices": [...], "examples": [...]}

# Example command
pinviz example bh1750 --json
# Output: {"status": "success", "example_name": "bh1750", "output_path": "out/bh1750.svg"}
```

### JSON Schemas

All JSON output is validated using Pydantic models in `src/pinviz/cli/output.py`:

- `RenderOutputJson` - Render command output
- `ValidateOutputJson` - Validate command output
- `ValidateDevicesOutputJson` - Device validation output
- `ExampleOutputJson` - Example command output
- `ListOutputJson` - List command output

## Configuration Management

PinViz uses a TOML configuration file with proper precedence:

1. **CLI arguments** (highest priority)
2. **Environment variables** (`PINVIZ_*` prefix)
3. **Config file** (`~/.config/pinviz/config.toml`)
4. **Defaults** (lowest priority)

```bash
# Create default config
pinviz config init

# View current config
pinviz config show

# Get config file path
pinviz config path

# Edit config file
pinviz config edit
```

**Example config.toml:**

```toml
# Logging verbosity: DEBUG, INFO, WARNING, ERROR
log_level = "WARNING"

# Log output format: console or json
log_format = "console"

# Default output directory
output_dir = "./out"
```

## Shell Completion

Install shell completion for better command-line experience:

```bash
# Auto-detect shell and install
pinviz completion install

# Specify shell explicitly
pinviz completion install --shell bash
pinviz completion install --shell zsh
pinviz completion install --shell fish

# Show completion script
pinviz completion show

# Uninstall completion
pinviz completion uninstall
```
