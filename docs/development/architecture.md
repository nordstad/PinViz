# Architecture

PinViz architecture overview.

## Design Patterns

1. **Separation of concerns**: Model → Layout → Rendering pipeline
2. **Factory pattern**: Boards and devices use factory functions
3. **Immutable data**: Data classes are immutable

## Core Modules

- `model.py` - Core data structures
- `boards.py` - Board templates
- `devices.py` - Device templates
- `config_loader.py` - Configuration parsing
- `layout.py` - Layout engine
- `render_svg.py` - SVG rendering
- `cli.py` - Command-line interface

See [CLAUDE.md](https://github.com/nordstad/PinViz/blob/main/CLAUDE.md) for detailed architectural documentation.
