"""SVG rendering for GPIO diagrams."""

import xml.etree.ElementTree as ET
from pathlib import Path

import drawsvg as draw

from .board_renderer import BoardRenderer, BoardStyle
from .component_renderer import ComponentRenderer
from .constants import TABLE_LAYOUT
from .layout import LayoutConfig, LayoutEngine
from .logging_config import get_logger
from .model import Board, Diagram, PinRole
from .render_constants import RENDER_CONSTANTS, _parse_font_size, _parse_numeric_value
from .theme import get_color_scheme
from .wire_renderer import WireRenderer

log = get_logger(__name__)


class SVGRenderer:
    """
    Render GPIO wiring diagrams to SVG format.

    Converts a Diagram object into a scalable SVG image showing the Raspberry Pi
    board, connected devices, wire connections, and optional GPIO reference diagram.

    The renderer handles:
        - Board SVG asset embedding
        - Device box rendering with labeled pins
        - Wire routing with rounded corners
        - Inline component symbols (resistors, capacitors, diodes)
        - GPIO pin numbering and color coding
        - Optional GPIO reference diagram
        - Automatic layout via LayoutEngine

    Examples:
        >>> from pinviz import boards, devices, Connection, Diagram, SVGRenderer
        >>>
        >>> diagram = Diagram(
        ...     title="LED Circuit",
        ...     board=boards.raspberry_pi_5(),
        ...     devices=[devices.led()],
        ...     connections=[
        ...         Connection(11, "LED", "Anode"),
        ...         Connection(6, "LED", "Cathode")
        ...     ]
        ... )
        >>>
        >>> renderer = SVGRenderer()
        >>> renderer.render(diagram, "led_circuit.svg")
    """

    def __init__(self, layout_config: LayoutConfig | None = None):
        """
        Initialize SVG renderer with optional layout configuration.

        Args:
            layout_config: Layout configuration for spacing and margins.
                If None, uses default LayoutConfig.
        """
        self.layout_config = layout_config or LayoutConfig()
        self.layout_engine = LayoutEngine(self.layout_config)
        self._init_svg_handlers()

    def _init_svg_handlers(self) -> None:
        """Initialize SVG element handlers."""
        self._svg_handlers = {
            "rect": self._handle_rect,
            "circle": self._handle_circle,
            "ellipse": self._handle_ellipse,
            "line": self._handle_line,
            "polyline": self._handle_polyline,
            "polygon": self._handle_polygon,
            "path": self._handle_path,
            "text": self._handle_text,
            "g": self._handle_group,
        }

    def render(self, diagram: Diagram, output_path: str | Path) -> None:
        """
        Render a diagram to an SVG file.

        Args:
            diagram: The diagram to render
            output_path: Output file path
        """
        log.info(
            "render_started",
            output_path=str(output_path),
            title=diagram.title,
            device_count=len(diagram.devices),
            connection_count=len(diagram.connections),
        )

        # Get color scheme from theme
        color_scheme = get_color_scheme(diagram.theme)

        # Initialize renderers with color scheme
        wire_renderer = WireRenderer(self.layout_config, color_scheme)
        component_renderer = ComponentRenderer(color_scheme)

        # Calculate layout (returns immutable LayoutResult)
        log.debug("calculating_layout")
        layout_result = self.layout_engine.layout_diagram(diagram)
        log.debug(
            "layout_calculated",
            canvas_width=layout_result.canvas_width,
            canvas_height=layout_result.canvas_height,
            wire_count=len(layout_result.routed_wires),
        )

        # Extract layout data for rendering
        canvas_width = layout_result.canvas_width
        canvas_height = layout_result.canvas_height
        routed_wires = layout_result.routed_wires
        board_margin_top = layout_result.board_margin_top

        # Create SVG drawing
        dwg = draw.Drawing(canvas_width, canvas_height)

        # Add background
        dwg.append(
            draw.Rectangle(0, 0, canvas_width, canvas_height, fill=color_scheme.canvas_background)
        )

        # Draw title
        if diagram.title and diagram.show_title:
            dwg.append(
                draw.Text(
                    diagram.title,
                    RENDER_CONSTANTS.TITLE_FONT_SIZE,
                    canvas_width / 2,
                    RENDER_CONSTANTS.TITLE_Y_OFFSET,
                    text_anchor="middle",
                    font_family="Arial, sans-serif",
                    font_weight="bold",
                    fill=color_scheme.text_primary,
                )
            )

        # Draw board
        log.debug("drawing_board", board_name=diagram.board.name)
        self._draw_board(
            dwg,
            diagram.board,
            board_margin_top,
            diagram.show_board_name,
            color_scheme,
            component_renderer,
        )

        # Draw GPIO pin numbers on the header
        x = self.layout_config.board_margin_left
        y = board_margin_top
        self._draw_gpio_pin_numbers(dwg, diagram.board, x, y, color_scheme)

        # Draw wires first so they appear behind devices
        # Sort wires for proper z-order to prevent overlapping/hiding
        # Primary: source pin X position (left column pins first, right column on top)
        # Secondary: destination Y (lower devices first)
        # Tertiary: rail X position (further right first)
        # This ensures wires from right GPIO column are always on top
        log.debug("drawing_wires", wire_count=len(routed_wires))
        sorted_wires = sorted(
            routed_wires,
            key=lambda w: (
                w.from_pin_pos.x,  # Left column first, right column on top
                -w.to_pin_pos.y,  # Lower Y (higher devices) drawn last
                -(w.path_points[2].x if len(w.path_points) > 2 else w.path_points[0].x),
            ),
        )
        for wire in sorted_wires:
            wire_renderer.draw_wire(dwg, wire, draw_connection_segment=False)

        # Draw device boxes (without pins yet)
        log.debug("drawing_devices", device_count=len(diagram.devices))
        for device in diagram.devices:
            component_renderer.draw_device_box(dwg, device)

        # Draw wire connection segments on top of device boxes
        for wire in sorted_wires:
            wire_renderer.draw_wire_connection_segment(dwg, wire)

        # Draw device pins on top of everything
        for device in diagram.devices:
            component_renderer.draw_device_pins(dwg, device)

        # Draw device specifications table if legend is enabled
        if diagram.show_legend:
            self._draw_device_specs_table(dwg, diagram, board_margin_top, color_scheme)

        # Save
        log.debug("saving_svg", output_path=str(output_path))
        dwg.save_svg(str(output_path))
        log.info("render_completed", output_path=str(output_path))

    def _draw_board(
        self,
        dwg: draw.Drawing,
        board: Board,
        board_margin_top: float,
        show_board_name: bool,
        color_scheme,
        component_renderer,
    ) -> None:
        """
        Draw the Raspberry Pi board with GPIO pins.

        Uses the new standardized BoardRenderer if board.layout is defined,
        otherwise falls back to legacy SVG asset embedding.

        Args:
            dwg: The SVG drawing object
            board: The board to render
            board_margin_top: Top margin for the board
            show_board_name: Whether to display the board name label
            color_scheme: Theme color scheme
            component_renderer: Component renderer for fallback
        """
        x = self.layout_config.board_margin_left
        y = board_margin_top

        # NEW: Use standardized BoardRenderer if layout is defined
        if board.layout is not None:
            log.debug("using_standardized_board_renderer", board_name=board.name)

            # Create board style (with optional overrides)
            style = BoardStyle(**board.style_overrides) if board.style_overrides else BoardStyle()

            # Render using new system
            renderer = BoardRenderer(style)
            board_group = renderer.render_board(board.layout, x, y)
            dwg.append(board_group)

            # Calculate board dimensions for label positioning
            board_width = board.layout.width_mm * style.scale_factor
            board_height = board.layout.height_mm * style.scale_factor

        # LEGACY: Fall back to SVG asset embedding
        elif Path(board.svg_asset_path).exists():
            log.debug("using_legacy_svg_asset", board_name=board.name, path=board.svg_asset_path)
            try:
                # Parse the SVG file
                tree = ET.parse(board.svg_asset_path)
                root = tree.getroot()

                # Create a group for the board with proper positioning
                board_group = draw.Group(transform=f"translate({x}, {y})")

                # Inline the SVG content by parsing and recreating elements
                self._inline_svg_elements(board_group, root, dwg, show_board_name)

                dwg.append(board_group)

                board_width = board.width
                board_height = board.height

            except FileNotFoundError as e:
                # Expected: SVG asset file not found - use fallback rendering
                log.warning(
                    "svg_asset_not_found",
                    path=board.svg_asset_path,
                    board=board.name,
                    error=str(e),
                )
                print(
                    f"Warning: SVG asset not found ({board.svg_asset_path}), "
                    "using fallback rendering"
                )
                component_renderer.draw_board_fallback(dwg, board, x, y)
                board_width = board.width
                board_height = board.height

            except ET.ParseError as e:
                # Data corruption: Malformed SVG content - use fallback rendering
                log.error(
                    "svg_parse_error",
                    path=board.svg_asset_path,
                    board=board.name,
                    error=str(e),
                    line=e.position[0] if hasattr(e, "position") else None,
                )
                print(f"Error: SVG file is malformed ({board.svg_asset_path}): {e}")
                print("Using fallback rendering instead.")
                component_renderer.draw_board_fallback(dwg, board, x, y)
                board_width = board.width
                board_height = board.height

            except (PermissionError, OSError) as e:
                # Critical: Permission denied or disk failure - escalate to user
                error_type = type(e).__name__
                log.error(
                    "svg_system_error",
                    error_type=error_type,
                    path=board.svg_asset_path,
                    board=board.name,
                    error=str(e),
                )
                raise RuntimeError(
                    f"Critical error loading SVG asset for board '{board.name}': "
                    f"{error_type} - {e}\n"
                    f"Path: {board.svg_asset_path}\n"
                    f"This may indicate a permission issue or disk failure. "
                    f"Please check file permissions and disk health."
                ) from e
        else:
            # Fallback: draw a simple rectangle
            log.debug("using_fallback_rectangle", board_name=board.name)
            component_renderer.draw_board_fallback(dwg, board, x, y)
            board_width = board.width
            board_height = board.height

        # Draw board label
        if show_board_name:
            dwg.append(
                draw.Text(
                    board.name,
                    RENDER_CONSTANTS.BOARD_LABEL_FONT_SIZE,
                    x + board_width / 2,
                    y + board_height + RENDER_CONSTANTS.BOARD_LABEL_Y_OFFSET,
                    text_anchor="middle",
                    font_family="Arial, sans-serif",
                    font_weight="bold",
                    fill=color_scheme.text_primary,
                )
            )

    def _draw_gpio_pin_numbers(
        self, dwg: draw.Drawing, board: Board, x: float, y: float, color_scheme
    ) -> None:
        """
        Draw pin numbers on GPIO header with color-coded backgrounds.

        Creates small circles at each pin location with the physical pin number (1-40)
        and color-coded background based on pin role (power, ground, GPIO, I2C, SPI, etc.).

        Args:
            dwg: The SVG drawing object
            board: The board containing pin definitions
            x: Board X offset
            y: Board Y offset
            color_scheme: Theme color scheme
        """
        # Color mapping for pin backgrounds based on pin role

        role_colors = {
            PinRole.POWER_3V3: "#FFA500",  # Orange
            PinRole.POWER_5V: "#FF0000",  # Red
            PinRole.GROUND: "#D3D3D3",  # Light gray
            PinRole.I2C_SDA: "#FF00FF",  # Magenta
            PinRole.I2C_SCL: "#FF00FF",  # Magenta
            PinRole.I2C_EEPROM: "#FFFF00",  # Yellow
            PinRole.SPI_MOSI: "#0000FF",  # Blue
            PinRole.SPI_MISO: "#0000FF",  # Blue
            PinRole.SPI_SCLK: "#0000FF",  # Blue
            PinRole.SPI_CE0: "#0000FF",  # Blue
            PinRole.SPI_CE1: "#0000FF",  # Blue
            PinRole.UART_TX: "#0000FF",  # Blue
            PinRole.UART_RX: "#0000FF",  # Blue
            PinRole.PWM: "#00FF00",  # Green
            PinRole.GPIO: "#00FF00",  # Green
            PinRole.PCM_CLK: "#00FF00",  # Green
            PinRole.PCM_FS: "#00FF00",  # Green
            PinRole.PCM_DIN: "#00FF00",  # Green
            PinRole.PCM_DOUT: "#00FF00",  # Green
        }

        # Pin size configuration
        pin_radius = RENDER_CONSTANTS.PIN_RADIUS
        pin_font_size = RENDER_CONSTANTS.PIN_FONT_SIZE

        for pin in board.pins:
            pin_x = x + pin.position.x
            pin_y = y + pin.position.y

            # Draw circle background for pin number
            # Use color based on pin role
            bg_color = role_colors.get(pin.role, "#FFFFFF")  # Default to white if role not found

            dwg.append(
                draw.Circle(
                    pin_x,
                    pin_y,
                    pin_radius,
                    fill=bg_color,
                    stroke=color_scheme.pin_circle_stroke,
                    stroke_width=RENDER_CONSTANTS.PIN_STROKE_WIDTH,
                    opacity=RENDER_CONSTANTS.PIN_OPACITY,
                )
            )

            # Draw pin number - scaled to fit in circle
            font_size = pin_font_size  # Scaled to fit in circle
            # Use appropriate text color based on background for readability
            text_color = "#FFFFFF" if bg_color in ["#0000FF", "#FF00FF"] else "#000000"
            dwg.append(
                draw.Text(
                    str(pin.number),
                    _parse_font_size(font_size),
                    pin_x,
                    pin_y + RENDER_CONSTANTS.PIN_TEXT_Y_OFFSET,
                    text_anchor="middle",
                    font_family="Arial, sans-serif",
                    font_weight="bold",
                    fill=text_color,
                )
            )

    def _inline_svg_elements(
        self, parent_group, svg_root, dwg: draw.Drawing, show_board_name: bool = True
    ) -> None:
        """
        Inline SVG elements from external SVG file.

        Recursively processes all elements in the SVG and adds them to the parent group.

        Args:
            parent_group: Parent drawing group to add elements to
            svg_root: Root element of the SVG to inline
            dwg: Main drawing object
            show_board_name: Whether to include board name text from SVG
        """
        # SVG namespace
        svg_ns = "{http://www.w3.org/2000/svg}"

        # Process all children of the SVG root (skip root itself)
        for child in svg_root:
            # Strip namespace from tag
            tag = child.tag.replace(svg_ns, "") if svg_ns in child.tag else child.tag

            # Get all attributes
            attribs = {k.replace(svg_ns, ""): v for k, v in child.attrib.items()}

            # Create element based on tag type
            if tag == "defs":
                # Handle defs section - add to main drawing's defs
                for def_child in child:
                    def_tag = (
                        def_child.tag.replace(svg_ns, "")
                        if svg_ns in def_child.tag
                        else def_child.tag
                    )
                    def_attribs = {k.replace(svg_ns, ""): v for k, v in def_child.attrib.items()}

                    # Handle gradients
                    if def_tag == "linearGradient":
                        gradient = draw.LinearGradient(**def_attribs)
                        for stop in def_child:
                            stop_attribs = self._parse_stop_attributes(stop)
                            gradient.add_stop(**stop_attribs)
                        # Auto-added to defs when referenced
                    elif def_tag == "radialGradient":
                        gradient = draw.RadialGradient(**def_attribs)
                        for stop in def_child:
                            stop_attribs = self._parse_stop_attributes(stop)
                            gradient.add_stop(**stop_attribs)
                        # Auto-added to defs when referenced
            elif tag == "g":
                # Handle group
                g = draw.Group(**attribs)
                # Recursively process children
                for grandchild in child:
                    self._add_svg_element(g, grandchild, dwg, svg_ns, show_board_name)
                parent_group.append(g)
            else:
                # Handle other elements
                self._add_svg_element(parent_group, child, dwg, svg_ns, show_board_name)

    def _add_svg_element(
        self, parent, element, dwg: draw.Drawing, svg_ns: str, show_board_name: bool = True
    ) -> None:
        """Add a single SVG element to parent."""
        tag = element.tag.replace(svg_ns, "") if svg_ns in element.tag else element.tag

        # Filter attributes: only keep SVG namespace attributes and non-namespaced attributes
        attribs = {}
        for k, v in element.attrib.items():
            # Keep non-namespaced attributes (no braces)
            if not k.startswith("{"):
                attribs[k] = v
            # Keep SVG namespace attributes (remove namespace prefix)
            elif k.startswith(svg_ns):
                attribs[k.replace(svg_ns, "")] = v

        # Dispatch to appropriate handler
        handler = self._svg_handlers.get(tag)
        if handler:
            svg_element = handler(element, attribs, dwg, svg_ns, show_board_name)
            if svg_element:
                parent.append(svg_element)

    def _handle_rect(self, element, attribs, dwg, svg_ns, show_board_name=True):
        x = _parse_numeric_value(attribs.pop("x", 0))
        y = _parse_numeric_value(attribs.pop("y", 0))
        width = _parse_numeric_value(attribs.pop("width", 0))
        height = _parse_numeric_value(attribs.pop("height", 0))
        return draw.Rectangle(x, y, width, height, **attribs)

    def _handle_circle(self, element, attribs, dwg, svg_ns, show_board_name=True):
        cx = _parse_numeric_value(attribs.pop("cx", 0))
        cy = _parse_numeric_value(attribs.pop("cy", 0))
        r = _parse_numeric_value(attribs.pop("r", 0))
        return draw.Circle(cx, cy, r, **attribs)

    def _handle_ellipse(self, element, attribs, dwg, svg_ns, show_board_name=True):
        cx = _parse_numeric_value(attribs.pop("cx", 0))
        cy = _parse_numeric_value(attribs.pop("cy", 0))
        rx = _parse_numeric_value(attribs.pop("rx", 0))
        ry = _parse_numeric_value(attribs.pop("ry", rx))
        return draw.Ellipse(cx, cy, rx, ry, **attribs)

    def _handle_line(self, element, attribs, dwg, svg_ns, show_board_name=True):
        x1 = _parse_numeric_value(attribs.pop("x1", 0))
        y1 = _parse_numeric_value(attribs.pop("y1", 0))
        x2 = _parse_numeric_value(attribs.pop("x2", 0))
        y2 = _parse_numeric_value(attribs.pop("y2", 0))
        return draw.Line(x1, y1, x2, y2, **attribs)

    def _handle_polyline(self, element, attribs, dwg, svg_ns, show_board_name=True):
        if "points" in attribs:
            points_str = attribs.pop("points")
            # Flatten points for drawsvg
            points_flat = []
            for point in points_str.split():
                coords = point.split(",")
                if len(coords) == 2:
                    x = _parse_numeric_value(coords[0])
                    y = _parse_numeric_value(coords[1])
                    points_flat.extend([x, y])
            return draw.Polyline(*points_flat, **attribs)
        return None

    def _handle_polygon(self, element, attribs, dwg, svg_ns, show_board_name=True):
        if "points" in attribs:
            points_str = attribs.pop("points")
            # Flatten points for drawsvg
            points_flat = []
            for point in points_str.split():
                coords = point.split(",")
                if len(coords) == 2:
                    x = _parse_numeric_value(coords[0])
                    y = _parse_numeric_value(coords[1])
                    points_flat.extend([x, y])
            return draw.Lines(*points_flat, close=True, **attribs)
        return None

    def _handle_path(self, element, attribs, dwg, svg_ns, show_board_name=True):
        if "d" in attribs:
            d = attribs.pop("d")
            return draw.Path(d=d, **attribs)
        return None

    def _handle_text(self, element, attribs, dwg, svg_ns, show_board_name=True):
        text_content = element.text or ""

        # Skip board name text if show_board_name is False
        if not show_board_name and "Raspberry Pi" in text_content:
            return None

        x = _parse_numeric_value(attribs.pop("x", 0))
        y = _parse_numeric_value(attribs.pop("y", 0))
        # Font size might not be present, use default
        font_size = attribs.pop("font-size", None) or attribs.pop("font_size", None)
        font_size = _parse_font_size(str(font_size)) if font_size else 12
        return draw.Text(text_content, font_size, x, y, **attribs)

    def _handle_group(self, element, attribs, dwg, svg_ns, show_board_name=True):
        g = draw.Group(**attribs)
        for child in element:
            self._add_svg_element(g, child, dwg, svg_ns, show_board_name)
        return g

    def _parse_stop_attributes(self, stop_element) -> dict:
        """Parse gradient stop attributes, handling inline styles."""
        svg_ns = "{http://www.w3.org/2000/svg}"
        attribs = {k.replace(svg_ns, ""): v for k, v in stop_element.attrib.items()}

        # Parse style attribute if present
        if "style" in attribs:
            style_str = attribs.pop("style")
            # Parse CSS style string
            for style_item in style_str.split(";"):
                if ":" in style_item:
                    key, value = style_item.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    # Map CSS properties to the ones we need
                    if key == "stop-color":
                        attribs["color"] = value
                    elif key == "stop-opacity":
                        attribs["opacity"] = value

        # Map offset if present
        result = {}
        if "offset" in attribs:
            result["offset"] = attribs["offset"]
        if "color" in attribs:
            result["color"] = attribs["color"]
        if "opacity" in attribs:
            result["opacity"] = attribs["opacity"]

        return result

    def _wrap_text(self, text: str, max_width: float, font_size: float) -> list[str]:
        """
        Wrap text to fit within max_width.

        Uses character-width estimation to break text into multiple lines.

        Args:
            text: Text to wrap
            max_width: Maximum width in pixels
            font_size: Font size in points

        Returns:
            List of text lines that fit within max_width
        """
        # Approximate character width (varies by font, ~0.55 of font size for Arial)
        char_width = font_size * 0.55
        max_chars = int(max_width / char_width)

        if len(text) <= max_chars:
            return [text]

        # Simple word-based wrapping
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + (1 if current_line else 0)  # +1 for space
            if current_length + word_length <= max_chars:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines if lines else [text]

    def _draw_device_specs_table(
        self, dwg: draw.Drawing, diagram: Diagram, board_margin_top: float, color_scheme
    ) -> None:
        """
        Draw a device specifications table below the diagram.

        Only draws if at least one device has a description.
        Positioned below the bottommost element (device or board) with proper spacing.

        Args:
            dwg: The SVG drawing object
            diagram: The diagram containing devices
            board_margin_top: Top margin of the board
            color_scheme: Theme color scheme
        """
        # Filter devices that have descriptions
        devices_with_specs = [d for d in diagram.devices if d.description]
        if not devices_with_specs:
            return

        # Table positioning - below the bottommost element
        table_x = self.layout_config.board_margin_left

        # Find the bottommost element (devices or board)
        board_bottom = board_margin_top + diagram.board.height
        device_bottom = (
            max(d.position.y + d.height for d in diagram.devices) if diagram.devices else 0
        )
        max_bottom = max(board_bottom, device_bottom)

        # Position table below the bottommost element + margin
        table_y = max_bottom + self.layout_config.specs_table_top_margin

        # Calculate table width to align with rightmost device
        # Find the rightmost device edge
        max_device_x = max(d.position.x + d.width for d in diagram.devices)
        table_width = max_device_x - table_x

        # Table styling parameters
        base_row_height = TABLE_LAYOUT.BASE_ROW_HEIGHT
        line_spacing = TABLE_LAYOUT.LINE_SPACING
        header_height = TABLE_LAYOUT.HEADER_HEIGHT
        padding_left = TABLE_LAYOUT.PADDING_LEFT
        padding_right = TABLE_LAYOUT.PADDING_RIGHT
        name_column_width = TABLE_LAYOUT.NAME_COLUMN_WIDTH
        desc_column_start = table_x + padding_left + name_column_width

        # Pre-calculate row heights for multi-line descriptions
        desc_max_width = table_width - name_column_width - padding_left - padding_right
        row_heights = []
        for device in devices_with_specs:
            desc_lines = self._wrap_text(device.description, desc_max_width, 9)
            # Row height = base height + extra space for additional lines
            extra_lines = max(0, len(desc_lines) - 1)
            row_height = base_row_height + (extra_lines * line_spacing)
            row_heights.append(row_height)

        # Calculate total table height
        total_table_height = header_height + sum(row_heights)

        # Draw table background
        dwg.append(
            draw.Rectangle(
                table_x,
                table_y,
                table_width,
                total_table_height,
                fill=color_scheme.table_background,
                stroke=color_scheme.legend_stroke,
                stroke_width=1,
                rx=4,
                ry=4,
            )
        )

        # Draw header
        dwg.append(
            draw.Rectangle(
                table_x,
                table_y,
                table_width,
                header_height,
                fill=color_scheme.table_header_background,
                stroke=color_scheme.legend_stroke,
                stroke_width=1,
            )
        )

        # Header text
        dwg.append(
            draw.Text(
                "Device Specifications",
                12,
                table_x + padding_left,
                table_y + 20,
                font_family="Arial, sans-serif",
                font_weight="bold",
                fill=color_scheme.text_primary,
            )
        )

        # Draw rows
        y_pos = table_y + header_height
        for idx, device in enumerate(devices_with_specs):
            row_height = row_heights[idx]

            # Device name (bold, left column)
            dwg.append(
                draw.Text(
                    device.name,
                    9,
                    table_x + padding_left,
                    y_pos + 20,
                    font_family="Arial, sans-serif",
                    font_weight="bold",
                    fill=color_scheme.text_primary,
                )
            )

            # Device description (right column) - with text wrapping
            desc_lines = self._wrap_text(device.description, desc_max_width, 9)

            for i, line in enumerate(desc_lines):
                dwg.append(
                    draw.Text(
                        line,
                        9,
                        desc_column_start,
                        y_pos + 20 + (i * line_spacing),
                        font_family="Arial, sans-serif",
                        fill=color_scheme.text_secondary,
                    )
                )

            # Separator line
            if device != devices_with_specs[-1]:  # Don't draw line after last row
                dwg.append(
                    draw.Line(
                        table_x,
                        y_pos + row_height,
                        table_x + table_width,
                        y_pos + row_height,
                        stroke=color_scheme.table_separator,
                        stroke_width=1,
                    )
                )

            y_pos += row_height

    def render_to_string(self, diagram: Diagram) -> str:
        """
        Render a diagram to an SVG string.

        Args:
            diagram: The diagram to render

        Returns:
            SVG content as string
        """
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
            temp_path = f.name

        try:
            self.render(diagram, temp_path)
            with open(temp_path) as f:
                return f.read()
        finally:
            Path(temp_path).unlink(missing_ok=True)
