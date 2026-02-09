"""Core data model for Raspberry Pi GPIO diagrams."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from .theme import Theme

if TYPE_CHECKING:
    from .board_renderer import BoardLayout


class PinRole(StrEnum):
    """
    Role or function of a GPIO pin.

    Defines the various roles that pins can have on the Raspberry Pi GPIO header
    or on connected devices. Used for automatic wire color assignment and
    documentation purposes.

    Attributes:
        POWER_3V3: 3.3V power supply pin
        POWER_5V: 5V power supply pin
        GROUND: Ground (GND) pin
        GPIO: General Purpose Input/Output pin
        I2C_SDA: I2C Serial Data line
        I2C_SCL: I2C Serial Clock line
        SPI_MOSI: SPI Master Out Slave In
        SPI_MISO: SPI Master In Slave Out
        SPI_SCLK: SPI Serial Clock
        SPI_CE0: SPI Chip Enable 0
        SPI_CE1: SPI Chip Enable 1
        UART_TX: UART Transmit
        UART_RX: UART Receive
        PWM: Pulse Width Modulation
        PCM_CLK: PCM Audio Clock
        PCM_FS: PCM Audio Frame Sync
        PCM_DIN: PCM Audio Data In
        PCM_DOUT: PCM Audio Data Out
        I2C_EEPROM: I2C EEPROM identification pins
    """

    POWER_3V3 = "3V3"
    POWER_5V = "5V"
    GROUND = "GND"
    GPIO = "GPIO"
    I2C_SDA = "I2C_SDA"
    I2C_SCL = "I2C_SCL"
    SPI_MOSI = "SPI_MOSI"
    SPI_MISO = "SPI_MISO"
    SPI_SCLK = "SPI_SCLK"
    SPI_CE0 = "SPI_CE0"
    SPI_CE1 = "SPI_CE1"
    UART_TX = "UART_TX"
    UART_RX = "UART_RX"
    PWM = "PWM"
    PCM_CLK = "PCM_CLK"
    PCM_FS = "PCM_FS"
    PCM_DIN = "PCM_DIN"
    PCM_DOUT = "PCM_DOUT"
    I2C_EEPROM = "I2C_EEPROM"


class WireColor(StrEnum):
    """
    Standard wire colors for electronics projects.

    Provides a set of commonly used wire colors as hex color codes.
    These can be used for explicit color assignment in connections.

    Attributes:
        RED: Red (#FF0000)
        BLACK: Black (#000000)
        WHITE: White (#FFFFFF)
        GREEN: Green (#00FF00)
        BLUE: Blue (#0000FF)
        YELLOW: Yellow (#FFFF00)
        ORANGE: Orange (#FF8C00)
        PURPLE: Purple (#9370DB)
        GRAY: Gray (#808080)
        BROWN: Brown (#8B4513)
        PINK: Pink (#FF69B4)
        CYAN: Cyan (#00CED1)
        MAGENTA: Magenta (#FF00FF)
        LIME: Lime (#32CD32)
        TURQUOISE: Turquoise (#40E0D0)
    """

    RED = "#FF0000"
    BLACK = "#000000"
    WHITE = "#FFFFFF"
    GREEN = "#00FF00"
    BLUE = "#0000FF"
    YELLOW = "#FFFF00"
    ORANGE = "#FF8C00"
    PURPLE = "#9370DB"
    GRAY = "#808080"
    BROWN = "#8B4513"
    PINK = "#FF69B4"
    CYAN = "#00CED1"
    MAGENTA = "#FF00FF"
    LIME = "#32CD32"
    TURQUOISE = "#40E0D0"


"""
Default wire colors automatically assigned based on pin roles.

Maps each PinRole to a standard wire color (hex code) following common
electronics conventions. These colors are used when no explicit color
is specified for a connection.

Color assignments:
    - Power (3.3V): Orange (#FF8C00)
    - Power (5V): Red (#FF0000)
    - Ground: Black (#000000)
    - I2C SDA: Green (#00FF00)
    - I2C SCL: Blue (#0000FF)
    - SPI MOSI: Dark Turquoise (#00CED1)
    - SPI MISO: Hot Pink (#FF69B4)
    - SPI SCLK: Gold (#FFD700)
    - SPI CE0: Medium Purple (#9370DB)
    - SPI CE1: Saddle Brown (#8B4513)
    - UART TX: Tomato (#FF6347)
    - UART RX: Royal Blue (#4169E1)
    - PWM: Orchid (#DA70D6)
    - GPIO: Gray (#808080) - default for generic GPIO pins
"""
DEFAULT_COLORS: dict[PinRole, str] = {
    PinRole.POWER_3V3: "#FF8C00",  # Orange
    PinRole.POWER_5V: "#FF0000",  # Red
    PinRole.GROUND: "#000000",  # Black
    PinRole.I2C_SDA: "#00FF00",  # Green
    PinRole.I2C_SCL: "#0000FF",  # Blue
    PinRole.SPI_MOSI: "#00CED1",  # Dark Turquoise
    PinRole.SPI_MISO: "#FF69B4",  # Hot Pink
    PinRole.SPI_SCLK: "#FFD700",  # Gold
    PinRole.SPI_CE0: "#9370DB",  # Medium Purple
    PinRole.SPI_CE1: "#8B4513",  # Saddle Brown
    PinRole.UART_TX: "#FF6347",  # Tomato
    PinRole.UART_RX: "#4169E1",  # Royal Blue
    PinRole.PWM: "#DA70D6",  # Orchid
    PinRole.GPIO: "#808080",  # Gray (default for generic GPIO)
}


@dataclass
class Point:
    """
    A 2D point in SVG coordinate space.

    Represents a position in the SVG canvas coordinate system.
    All measurements are in SVG units (typically pixels).

    Attributes:
        x: Horizontal position (left to right)
        y: Vertical position (top to bottom)
    """

    x: float
    y: float


@dataclass
class HeaderPin:
    """
    A pin on the Raspberry Pi GPIO header.

    Represents a single pin on the 40-pin GPIO header, including its physical
    pin number, function/role, and optional BCM GPIO number for GPIO pins.

    Attributes:
        number: Physical pin number on the header (1-40)
        name: Pin name (e.g., "3V3", "GPIO2", "GND")
        role: Functional role of the pin (power, GPIO, I2C, SPI, etc.)
        gpio_bcm: BCM GPIO number for GPIO pins (e.g., GPIO2 = BCM 2), None for non-GPIO pins
        position: Pin position in board coordinate space, set by board template
    """

    number: int  # Physical pin number (1-40)
    name: str  # e.g., "3V3", "GPIO2", "GND"
    role: PinRole
    gpio_bcm: int | None = None  # BCM GPIO number (e.g., GPIO2 = BCM 2)
    position: Point | None = None  # Position in board coordinate space


@dataclass
class Board:
    """
    A Raspberry Pi board with GPIO header.

    Represents a physical Raspberry Pi board including its GPIO header pins,
    dimensions, and rendering information.

    Attributes:
        name: Board display name (e.g., "Raspberry Pi 5")
        pins: List of all GPIO header pins (40 pins for standard boards)
        svg_asset_path: Path to board SVG image file (legacy, optional)
        width: Board width in SVG units (legacy, used if layout is None)
        height: Board height in SVG units (legacy, used if layout is None)
        header_offset: Position of GPIO header pin 1 (legacy)
        layout: Optional BoardLayout for standardized rendering (preferred)
        style_overrides: Optional style customizations (e.g., custom PCB color)
    """

    name: str
    pins: list[HeaderPin]
    svg_asset_path: str = ""  # Path to board SVG image (legacy)
    width: float = 340.0  # Board width in SVG units (legacy)
    height: float = 220.0  # Board height in SVG units (legacy)
    header_offset: Point = field(
        default_factory=lambda: Point(297.0, 52.0)
    )  # GPIO header pin 1 position (legacy)
    layout: BoardLayout | None = None  # Standardized layout (preferred)
    style_overrides: dict = field(default_factory=dict)  # Custom styling

    def get_pin_by_number(self, pin_number: int) -> HeaderPin | None:
        """
        Get a pin by its physical pin number.

        Args:
            pin_number: Physical pin number (1-40)

        Returns:
            HeaderPin if found, None otherwise

        Examples:
            >>> board = boards.raspberry_pi_5()
            >>> pin = board.get_pin_by_number(1)
            >>> print(pin.name)
            3V3
        """
        return next((p for p in self.pins if p.number == pin_number), None)

    def get_pin_by_bcm(self, bcm_number: int) -> HeaderPin | None:
        """
        Get a pin by its BCM GPIO number.

        Only applies to GPIO pins. Power and ground pins don't have BCM numbers.

        Args:
            bcm_number: BCM GPIO number (0-27 for Raspberry Pi)

        Returns:
            HeaderPin if found, None otherwise

        Examples:
            >>> board = boards.raspberry_pi_5()
            >>> pin = board.get_pin_by_bcm(2)
            >>> print(f"{pin.name} is on physical pin {pin.number}")
            GPIO2 is on physical pin 3
        """
        return next((p for p in self.pins if p.gpio_bcm == bcm_number), None)

    def get_pin_by_name(self, name: str) -> HeaderPin | None:
        """
        Get a pin by its name.

        Args:
            name: Pin name (e.g., "GPIO2", "3V3", "GND")

        Returns:
            HeaderPin if found, None otherwise

        Examples:
            >>> board = boards.raspberry_pi_5()
            >>> pin = board.get_pin_by_name("GPIO2")
            >>> print(f"Pin {pin.number} - {pin.name}")
            Pin 3 - GPIO2
        """
        return next((p for p in self.pins if p.name == name), None)


@dataclass
class DevicePin:
    """
    A pin on a device or module.

    Represents a connection point on an external device (sensor, LED, button, etc.)
    that can be wired to the Raspberry Pi GPIO header.

    Attributes:
        name: Pin name as labeled on the device (e.g., "VCC", "GND", "SDA", "SCL")
        role: Functional role of the pin (determines wire color)
        position: Pin position relative to device origin (set by device template)
    """

    name: str  # e.g., "VCC", "GND", "SDA", "SCL"
    role: PinRole
    position: Point = field(default_factory=lambda: Point(0, 0))  # Position relative to device


@dataclass
class Device:
    """
    An electronic device or module to be connected to the Raspberry Pi.

    Represents an external component (sensor, LED, button, etc.) that will
    be wired to the GPIO header. Devices have named pins and are rendered
    as colored rectangles in the diagram.

    Attributes:
        name: Display name shown in diagram (e.g., "BH1750 Light Sensor")
        pins: List of connection points on the device
        width: Device box width in SVG units (default: 80.0)
        height: Device box height in SVG units (default: 40.0)
        position: Device position in canvas (automatically calculated by layout engine)
        color: Device box fill color as hex code (default: "#4A90E2" blue)
        type_id: Optional device template type ID (for registry lookup)
        description: Optional device description
        url: Optional URL to device documentation or datasheet
        category: Optional device category (sensors, displays, leds, etc.)
        i2c_address: Optional default I2C address (7-bit integer)
    """

    name: str  # Display name (e.g., "BH1750 Light Sensor")
    pins: list[DevicePin]
    width: float = 80.0
    height: float = 40.0
    position: Point = field(default_factory=lambda: Point(0, 0))  # Set by layout engine
    color: str = "#4A90E2"  # Device box color
    type_id: str | None = None  # Optional device template type ID

    # Optional metadata fields (populated from registry or config)
    description: str | None = None
    url: str | None = None
    category: str | None = None
    i2c_address: int | None = None

    def get_pin_by_name(self, name: str) -> DevicePin | None:
        """
        Get a device pin by name.

        Args:
            name: Pin name as labeled on device (e.g., "VCC", "SDA")

        Returns:
            DevicePin if found, None otherwise

        Examples:
            >>> sensor = devices.bh1750_light_sensor()
            >>> vcc_pin = sensor.get_pin_by_name("VCC")
            >>> print(vcc_pin.role)
            PinRole.POWER_3V3
        """
        return next((p for p in self.pins if p.name == name), None)


class WireStyle(StrEnum):
    """
    Wire routing style for connections.

    Defines how wires are drawn between board pins and device pins.

    Attributes:
        ORTHOGONAL: Straight lines with right angles (no rounding)
        CURVED: Smooth bezier curves throughout
        MIXED: Orthogonal routing with rounded corners (default, recommended)
    """

    ORTHOGONAL = "orthogonal"  # Right angles
    CURVED = "curved"  # Bezier curves
    MIXED = "mixed"  # Orthogonal with rounded corners


class ComponentType(StrEnum):
    """
    Type of inline component on a wire.

    Defines types of electronic components that can be placed along
    a wire connection between board and device.

    Attributes:
        RESISTOR: Resistor (e.g., current limiting, pull-up/down)
        CAPACITOR: Capacitor (e.g., decoupling, filtering)
        DIODE: Diode (e.g., flyback protection)
    """

    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    DIODE = "diode"


@dataclass
class Component:
    """
    An inline component placed on a wire connection.

    Represents a component (resistor, capacitor, diode) that sits on a wire
    between the board and device. Useful for showing pull-up resistors,
    current limiting resistors, decoupling capacitors, etc.

    Attributes:
        type: Type of component (resistor, capacitor, diode)
        value: Component value with units (e.g., "220Ω", "100µF", "1N4148")
        position: Position along wire path from source to destination (0.0-1.0, default 0.55)
    """

    type: ComponentType
    value: str  # e.g., "220Ω", "100µF", "1N4148"
    position: float = 0.55  # Position along wire path (0.0-1.0, default 55% from source)


@dataclass
class Connection:
    """
    A wire connection between a board pin and a device pin, or between two devices.

    Represents a physical wire connecting either:
    1. A GPIO header pin to a device pin (board-to-device connection)
    2. A pin on one device to a pin on another device (device-to-device connection)

    Wire color is automatically assigned based on pin role unless explicitly specified.

    Attributes:
        board_pin: Physical pin number on the GPIO header (1-40). Required for board connections.
        device_name: Name of the target device (must match Device.name)
        device_pin_name: Name of the target pin on the device
        source_device: Name of the source device for device-to-device connections
        source_pin: Name of the source pin for device-to-device connections
        color: Wire color as hex code (auto-assigned from pin role if None)
        net_name: Optional logical net name for documentation (e.g., "I2C_BUS")
        style: Wire routing style (orthogonal, curved, or mixed)
        components: List of inline components on this wire (resistors, capacitors, etc.)

    Examples:
        >>> # Board-to-device connection with auto-assigned color
        >>> conn = Connection(board_pin=1, device_name="Sensor", device_pin_name="VCC")
        >>>
        >>> # Device-to-device connection
        >>> conn = Connection(
        ...     source_device="TP4056",
        ...     source_pin="OUT+",
        ...     device_name="ESP32",
        ...     device_pin_name="VIN"
        ... )
        >>>
        >>> # Connection with custom color and resistor
        >>> conn = Connection(
        ...     board_pin=11,
        ...     device_name="LED",
        ...     device_pin_name="Anode",
        ...     color="#FF0000",
        ...     components=[Component(ComponentType.RESISTOR, "220Ω")]
        ... )
    """

    # Maintain backward compatibility: board_pin stays as first positional arg
    board_pin: int | None = None  # Physical pin number on the board (for board connections)
    device_name: str | None = None  # Name of the target device
    device_pin_name: str | None = None  # Name of the pin on the target device

    # New fields for device-to-device connections
    source_device: str | None = None  # Name of the source device
    source_pin: str | None = None  # Name of the pin on the source device

    # Connection properties
    color: str | None = None  # Wire color (auto-assigned if None)
    net_name: str | None = None  # Optional net name for grouping
    style: WireStyle = WireStyle.MIXED  # Wire routing style
    components: list[Component] = field(default_factory=list)  # Inline components

    def __post_init__(self) -> None:
        """Validate that exactly one source type is specified."""
        # Validate target device fields are always present
        if self.device_name is None:
            raise ValueError(
                "Connection validation error: 'device_name' is required for all connections. "
                f"Current value: {self.device_name}"
            )
        if self.device_pin_name is None:
            raise ValueError(
                "Connection validation error: 'device_pin_name' is required for all connections. "
                f"Target device: '{self.device_name}', device_pin_name: {self.device_pin_name}"
            )

        # Validate source: exactly one source type must be specified
        has_board_source = self.board_pin is not None
        has_device_source = self.source_device is not None and self.source_pin is not None

        # Check for incomplete device-to-device connection specification
        has_partial_device_source = (self.source_device is None) != (self.source_pin is None)

        if has_partial_device_source:
            raise ValueError(
                "Connection validation error: Incomplete device-to-device connection. "
                f"Both 'source_device' and 'source_pin' must be specified together. "
                f"Current values: source_device='{self.source_device}', "
                f"source_pin='{self.source_pin}'. "
                f"Target: device='{self.device_name}', pin='{self.device_pin_name}'"
            )

        if has_board_source and has_device_source:
            raise ValueError(
                "Connection validation error: Cannot specify both board_pin "
                "and source_device/source_pin. "
                f"A connection must have exactly one source. "
                f"Current values: board_pin={self.board_pin}, "
                f"source_device='{self.source_device}', "
                f"source_pin='{self.source_pin}'. "
                f"Target: device='{self.device_name}', pin='{self.device_pin_name}'"
            )

        if not has_board_source and not has_device_source:
            raise ValueError(
                "Connection validation error: Must specify either 'board_pin' OR both "
                f"'source_device' and 'source_pin'. "
                f"A connection must have exactly one source. "
                f"Current values: board_pin={self.board_pin}, "
                f"source_device='{self.source_device}', "
                f"source_pin='{self.source_pin}'. "
                f"Target: device='{self.device_name}', pin='{self.device_pin_name}'"
            )

    def is_board_connection(self) -> bool:
        """
        Check if this is a board-to-device connection.

        Returns:
            True if the connection source is a board pin, False otherwise.
        """
        return self.board_pin is not None

    def is_device_connection(self) -> bool:
        """
        Check if this is a device-to-device connection.

        Returns:
            True if the connection source is another device, False otherwise.
        """
        return self.source_device is not None

    def get_source(self) -> tuple[str, str]:
        """
        Get the source of this connection as a (name, pin) tuple.

        Returns:
            For board connections: ("board", str(board_pin))
            For device connections: (source_device, source_pin)

        Raises:
            ValueError: If the connection has invalid state (should not happen after __post_init__).
        """
        if self.is_board_connection():
            return ("board", str(self.board_pin))
        elif self.is_device_connection():
            return (self.source_device, self.source_pin)  # type: ignore
        else:
            raise ValueError("Connection has invalid state: no source specified")

    @classmethod
    def from_board(
        cls,
        board_pin: int,
        device_name: str,
        device_pin_name: str,
        color: str | None = None,
        net_name: str | None = None,
        style: WireStyle = WireStyle.MIXED,
        components: list[Component] | None = None,
    ) -> Connection:
        """
        Create a board-to-device connection.

        Args:
            board_pin: Physical pin number on the GPIO header (1-40)
            device_name: Name of the target device
            device_pin_name: Name of the target pin on the device
            color: Optional wire color as hex code
            net_name: Optional logical net name for documentation
            style: Wire routing style (default: MIXED)
            components: Optional list of inline components

        Returns:
            A new Connection instance for a board-to-device connection.

        Examples:
            >>> conn = Connection.from_board(1, "Sensor", "VCC", color="#FF0000")
        """
        return cls(
            board_pin=board_pin,
            device_name=device_name,
            device_pin_name=device_pin_name,
            color=color,
            net_name=net_name,
            style=style,
            components=components or [],
        )

    @classmethod
    def from_device(
        cls,
        source_device: str,
        source_pin: str,
        target_device: str,
        target_pin: str,
        color: str | None = None,
        net_name: str | None = None,
        style: WireStyle = WireStyle.MIXED,
        components: list[Component] | None = None,
    ) -> Connection:
        """
        Create a device-to-device connection.

        Args:
            source_device: Name of the source device
            source_pin: Name of the source pin
            target_device: Name of the target device
            target_pin: Name of the target pin
            color: Optional wire color as hex code
            net_name: Optional logical net name for documentation
            style: Wire routing style (default: MIXED)
            components: Optional list of inline components

        Returns:
            A new Connection instance for a device-to-device connection.

        Examples:
            >>> conn = Connection.from_device("TP4056", "OUT+", "ESP32", "VIN")
        """
        return cls(
            source_device=source_device,
            source_pin=source_pin,
            device_name=target_device,
            device_pin_name=target_pin,
            color=color,
            net_name=net_name,
            style=style,
            components=components or [],
        )


@dataclass
class Diagram:
    """
    A complete GPIO wiring diagram.

    Represents the entire diagram including the Raspberry Pi board, all connected
    devices, and all wire connections. This is the top-level object that gets
    rendered to SVG.

    Attributes:
        title: Diagram title displayed at the top
        board: The Raspberry Pi board
        devices: List of all devices to be connected
        connections: List of all wire connections
        show_legend: Whether to show the device specifications table (default: False)
        show_gpio_diagram: Whether to show the GPIO pin reference diagram (default: False)
        show_title: Whether to show the diagram title (default: True)
        show_board_name: Whether to show the board name (default: True)
        canvas_width: Canvas width in SVG units (auto-calculated by layout engine)
        canvas_height: Canvas height in SVG units (auto-calculated by layout engine)

    Examples:
        >>> from pinviz import boards, devices, Connection, Diagram, SVGRenderer
        >>>
        >>> # Create diagram
        >>> diagram = Diagram(
        ...     title="BH1750 Light Sensor",
        ...     board=boards.raspberry_pi_5(),
        ...     devices=[devices.bh1750_light_sensor()],
        ...     connections=[
        ...         Connection(1, "BH1750", "VCC"),
        ...         Connection(6, "BH1750", "GND"),
        ...         Connection(3, "BH1750", "SDA"),
        ...         Connection(5, "BH1750", "SCL"),
        ...     ]
        ... )
        >>>
        >>> # Render to SVG
        >>> renderer = SVGRenderer()
        >>> renderer.render(diagram, "output.svg")
    """

    title: str
    board: Board
    devices: list[Device]
    connections: list[Connection]
    show_legend: bool = False
    show_gpio_diagram: bool = False
    show_title: bool = True
    show_board_name: bool = True
    theme: Theme = Theme.LIGHT
    canvas_width: float = 800.0
    canvas_height: float = 600.0
