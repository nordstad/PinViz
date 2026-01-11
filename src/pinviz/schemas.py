"""Configuration schema validation using Pydantic.

This module defines Pydantic models for validating diagram configuration files.
It provides comprehensive validation for boards, devices, connections, and complete
diagram configurations with helpful error messages.

Examples:
    >>> from pinviz.schemas import DiagramConfigSchema
    >>> config_dict = {
    ...     "title": "My Diagram",
    ...     "board": "raspberry_pi_5",
    ...     "devices": [{"type": "bh1750", "name": "Light Sensor"}],
    ...     "connections": [{
    ...         "board_pin": 1,
    ...         "device": "Light Sensor",
    ...         "device_pin": "VCC"
    ...     }]
    ... }
    >>> schema = DiagramConfigSchema(**config_dict)
    >>> print(schema.title)
    My Diagram
"""

from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

# Valid board names and aliases
VALID_BOARD_NAMES = {
    "raspberry_pi_5",
    "raspberry_pi_4",
    "raspberry_pi_pico",
    "raspberry_pi",
    "rpi5",
    "rpi4",
    "pi4",
    "rpi",
    "pico",
}

# Valid device types from the device registry
VALID_DEVICE_TYPES = {
    "bh1750",
    "bme280",
    "button",
    "dht22",
    "ds18b20",
    "hcsr04",
    "i2c_device",
    "i2c",  # Alias for i2c_device
    "ir_led_ring",
    "led",
    "mcp3008",
    "pir",
    "spi_device",
    "spi",  # Alias for spi_device
    "ssd1306",
}

# Valid pin roles
VALID_PIN_ROLES = {
    "GPIO",
    "I2C_SDA",
    "I2C_SCL",
    "I2C_EEPROM",
    "SPI_MOSI",
    "SPI_MISO",
    "SPI_SCLK",
    "SPI_CE0",
    "SPI_CE1",
    "UART_TX",
    "UART_RX",
    "PWM",
    "PCM_FS",
    "PCM_DIN",
    "PCM_DOUT",
    "3V3",
    "5V",
    "GND",
}

# Valid wire styles
VALID_WIRE_STYLES = {"orthogonal", "curved", "mixed"}

# Valid component types
VALID_COMPONENT_TYPES = {"resistor", "capacitor", "led", "diode"}


class PointSchema(BaseModel):
    """Schema for 2D point coordinates.

    Attributes:
        x: X-coordinate (horizontal position)
        y: Y-coordinate (vertical position)
    """

    x: Annotated[float, Field(ge=0, description="X coordinate (non-negative)")]
    y: Annotated[float, Field(ge=0, description="Y coordinate (non-negative)")]

    model_config = ConfigDict(extra="forbid")


class DevicePinSchema(BaseModel):
    """Schema for device pin definition.

    Attributes:
        name: Pin name (e.g., "VCC", "GND", "SDA")
        role: Pin role/function (e.g., "3V3", "GND", "GPIO")
        position: Optional pin position (auto-calculated if not provided)
    """

    name: Annotated[str, Field(min_length=1, max_length=50, description="Pin name")]
    role: Annotated[str, Field(description="Pin role/function")] = "GPIO"
    position: PointSchema | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate that role is a known pin role."""
        role_upper = v.upper()
        if role_upper not in VALID_PIN_ROLES:
            raise ValueError(
                f"Invalid pin role '{v}'. Must be one of: {', '.join(sorted(VALID_PIN_ROLES))}"
            )
        return role_upper


class CustomDeviceSchema(BaseModel):
    """Schema for custom device definition.

    Attributes:
        name: Device name
        pins: List of device pins
        width: Device width in SVG units
        height: Device height in SVG units
        color: Device color as hex code
        description: Optional device description/specifications
    """

    name: Annotated[str, Field(min_length=1, max_length=100, description="Device name")]
    pins: Annotated[list[DevicePinSchema], Field(min_length=1, description="List of device pins")]
    width: Annotated[float, Field(gt=0, description="Device width")] = 80.0
    height: Annotated[float, Field(gt=0, description="Device height")] = 40.0
    color: Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")] = (
        "#4A90E2"
    )
    description: Annotated[str, Field(max_length=200)] | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_unique_pin_names(self):
        """Ensure all pin names are unique within the device."""
        pin_names = [pin.name for pin in self.pins]
        duplicates = [name for name in pin_names if pin_names.count(name) > 1]
        if duplicates:
            unique_dups = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate pin names found in device '{self.name}': {', '.join(unique_dups)}"
            )
        return self


class PredefinedDeviceSchema(BaseModel):
    """Schema for predefined device type.

    Attributes:
        type: Device type from registry
        name: Optional device name override
        description: Optional device description/specifications
        num_leds: Number of LEDs (for ir_led_ring type)
        has_interrupt: Whether device has interrupt pin (for i2c_device type)
        has_int_pin: Alias for has_interrupt
        color: LED color name (for led type)
        pull_up: Whether button has pull-up resistor (for button type)
    """

    type: Annotated[str, Field(description="Device type from registry")]
    name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    description: Annotated[str, Field(max_length=200)] | None = None
    # Device-specific parameters
    num_leds: Annotated[int, Field(ge=1, le=100)] | None = None  # for ir_led_ring
    has_interrupt: bool | None = None  # for i2c_device
    has_int_pin: bool | None = None  # alias for has_interrupt
    color: Annotated[str, Field(max_length=50)] | None = None  # for led
    pull_up: bool | None = None  # for button

    model_config = ConfigDict(extra="forbid")

    @field_validator("type")
    @classmethod
    def validate_device_type(cls, v: str) -> str:
        """Validate that device type is in registry."""
        type_lower = v.lower()
        if type_lower not in VALID_DEVICE_TYPES:
            valid_types = ", ".join(sorted(VALID_DEVICE_TYPES))
            raise ValueError(f"Invalid device type '{v}'. Must be one of: {valid_types}")
        return type_lower


class DeviceSchema(BaseModel):
    """Union schema for device configuration (predefined or custom).

    A device must be either:
    - A predefined type (has 'type' field)
    - A custom definition (has 'name' and 'pins' fields)
    """

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def validate_device(cls, data: dict[str, Any]) -> PredefinedDeviceSchema | CustomDeviceSchema:
        """Validate device configuration based on fields present.

        Args:
            data: Device configuration dictionary

        Returns:
            Validated device schema (predefined or custom)

        Raises:
            ValidationError: If device configuration is invalid
        """
        has_type = "type" in data
        has_pins = "pins" in data
        has_name = "name" in data

        # Custom device: has name and pins but no type
        if has_pins and has_name and not has_type:
            return CustomDeviceSchema(**data)

        # Predefined device: has type
        if has_type:
            return PredefinedDeviceSchema(**data)

        # Invalid configuration
        raise ValueError(
            "Device must have either 'type' (predefined device) or "
            "'name' and 'pins' (custom device)"
        )


class ComponentSchema(BaseModel):
    """Schema for inline component (resistor, capacitor, etc.).

    Attributes:
        type: Component type
        value: Component value (e.g., "220Ω", "10µF")
        position: Position along wire (0.0 = start, 1.0 = end)
    """

    type: Annotated[str, Field(description="Component type")] = "resistor"
    value: Annotated[str, Field(min_length=1, max_length=50, description="Component value")]
    position: Annotated[float, Field(ge=0.0, le=1.0, description="Position along wire")] = 0.55

    model_config = ConfigDict(extra="forbid")

    @field_validator("type")
    @classmethod
    def validate_component_type(cls, v: str) -> str:
        """Validate that component type is valid."""
        type_lower = v.lower()
        if type_lower not in VALID_COMPONENT_TYPES:
            valid_types = ", ".join(sorted(VALID_COMPONENT_TYPES))
            raise ValueError(f"Invalid component type '{v}'. Must be one of: {valid_types}")
        return type_lower


class ConnectionSchema(BaseModel):
    """Schema for wire connection.

    Attributes:
        board_pin: Physical pin number on board (1-40 for Raspberry Pi)
        device: Device name
        device_pin: Pin name on device
        color: Optional wire color as hex code
        net: Optional logical net name
        style: Wire routing style
        components: Optional inline components
    """

    board_pin: Annotated[int, Field(ge=1, description="Board pin number")]
    device: Annotated[str, Field(min_length=1, max_length=100, description="Device name")]
    device_pin: Annotated[str, Field(min_length=1, max_length=50, description="Device pin name")]
    color: (
        Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")] | None
    ) = None
    net: Annotated[str, Field(max_length=100)] | None = None
    style: Annotated[str, Field(description="Wire routing style")] = "mixed"
    components: list[ComponentSchema] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @field_validator("style")
    @classmethod
    def validate_wire_style(cls, v: str) -> str:
        """Validate that wire style is valid."""
        style_lower = v.lower()
        if style_lower not in VALID_WIRE_STYLES:
            raise ValueError(
                f"Invalid wire style '{v}'. Must be one of: {', '.join(sorted(VALID_WIRE_STYLES))}"
            )
        return style_lower


class DiagramConfigSchema(BaseModel):
    """Schema for complete diagram configuration.

    Attributes:
        title: Diagram title
        board: Board type/name
        devices: List of devices
        connections: List of wire connections
        show_legend: Whether to show wire color legend
        show_gpio_diagram: Whether to show GPIO pin diagram
        show_title: Whether to show the diagram title
        show_board_name: Whether to show board name label
    """

    title: Annotated[str, Field(min_length=1, max_length=200, description="Diagram title")] = (
        "GPIO Diagram"
    )
    board: Annotated[str, Field(description="Board type/name")] = "raspberry_pi_5"
    devices: Annotated[list[dict[str, Any]], Field(description="List of devices")] = Field(
        default_factory=list
    )
    connections: Annotated[list[ConnectionSchema], Field(description="List of connections")] = (
        Field(default_factory=list)
    )
    show_legend: bool = True
    show_gpio_diagram: bool = False
    show_title: bool = True
    show_board_name: bool = True

    model_config = ConfigDict(extra="forbid")

    @field_validator("board")
    @classmethod
    def validate_board_name(cls, v: str) -> str:
        """Validate that board name is supported."""
        board_lower = v.lower()
        if board_lower not in VALID_BOARD_NAMES:
            raise ValueError(
                f"Invalid board name '{v}'. Must be one of: {', '.join(sorted(VALID_BOARD_NAMES))}"
            )
        return board_lower

    @field_validator("devices")
    @classmethod
    def validate_devices(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate each device in the list."""
        validated_devices = []
        for i, device_data in enumerate(v):
            try:
                # Validate device structure
                DeviceSchema.validate_device(device_data)
                validated_devices.append(device_data)
            except ValidationError as e:
                raise ValueError(f"Invalid device at index {i}: {e}") from e
        return validated_devices

    @model_validator(mode="after")
    def validate_connections_reference_devices(self):
        """Ensure all connections reference existing devices."""
        # Collect device names
        device_names = set()
        for device_data in self.devices:
            if "name" in device_data:
                device_names.add(device_data["name"])
            elif "type" in device_data and "name" not in device_data:
                # Default name for predefined devices without custom name
                # We can't determine the exact default name without loading the device,
                # so we'll skip this validation here and let the loader handle it
                pass

        # Check connections (only if we have explicit device names)
        if device_names:
            for i, connection in enumerate(self.connections):
                if connection.device not in device_names:
                    # Only warn if the device name is explicitly set
                    # (not a default from a type-only device)
                    has_matching_type = any(
                        d.get("type") == connection.device.lower() for d in self.devices
                    )
                    if not has_matching_type and connection.device not in device_names:
                        available = ", ".join(sorted(device_names))
                        raise ValueError(
                            f"Connection at index {i} references unknown device "
                            f"'{connection.device}'. Available devices: {available}"
                        )

        return self


def validate_config(config_dict: dict[str, Any]) -> DiagramConfigSchema:
    """
    Validate a configuration dictionary against the schema.

    Args:
        config_dict: Configuration dictionary to validate

    Returns:
        Validated DiagramConfigSchema instance

    Raises:
        ValidationError: If configuration is invalid with detailed error messages

    Examples:
        >>> config = {
        ...     "title": "Test",
        ...     "devices": [{"type": "bh1750"}],
        ...     "connections": [{"board_pin": 1, "device": "BH1750", "device_pin": "VCC"}]
        ... }
        >>> validated = validate_config(config)
        >>> print(validated.title)
        Test
    """
    return DiagramConfigSchema(**config_dict)


def get_validation_errors(config_dict: dict[str, Any]) -> list[str]:
    """
    Get a list of human-readable validation error messages.

    Args:
        config_dict: Configuration dictionary to validate

    Returns:
        List of error messages (empty if valid)

    Examples:
        >>> config = {"devices": [], "connections": []}
        >>> errors = get_validation_errors(config)
        >>> len(errors) > 0
        True
    """
    try:
        DiagramConfigSchema(**config_dict)
        return []
    except ValidationError as e:
        return [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]


class BoardPinConfigSchema(BaseModel):
    """Schema for board header pin definition in configuration file.

    Attributes:
        physical_pin: Physical pin number (1-40 for Raspberry Pi)
        name: Pin name/label (e.g., "GPIO2", "3V3", "GND")
        role: Pin function/role (e.g., "GPIO", "I2C_SDA", "POWER_3V3")
        gpio_bcm: BCM GPIO number (null for power/ground pins)
        header: Header side for dual-header boards ("left" or "right", optional)
    """

    physical_pin: Annotated[int, Field(ge=1, description="Physical pin number")]
    name: Annotated[str, Field(min_length=1, max_length=50, description="Pin name")]
    role: Annotated[str, Field(description="Pin role/function")]
    gpio_bcm: int | None = None
    header: str | None = None  # "left" or "right" for dual-header boards

    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate that role is a known pin role."""
        role_upper = v.upper()
        if role_upper not in VALID_PIN_ROLES:
            raise ValueError(
                f"Invalid pin role '{v}'. Must be one of: {', '.join(sorted(VALID_PIN_ROLES))}"
            )
        return role_upper


class BoardLayoutConfigSchema(BaseModel):
    """Schema for board GPIO header layout configuration.

    Defines the physical layout parameters for positioning GPIO header pins
    in the SVG rendering. These values should align with the board's SVG asset.

    Supports two layout modes:
    1. Single-header (Raspberry Pi): Vertical layout with left_col_x, right_col_x,
       start_y, row_spacing
    2. Dual-header (Pico): Horizontal layout with top_header and bottom_header

    Attributes:
        left_col_x: X-coordinate for left column (single-header vertical layout only)
        right_col_x: X-coordinate for right column (single-header vertical layout only)
        start_y: Starting Y-coordinate (single-header vertical layout only)
        row_spacing: Vertical spacing between rows (single-header vertical layout only)
        top_header: Layout for top physical header (dual-header horizontal layout)
        bottom_header: Layout for bottom physical header (dual-header horizontal layout)
    """

    # Single-header vertical layout (Raspberry Pi)
    left_col_x: Annotated[
        float | None, Field(None, gt=0, description="X position for left column (odd pins)")
    ]
    right_col_x: Annotated[
        float | None, Field(None, gt=0, description="X position for right column (even pins)")
    ]
    start_y: Annotated[
        float | None, Field(None, gt=0, description="Starting Y position for first row")
    ]
    row_spacing: Annotated[
        float | None, Field(None, gt=0, description="Vertical spacing between rows")
    ]

    # Dual-header horizontal layout (Pico-style: pins on top/bottom edges)
    top_header: dict | None = None
    bottom_header: dict | None = None

    model_config = ConfigDict(extra="allow")  # Allow extra fields for flexibility

    @model_validator(mode="after")
    def validate_layout_mode(self):
        """Ensure either single-header or dual-header layout is defined."""
        has_single_header = all(
            [
                self.left_col_x is not None,
                self.right_col_x is not None,
                self.start_y is not None,
                self.row_spacing is not None,
            ]
        )
        has_dual_header = self.top_header is not None and self.bottom_header is not None

        if not has_single_header and not has_dual_header:
            raise ValueError(
                "Layout must define either single-header "
                "(left_col_x, right_col_x, start_y, row_spacing) "
                "or dual-header (top_header, bottom_header) configuration"
            )

        if has_single_header and self.right_col_x <= self.left_col_x:
            raise ValueError(
                f"right_col_x ({self.right_col_x}) must be greater than "
                f"left_col_x ({self.left_col_x})"
            )

        return self


class BoardConfigSchema(BaseModel):
    """Schema for complete board configuration file.

    This schema validates board definition JSON files that specify the board's
    GPIO header layout and pin assignments. Board configurations are loaded
    from JSON files in the board_configs directory.

    Attributes:
        name: Board name (e.g., "Raspberry Pi 5")
        svg_asset: Filename of the SVG asset (relative to assets directory)
        width: Board width in SVG units (for legacy compatibility)
        height: Board height in SVG units (for legacy compatibility)
        header_offset: Legacy offset values for header positioning
        layout: GPIO header layout parameters
        pins: List of GPIO header pin definitions

    Examples:
        >>> config_dict = {
        ...     "name": "Raspberry Pi 5",
        ...     "svg_asset": "pi_5_mod.svg",
        ...     "width": 205.42,
        ...     "height": 307.46,
        ...     "header_offset": {"x": 23.715, "y": 5.156},
        ...     "layout": {
        ...         "left_col_x": 187.1,
        ...         "right_col_x": 199.1,
        ...         "start_y": 16.2,
        ...         "row_spacing": 12.0
        ...     },
        ...     "pins": [
        ...         {"physical_pin": 1, "name": "3V3", "role": "3V3", "gpio_bcm": None},
        ...         {"physical_pin": 2, "name": "5V", "role": "5V", "gpio_bcm": None}
        ...     ]
        ... }
        >>> config = BoardConfigSchema(**config_dict)
        >>> config.name
        'Raspberry Pi 5'
    """

    name: Annotated[str, Field(min_length=1, max_length=100, description="Board name")]
    svg_asset: Annotated[
        str,
        Field(min_length=1, max_length=100, description="SVG asset filename"),
    ]
    width: Annotated[float, Field(gt=0, description="Board width (legacy)")]
    height: Annotated[float, Field(gt=0, description="Board height (legacy)")]
    header_offset: PointSchema
    layout: BoardLayoutConfigSchema
    pins: Annotated[
        list[BoardPinConfigSchema],
        Field(min_length=1, description="List of GPIO header pins"),
    ]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_unique_pin_numbers(self):
        """Ensure all physical pin numbers are unique."""
        pin_numbers = [pin.physical_pin for pin in self.pins]
        duplicates = [num for num in pin_numbers if pin_numbers.count(num) > 1]
        if duplicates:
            unique_dups = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate physical pin numbers found: {', '.join(map(str, unique_dups))}"
            )
        return self

    @model_validator(mode="after")
    def validate_pin_numbers_sequential(self):
        """Ensure pin numbers are sequential from 1 to N."""
        pin_numbers = sorted([pin.physical_pin for pin in self.pins])
        expected = list(range(1, len(self.pins) + 1))
        if pin_numbers != expected:
            raise ValueError(
                f"Pin numbers must be sequential from 1 to {len(self.pins)}. Found: {pin_numbers}"
            )
        return self


def validate_board_config(config_dict: dict[str, Any]) -> BoardConfigSchema:
    """
    Validate a board configuration dictionary against the schema.

    Args:
        config_dict: Board configuration dictionary to validate

    Returns:
        Validated BoardConfigSchema instance

    Raises:
        ValidationError: If configuration is invalid with detailed error messages

    Examples:
        >>> config = {
        ...     "name": "Test Board",
        ...     "svg_asset": "test.svg",
        ...     "width": 200.0,
        ...     "height": 300.0,
        ...     "header_offset": {"x": 20.0, "y": 5.0},
        ...     "layout": {
        ...         "left_col_x": 187.1,
        ...         "right_col_x": 199.1,
        ...         "start_y": 16.2,
        ...         "row_spacing": 12.0
        ...     },
        ...     "pins": [...]  # 40 pin definitions
        ... }
        >>> validated = validate_board_config(config)
        >>> print(validated.name)
        Test Board
    """
    return BoardConfigSchema(**config_dict)


# Valid device categories
VALID_DEVICE_CATEGORIES = {"sensors", "leds", "displays", "actuators", "io", "generic"}


class DeviceParameterSchema(BaseModel):
    """Schema for device parameter definition.

    Attributes:
        type: Parameter type (string, int, float, bool)
        default: Default value for the parameter
        description: Description of what the parameter does
    """

    type: Annotated[str, Field(description="Parameter type")]
    default: Any = None
    description: Annotated[str, Field(description="Parameter description")] = ""

    model_config = ConfigDict(extra="forbid")

    @field_validator("type")
    @classmethod
    def validate_parameter_type(cls, v: str) -> str:
        """Validate that parameter type is valid."""
        valid_types = {"string", "int", "float", "bool"}
        type_lower = v.lower()
        if type_lower not in valid_types:
            raise ValueError(
                f"Invalid parameter type '{v}'. Must be one of: {', '.join(sorted(valid_types))}"
            )
        return type_lower


class DeviceDisplaySchema(BaseModel):
    """Schema for device display properties.

    Attributes:
        width: Device width in SVG units
        height: Device height in SVG units
        color: Optional device color override
    """

    width: Annotated[float, Field(gt=0, description="Device width")] = 80.0
    height: Annotated[float, Field(gt=0, description="Device height")] = 40.0
    color: (
        Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")] | None
    ) = None

    model_config = ConfigDict(extra="forbid")


class DeviceLayoutSchema(BaseModel):
    """Schema for device pin layout configuration.

    Attributes:
        pin_spacing: Spacing between pins
        start_y: Starting Y position for pins
        orientation: Layout orientation (vertical or horizontal)
    """

    pin_spacing: Annotated[float, Field(gt=0, description="Pin spacing")] = 10.0
    start_y: Annotated[float, Field(ge=0, description="Starting Y position")] = 12.0
    orientation: Annotated[str, Field(description="Layout orientation")] = "vertical"

    model_config = ConfigDict(extra="forbid")

    @field_validator("orientation")
    @classmethod
    def validate_orientation(cls, v: str) -> str:
        """Validate that orientation is valid."""
        valid_orientations = {"vertical", "horizontal"}
        orientation_lower = v.lower()
        if orientation_lower not in valid_orientations:
            valid_str = ", ".join(sorted(valid_orientations))
            raise ValueError(f"Invalid orientation '{v}'. Must be one of: {valid_str}")
        return orientation_lower


class DeviceConfigPinSchema(BaseModel):
    """Schema for device configuration pin definition.

    Attributes:
        name: Pin name (e.g., "VCC", "GND", "SDA")
        role: Pin role/function (e.g., "3V3", "GND", "GPIO")
        optional: Whether the pin is optional
        position: Optional explicit pin position
    """

    name: Annotated[str, Field(min_length=1, max_length=50, description="Pin name")]
    role: Annotated[str, Field(description="Pin role/function")] = "GPIO"
    optional: bool = False
    position: PointSchema | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate that role is a known pin role."""
        role_upper = v.upper()
        if role_upper not in VALID_PIN_ROLES:
            raise ValueError(
                f"Invalid pin role '{v}'. Must be one of: {', '.join(sorted(VALID_PIN_ROLES))}"
            )
        return role_upper


class DeviceConfigSchema(BaseModel):
    """Schema for device configuration file validation.

    This schema validates device definition JSON files that specify device
    properties, pins, and metadata. Device configurations are loaded from
    JSON files in the device_configs directory.

    Attributes:
        id: Unique device identifier (lowercase, alphanumeric with underscores)
        name: Device display name
        category: Device category (sensors, leds, displays, etc.)
        description: Brief description of the device
        pins: List of device pins
        parameters: Optional device parameters for variants
        layout: Optional pin layout configuration
        display: Optional display properties
        i2c_address: Optional I2C address
        datasheet_url: Optional datasheet URL
        notes: Optional setup notes

    Examples:
        >>> config_dict = {
        ...     "id": "bh1750",
        ...     "name": "BH1750 Light Sensor",
        ...     "category": "sensors",
        ...     "pins": [
        ...         {"name": "VCC", "role": "3V3"},
        ...         {"name": "GND", "role": "GND"}
        ...     ],
        ...     "i2c_address": "0x23"
        ... }
        >>> config = DeviceConfigSchema(**config_dict)
        >>> config.name
        'BH1750 Light Sensor'
    """

    id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            pattern=r"^[a-z][a-z0-9_-]*$",
            description="Unique device identifier",
        ),
    ]
    name: Annotated[str, Field(min_length=1, max_length=100, description="Device name")]
    category: Annotated[str, Field(description="Device category")]
    description: Annotated[str, Field(description="Device description")] = ""
    pins: Annotated[
        list[DeviceConfigPinSchema],
        Field(min_length=1, description="List of device pins"),
    ]
    parameters: dict[str, DeviceParameterSchema] = Field(default_factory=dict)
    layout: DeviceLayoutSchema | None = None
    display: DeviceDisplaySchema | None = None
    i2c_address: (
        Annotated[
            str,
            Field(pattern=r"^0x[0-9A-Fa-f]{2}$", description="I2C address in hex format"),
        ]
        | None
    ) = None
    datasheet_url: Annotated[str, Field(description="Datasheet URL")] | None = None
    notes: Annotated[str, Field(description="Setup notes")] = ""

    model_config = ConfigDict(extra="forbid")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate that category is valid."""
        category_lower = v.lower()
        if category_lower not in VALID_DEVICE_CATEGORIES:
            valid_str = ", ".join(sorted(VALID_DEVICE_CATEGORIES))
            raise ValueError(f"Invalid category '{v}'. Must be one of: {valid_str}")
        return category_lower

    @field_validator("datasheet_url")
    @classmethod
    def validate_datasheet_url(cls, v: str | None) -> str | None:
        """Validate that datasheet URL is valid."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError(f"Invalid datasheet URL '{v}'. Must start with http:// or https://")
        return v

    @model_validator(mode="after")
    def validate_unique_pin_names(self):
        """Ensure all pin names are unique within the device."""
        pin_names = [pin.name for pin in self.pins]
        duplicates = [name for name in pin_names if pin_names.count(name) > 1]
        if duplicates:
            unique_dups = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate pin names found in device '{self.name}': {', '.join(unique_dups)}"
            )
        return self

    @model_validator(mode="after")
    def validate_i2c_pins_if_address(self):
        """If I2C address is specified, ensure device has I2C pins."""
        if self.i2c_address:
            pin_roles = [pin.role for pin in self.pins]
            has_sda = "I2C_SDA" in pin_roles
            has_scl = "I2C_SCL" in pin_roles
            if not (has_sda and has_scl):
                raise ValueError(
                    f"Device '{self.name}' has i2c_address but missing I2C pins "
                    f"(needs both I2C_SDA and I2C_SCL)"
                )
        return self


def validate_device_config(config_dict: dict[str, Any]) -> DeviceConfigSchema:
    """
    Validate a device configuration dictionary against the schema.

    Args:
        config_dict: Device configuration dictionary to validate

    Returns:
        Validated DeviceConfigSchema instance

    Raises:
        ValidationError: If configuration is invalid with detailed error messages

    Examples:
        >>> config = {
        ...     "id": "test_sensor",
        ...     "name": "Test Sensor",
        ...     "category": "sensors",
        ...     "pins": [
        ...         {"name": "VCC", "role": "3V3"},
        ...         {"name": "GND", "role": "GND"}
        ...     ]
        ... }
        >>> validated = validate_device_config(config)
        >>> print(validated.name)
        Test Sensor
    """
    return DeviceConfigSchema(**config_dict)
