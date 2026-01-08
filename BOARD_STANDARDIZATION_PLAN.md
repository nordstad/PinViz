# Board Rendering Standardization Plan

## Problem Analysis

### Current Issues

The Raspberry Pi and Raspberry Pi Zero boards have very different visual styles in the generated diagrams:

- **Pi 5/Pi 2**: Uses `pi2.svg` with width=205.42, height=307.46
- **Pi Zero 2 W**: Uses `pi_zero.svg` with width=465.60, height=931.20 (**2.27x larger!**)
- **Critical scaling problem**: Pi Zero is rendered almost 2.3x larger than Pi 5, despite being physically SMALLER (65mm vs 85mm wide)
- **Inconsistent visual language**: Different colors, details, proportions despite both being Raspberry Pi boards
- **No size normalization**: Board sizes come directly from SVG files, not physical dimensions
- **Future scalability**: No clear pattern for adding new boards (ESP32, Arduino, etc.)

**Physical Reality vs Current Rendering**:

- Pi 5: 85mm × 56mm → rendered at ~205px × 307px (scale: ~2.4px/mm)
- Pi Zero: 65mm × 30mm → rendered at ~466px × 931px (scale: ~7.2px/mm) ❌ **3x too large!**

### Root Causes

1. **External SVG dependency**: Relies on externally created SVG assets with no standardization
2. **No design system**: No unified color palette, dimensions, or style guide
3. **Asset-driven approach**: Board appearance is determined by the SVG file, not by code
4. **Hard-coded positioning**: Pin positions are manually calculated per board with magic numbers

## Proposed Solution

### Approach: Hybrid System

Combine programmatic rendering with optional SVG overlays for a standardized, extensible system.

### Core Components

#### 1. Board Renderer Abstraction

**File**: `src/pinviz/board_renderer.py`

Create a base board rendering system that:

- Defines standard board dimensions and scaling
- Provides consistent colors, styles, and visual elements
- Programmatically renders board shapes, mounting holes, headers
- Allows optional decorative overlays (chips, connectors, etc.)

**Key Classes**:

```python
import drawsvg as draw
from dataclasses import dataclass, field

@dataclass
class BoardStyle:
    """Standardized board visual styling"""
    pcb_color: str = "#006B32"  # Standard PCB green
    pcb_border_color: str = "#004D24"
    header_color: str = "#1A1A1A"  # Black plastic connector
    pad_color: str = "#FFD700"  # Gold pads
    silkscreen_color: str = "#FFFFFF"
    mounting_hole_color: str = "#C0C0C0"
    corner_radius: float = 8.0
    border_width: float = 2.0
    scale_factor: float = 3.0  # px/mm - CRITICAL for consistent sizing

@dataclass
class BoardLayout:
    """Physical board dimensions and features (in mm)"""
    width_mm: float  # Physical width in millimeters
    height_mm: float  # Physical height in millimeters
    header_x_mm: float  # Header position X in mm
    header_y_mm: float  # Header position Y in mm
    header_width_mm: float = 5.08  # Standard 2-row header width (2.54mm * 2)
    header_height_mm: float = 50.8  # 20 pins * 2.54mm spacing
    mounting_holes: list[Point] = field(default_factory=list)  # In mm
    decorative_elements: list[dict] = field(default_factory=list)  # Optional

    @property
    def width_px(self) -> float:
        """Width in SVG pixels (scaled)"""
        return self.width_mm * 3.0  # Standard scale factor

    @property
    def height_px(self) -> float:
        """Height in SVG pixels (scaled)"""
        return self.height_mm * 3.0

class BoardRenderer:
    """Programmatic board rendering with consistent styling using drawsvg"""

    def __init__(self, style: BoardStyle):
        self.style = style

    def render_board(self, board: Board, x: float, y: float) -> draw.Group:
        """Render a standardized board representation"""
        group = draw.Group(transform=f"translate({x}, {y})")

        # Convert mm to pixels using standard scale
        layout = board.layout
        w_px = layout.width_mm * self.style.scale_factor
        h_px = layout.height_mm * self.style.scale_factor

        # 1. PCB body with rounded corners
        pcb = draw.Rectangle(
            0, 0, w_px, h_px,
            rx=self.style.corner_radius,
            ry=self.style.corner_radius,
            fill=self.style.pcb_color,
            stroke=self.style.pcb_border_color,
            stroke_width=self.style.border_width
        )
        group.append(pcb)

        # 2. Mounting holes
        for hole_mm in layout.mounting_holes:
            hole_px = Point(
                hole_mm.x * self.style.scale_factor,
                hole_mm.y * self.style.scale_factor
            )
            group.append(self.render_mounting_hole(hole_px))

        # 3. GPIO header area
        group.append(self.render_header(layout))

        return group

    def render_header(self, layout: BoardLayout) -> draw.Group:
        """Render the GPIO header with standardized appearance"""
        group = draw.Group()

        # Convert to pixels
        x = layout.header_x_mm * self.style.scale_factor
        y = layout.header_y_mm * self.style.scale_factor
        w = layout.header_width_mm * self.style.scale_factor
        h = layout.header_height_mm * self.style.scale_factor

        # Black plastic connector housing
        header_rect = draw.Rectangle(
            x - 2, y - 2, w + 4, h + 4,
            rx=2, ry=2,
            fill=self.style.header_color,
            stroke="#000",
            stroke_width=1
        )
        group.append(header_rect)

        return group

    def render_mounting_hole(self, pos: Point) -> draw.Group:
        """Render a mounting hole"""
        group = draw.Group()
        # Outer circle (drill hole)
        group.append(draw.Circle(
            pos.x, pos.y, 3.2 * self.style.scale_factor / 3.0,  # ~3.2mm hole
            fill=self.style.mounting_hole_color,
            stroke="#999",
            stroke_width=0.5
        ))
        # Inner circle (through-hole)
        group.append(draw.Circle(
            pos.x, pos.y, 1.6 * self.style.scale_factor / 3.0,  # ~1.6mm inner
            fill="white",
            opacity=0.3
        ))
        return group
```

#### 2. Board Definition Schema

**File**: `src/pinviz/board_schemas.py`

Standardize board definitions with physical dimensions and layout:

```python
@dataclass
class StandardBoardDef:
    """Standard board definition for consistent rendering"""
    id: str  # e.g., "raspberry_pi_5", "esp32_devkit"
    name: str  # Display name
    manufacturer: str

    # Physical dimensions (in mm, converted to SVG units)
    physical_width: float
    physical_height: float

    # GPIO header layout
    header_pins: int  # e.g., 40 for RPi, 30 for ESP32
    header_rows: int  # Usually 2
    header_layout: str  # "vertical", "horizontal", "dual"
    header_position: Point  # Relative position on board

    # Pin definitions
    pins: list[HeaderPin]

    # Visual layout
    layout: BoardLayout
    style_overrides: dict = field(default_factory=dict)  # Optional style customization

    # Optional: SVG overlay for detailed decorations
    svg_overlay_path: str | None = None
```

#### 3. Updated Board Factory Functions

**File**: `src/pinviz/boards.py`

Update board factories to use the new standardized system:

```python
def raspberry_pi_5() -> Board:
    """Create a Raspberry Pi 5 board with standardized rendering"""
    return Board(
        name="Raspberry Pi 5",
        pins=_create_rpi_40pin_header(),
        board_def=StandardBoardDef(
            id="raspberry_pi_5",
            name="Raspberry Pi 5",
            manufacturer="Raspberry Pi Foundation",
            physical_width=85.0,  # mm
            physical_height=56.0,  # mm
            header_pins=40,
            header_rows=2,
            header_layout="vertical",
            header_position=Point(32, 6),
            pins=_create_rpi_40pin_header(),
            layout=BoardLayout(
                width=85.0,
                height=56.0,
                header_x=32,
                header_y=6,
                header_width=12,
                header_height=52,
                mounting_holes=[
                    Point(3.5, 3.5),
                    Point(61.5, 3.5),
                    Point(3.5, 52.5),
                    Point(61.5, 52.5),
                ]
            )
        )
    )

def raspberry_pi_zero_2w() -> Board:
    """Create a Raspberry Pi Zero 2 W with SAME visual style as Pi 5"""
    return Board(
        name="Raspberry Pi Zero 2 W",
        pins=_create_rpi_40pin_header(),  # Same pinout
        board_def=StandardBoardDef(
            id="raspberry_pi_zero_2w",
            name="Raspberry Pi Zero 2 W",
            manufacturer="Raspberry Pi Foundation",
            physical_width=65.0,  # mm - smaller board
            physical_height=30.0,  # mm
            header_pins=40,
            header_rows=2,
            header_layout="vertical",
            header_position=Point(28, 4),
            pins=_create_rpi_40pin_header(),
            layout=BoardLayout(
                width=65.0,
                height=30.0,
                header_x=28,
                header_y=4,
                header_width=12,
                header_height=22,  # Shorter header area
                mounting_holes=[
                    Point(3.5, 3.5),
                    Point(61.5, 3.5),
                    Point(3.5, 26.5),
                    Point(61.5, 26.5),
                ]
            )
        )
    )

def esp32_devkit() -> Board:
    """Example: ESP32 DevKit board with consistent styling"""
    return Board(
        name="ESP32 DevKit",
        pins=_create_esp32_pins(),
        board_def=StandardBoardDef(
            id="esp32_devkit",
            name="ESP32 DevKit",
            manufacturer="Espressif",
            physical_width=28.0,  # mm
            physical_height=51.0,  # mm
            header_pins=30,
            header_rows=2,
            header_layout="vertical",
            header_position=Point(2, 2),
            pins=_create_esp32_pins(),
            layout=BoardLayout(
                width=28.0,
                height=51.0,
                header_x=2,
                header_y=2,
                header_width=24,
                header_height=47,
                mounting_holes=[],  # ESP32 typically has no mounting holes
                decorative_elements=[
                    {"type": "chip", "x": 8, "y": 20, "width": 12, "height": 15, "label": "ESP32"}
                ]
            ),
            style_overrides={
                "pcb_color": "#000080"  # ESP32 boards often blue
            }
        )
    )
```

#### 4. Update SVGRenderer

**File**: `src/pinviz/render_svg.py`

Modify `_draw_board()` to use the new programmatic renderer:

```python
def _draw_board(self, dwg: draw.Drawing, board: Board) -> None:
    """Draw board using standardized programmatic rendering"""
    x = self.layout_config.board_margin_left
    y = self.layout_config.board_margin_top

    # Get board style (with any overrides)
    style = self._get_board_style(board)

    # Render using programmatic renderer
    board_renderer = BoardRenderer(style)
    board_group = board_renderer.render_board(board, x, y)
    dwg.append(board_group)

    # Draw GPIO pin numbers (same as before)
    self._draw_gpio_pin_numbers(dwg, board, x, y)

    # Draw board label
    self._draw_board_label(dwg, board, x, y)
```

#### 5. Configuration System

**File**: `src/pinviz/board_config.py`

Create a board configuration system for easy additions:

```python
# Board registry - makes it easy to add new boards
BOARD_REGISTRY = {
    "raspberry_pi_5": raspberry_pi_5,
    "rpi5": raspberry_pi_5,
    "raspberry_pi_zero_2w": raspberry_pi_zero_2w,
    "pi_zero": raspberry_pi_zero_2w,
    "esp32": esp32_devkit,
    "esp32_devkit": esp32_devkit,
    # Easy to add more...
}

def get_board(board_id: str) -> Board:
    """Get a board by ID with automatic lookup"""
    factory = BOARD_REGISTRY.get(board_id.lower())
    if not factory:
        raise ValueError(f"Unknown board: {board_id}")
    return factory()
```

### Visual Consistency Standards

#### Color Palette

```python
STANDARD_COLORS = {
    "pcb_green": "#006B32",      # Standard PCB green
    "pcb_blue": "#000080",       # Alternative PCB blue
    "pcb_black": "#1A1A1A",      # Black PCB
    "pcb_red": "#8B0000",        # Red PCB
    "header_black": "#1A1A1A",   # Plastic connector housing
    "pad_gold": "#FFD700",       # Gold contact pads
    "pad_silver": "#C0C0C0",     # Silver contact pads
    "silkscreen": "#FFFFFF",     # White silkscreen text
    "copper": "#B87333",         # Exposed copper
}
```

#### Sizing Standards

**KEY PRINCIPLE: Uniform Scale Factor Across All Boards**

All boards must render at the same scale factor to maintain visual consistency:

- **Standard scale**: 3.0 px/mm (consistent across all boards)
- **Pin spacing**: 2.54mm (0.1" pitch) = 7.62px in SVG units
- **GPIO pin circles**: 4.5px radius (consistent for all boards)
- **Header connector**: Standard 2.54mm pitch
- **Corner radius**: 8px for large boards, 5px for small boards
- **Border width**: 2px

**Example board sizes at 3.0 px/mm**:

- Pi 5 (85mm × 56mm) → 255px × 168px
- Pi Zero (65mm × 30mm) → 195px × 90px ✓ Correctly smaller!
- ESP32 (28mm × 51mm) → 84px × 153px

#### Typography

- Board name: Arial Bold, 14px
- Pin labels: Arial Bold, 4.5px (inside colored circles)
- Silkscreen text: Arial, 8px, white

### Implementation Plan

#### Phase 1: Core Infrastructure

- [ ] Create `BoardStyle` dataclass with standard colors/styling
- [ ] Create `BoardLayout` dataclass for physical dimensions
- [ ] Create `StandardBoardDef` to replace current Board model fields
- [ ] Implement `BoardRenderer` class with programmatic rendering
- [ ] Add color palette constants

#### Phase 2: Refactor Existing Boards

- [ ] Update `raspberry_pi_5()` to use new system
- [ ] Update `raspberry_pi_zero_2w()` to use new system
- [ ] Ensure both boards look visually consistent
- [ ] Test all existing examples work correctly
- [ ] Update tests

#### Phase 3: Documentation & Examples

- [ ] Create board addition guide (`docs/adding_boards.md`)
- [ ] Document the StandardBoardDef schema
- [ ] Create ESP32 example to demonstrate extensibility
- [ ] Add visual style guide showing standard colors
- [ ] Update CLAUDE.md with new architecture

#### Phase 4: Migration & Cleanup

- [ ] Mark old SVG assets as deprecated (but keep for fallback)
- [ ] Update examples to use new boards
- [ ] Regenerate all example images
- [ ] Update README with new board support
- [ ] Add board registry documentation

### Benefits

1. **Visual Consistency**: All boards use the same color palette, styling, and proportions
2. **Easy Extension**: Adding new boards is as simple as defining dimensions and pin layout
3. **Maintainable**: No need to create/edit complex SVG files manually
4. **Flexible**: Style can be customized per-board if needed while maintaining consistency
5. **Professional**: Clean, standardized appearance across all board types
6. **Future-proof**: Easy to add ESP32, Arduino, STM32, and other boards

### Open Questions

1. **SVG overlays**: Should we support optional decorative overlays for chips/connectors?
   - **Recommendation**: Yes, but make them optional and standardized
2. **Scale factor**: Should all boards scale to same pin spacing or physical dimensions?
   - **Recommendation**: Same pin spacing (12mm) for visual consistency
3. **Custom boards**: How do users add custom/one-off boards?
   - **Recommendation**: Provide `custom_board()` factory that takes BoardLayout directly
4. **Backwards compatibility**: Keep old SVG rendering as fallback?
   - **Recommendation**: Yes, but mark as deprecated

### Success Criteria

- [ ] Raspberry Pi 5 and Pi Zero 2 W have identical visual styling
- [ ] Adding a new board type takes < 50 lines of code
- [ ] All boards use the same color palette and design language
- [ ] ESP32 board successfully implemented as proof-of-concept
- [ ] All existing tests pass
- [ ] Documentation clear enough for contributors to add boards

### Future Enhancements

1. **Board themes**: Dark mode, high contrast, custom color schemes
2. **Interactive editor**: Web UI to design board layouts
3. **Auto-import**: Parse board definitions from external formats (KiCad, Eagle)
4. **3D preview**: Optional 3D board representation
5. **Component library**: Standardized decorative elements (chips, connectors, LEDs)

## Next Steps

1. Create branch (already done: `feature/standardize-board-rendering`)
2. Implement Phase 1 (Core Infrastructure)
3. Refactor one board (Pi 5) as proof of concept
4. Test and iterate
5. Apply to remaining boards
