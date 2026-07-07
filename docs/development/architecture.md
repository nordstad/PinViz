# Architecture

PinViz architecture overview.

## Design Patterns

1. **Separation of concerns**: Model → Layout → Rendering pipeline
2. **Factory pattern**: Boards and devices use factory functions
3. **Schema-first validation**: Pydantic schemas validate config before runtime objects are built

## Core Modules

- `model.py` - Core data structures
- `boards.py` - Board templates
- `devices/` - Device registry, loader, and template catalog
- `config_loader.py` - Configuration parsing
- `layout/` - Layout engine and routing components
- `render_svg.py` - SVG rendering
- `cli/` - Command-line interface commands and output utilities

See [CLAUDE.md](https://github.com/nordstad/PinViz/blob/main/CLAUDE.md) for detailed architectural documentation.
