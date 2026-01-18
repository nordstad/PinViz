"""Validation module for GPIO wiring diagrams.

This module provides validation to catch common wiring mistakes:
- Multiple devices using the same GPIO pin
- I2C address conflicts between devices
- 5V devices connected to 3.3V pins (voltage mismatches)
- GPIO current limits exceeded

DISCLAIMER:
This validation is provided as a convenience tool to catch common mistakes.
It is NOT a substitute for proper electrical engineering review and does not
guarantee the safety or correctness of your wiring. Users are solely responsible
for verifying their wiring against component datasheets, electrical specifications,
and safety standards. Always test your circuits carefully and consult with qualified
professionals when needed. The authors and contributors of this software assume no
liability for any hardware damage, personal injury, or other consequences resulting
from the use of this validation tool.
"""

from dataclasses import dataclass
from enum import Enum

from .devices.registry import get_registry
from .logging_config import get_logger
from .model import Diagram, PinRole

log = get_logger(__name__)


# Pin Compatibility Matrix
# Defines which pin roles can be safely connected to each other
# Key: (source_role, target_role) -> (is_compatible, severity_if_incompatible)
# Severity: "error" for dangerous connections, "warning" for questionable ones
PIN_COMPATIBILITY_MATRIX: dict[tuple[PinRole, PinRole], tuple[bool, str | None]] = {
    # Power connections - same voltage OK
    (PinRole.POWER_3V3, PinRole.POWER_3V3): (True, None),
    (PinRole.POWER_5V, PinRole.POWER_5V): (True, None),
    # Power to ground - DANGEROUS short circuit
    (PinRole.POWER_3V3, PinRole.GROUND): (False, "error"),
    (PinRole.POWER_5V, PinRole.GROUND): (False, "error"),
    # Ground connections always OK
    (PinRole.GROUND, PinRole.GROUND): (True, None),
    # Cross-voltage power connections - handled separately in voltage checks
    (PinRole.POWER_5V, PinRole.POWER_3V3): (False, "error"),
    (PinRole.POWER_3V3, PinRole.POWER_5V): (False, "warning"),
    # I2C connections - data and clock lines
    (PinRole.I2C_SDA, PinRole.I2C_SDA): (True, None),
    (PinRole.I2C_SCL, PinRole.I2C_SCL): (True, None),
    (PinRole.I2C_SDA, PinRole.I2C_SCL): (False, "error"),  # Swapped I2C lines
    (PinRole.I2C_SCL, PinRole.I2C_SDA): (False, "error"),  # Swapped I2C lines
    # SPI connections - MOSI, MISO, SCLK, chip enables
    (PinRole.SPI_MOSI, PinRole.SPI_MOSI): (True, None),
    (PinRole.SPI_MISO, PinRole.SPI_MISO): (True, None),
    (PinRole.SPI_SCLK, PinRole.SPI_SCLK): (True, None),
    (PinRole.SPI_CE0, PinRole.SPI_CE0): (True, None),
    (PinRole.SPI_CE1, PinRole.SPI_CE1): (True, None),
    (PinRole.SPI_MOSI, PinRole.SPI_MISO): (False, "error"),  # Swapped MOSI/MISO
    (PinRole.SPI_MISO, PinRole.SPI_MOSI): (False, "error"),  # Swapped MOSI/MISO
    # UART connections - TX and RX
    (PinRole.UART_TX, PinRole.UART_RX): (True, None),  # TX to RX is correct
    (PinRole.UART_RX, PinRole.UART_TX): (True, None),  # RX to TX is correct
    (PinRole.UART_TX, PinRole.UART_TX): (False, "error"),  # TX to TX won't work
    (PinRole.UART_RX, PinRole.UART_RX): (False, "error"),  # RX to RX won't work
    # PWM connections
    (PinRole.PWM, PinRole.PWM): (True, None),
    (PinRole.PWM, PinRole.GPIO): (True, None),  # PWM to generic GPIO OK
    # GPIO connections - generic GPIO can connect to most things with caution
    (PinRole.GPIO, PinRole.GPIO): (True, None),
    (PinRole.GPIO, PinRole.PWM): (True, None),
    # PCM Audio connections
    (PinRole.PCM_CLK, PinRole.PCM_CLK): (True, None),
    (PinRole.PCM_FS, PinRole.PCM_FS): (True, None),
    (PinRole.PCM_DIN, PinRole.PCM_DIN): (True, None),
    (PinRole.PCM_DOUT, PinRole.PCM_DOUT): (True, None),
    # I2C EEPROM identification
    (PinRole.I2C_EEPROM, PinRole.I2C_EEPROM): (True, None),
}


def check_pin_compatibility(source_role: PinRole, target_role: PinRole) -> tuple[bool, str | None]:
    """
    Check if two pin roles are compatible for connection.

    Args:
        source_role: Role of the source pin
        target_role: Role of the target pin

    Returns:
        Tuple of (is_compatible, severity_level)
        severity_level is "error" or "warning" if incompatible, None if compatible

    Examples:
        >>> check_pin_compatibility(PinRole.POWER_3V3, PinRole.POWER_3V3)
        (True, None)
        >>> check_pin_compatibility(PinRole.POWER_5V, PinRole.GROUND)
        (False, "error")
    """
    # Check direct match in compatibility matrix
    if (source_role, target_role) in PIN_COMPATIBILITY_MATRIX:
        return PIN_COMPATIBILITY_MATRIX[(source_role, target_role)]

    # Default behavior for unlisted combinations:
    # - Power to power: warning (might be intentional voltage distribution)
    # - GPIO to specialized pins: warning (might be bit-banging)
    # - Different protocol pins: error (likely a mistake)

    power_roles = {PinRole.POWER_3V3, PinRole.POWER_5V}
    protocol_roles = {
        PinRole.I2C_SDA,
        PinRole.I2C_SCL,
        PinRole.SPI_MOSI,
        PinRole.SPI_MISO,
        PinRole.SPI_SCLK,
        PinRole.SPI_CE0,
        PinRole.SPI_CE1,
        PinRole.UART_TX,
        PinRole.UART_RX,
    }

    # GPIO to protocol pins - warning (might be software implementation)
    if source_role == PinRole.GPIO and target_role in protocol_roles:
        return (True, "warning")
    if source_role in protocol_roles and target_role == PinRole.GPIO:
        return (True, "warning")

    # Power to protocol/data pins - error (dangerous)
    if source_role in power_roles and target_role in protocol_roles:
        return (False, "error")
    if source_role in protocol_roles and target_role in power_roles:
        return (False, "error")

    # Default: incompatible with warning
    return (False, "warning")


class ValidationLevel(str, Enum):
    """Severity level of a validation issue."""

    ERROR = "error"  # Critical issue that could damage hardware
    WARNING = "warning"  # Potential issue that should be reviewed
    INFO = "info"  # Informational note


@dataclass
class ValidationIssue:
    """A validation issue found in a diagram.

    Attributes:
        level: Severity level (error, warning, info)
        message: Human-readable description of the issue
        location: Where the issue was found (e.g., "GPIO 18", "Connection 1->2")
    """

    level: ValidationLevel
    message: str
    location: str | None = None

    def __str__(self) -> str:
        """Format validation issue for display."""
        if self.level == ValidationLevel.ERROR:
            prefix = "⚠️  Error"
        elif self.level == ValidationLevel.WARNING:
            prefix = "⚠️  Warning"
        else:
            prefix = "ℹ️  Info"

        if self.location:
            return f"{prefix}: {self.message} ({self.location})"
        return f"{prefix}: {self.message}"


class DiagramValidator:
    """Validates GPIO wiring diagrams for common mistakes.

    Performs structural validation to catch errors before diagram generation:
    - Duplicate GPIO pin assignments
    - I2C address conflicts
    - Voltage compatibility (3.3V vs 5V)
    - GPIO current limits

    Example:
        >>> validator = DiagramValidator()
        >>> issues = validator.validate(diagram)
        >>> for issue in issues:
        ...     print(issue)
    """

    # GPIO current limit per pin (Raspberry Pi spec)
    MAX_GPIO_CURRENT_MA = 16

    def validate(self, diagram: Diagram) -> list[ValidationIssue]:
        """Validate a diagram and return all issues found.

        Args:
            diagram: The diagram to validate

        Returns:
            List of validation issues (errors, warnings, info)
        """
        log.info(
            "validation_started",
            board=diagram.board.name,
            device_count=len(diagram.devices),
            connection_count=len(diagram.connections),
        )

        issues: list[ValidationIssue] = []
        issues.extend(self._check_pin_conflicts(diagram))
        issues.extend(self._check_voltage_mismatches(diagram))
        issues.extend(self._check_pin_role_compatibility(diagram))
        issues.extend(self._check_i2c_address_conflicts(diagram))
        issues.extend(self._check_current_limits(diagram))
        issues.extend(self._check_connection_validity(diagram))
        issues.extend(self._check_stub_wires(diagram))

        # Categorize for logging
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
        infos = [i for i in issues if i.level == ValidationLevel.INFO]

        log.info(
            "validation_completed",
            total_issues=len(issues),
            errors=len(errors),
            warnings=len(warnings),
            infos=len(infos),
        )

        # Log individual issues at appropriate levels
        for issue in errors:
            log.error("validation_error_found", issue=str(issue), location=issue.location)
        for issue in warnings:
            log.warning("validation_warning_found", issue=str(issue), location=issue.location)

        return issues

    def _check_pin_conflicts(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check for multiple devices connected to the same GPIO pin.

        This checks for duplicate physical pin usage, which is usually an error
        except for pins like power/ground that can be shared.
        """
        log.debug("checking_pin_conflicts")
        issues: list[ValidationIssue] = []
        pin_usage: dict[int, list[str]] = {}

        # Track only board-to-device connections for pin conflict checking
        for conn in diagram.connections:
            # Only count board connections (not device-to-device)
            if conn.is_board_connection():
                if conn.board_pin not in pin_usage:
                    pin_usage[conn.board_pin] = []
                pin_usage[conn.board_pin].append(f"{conn.device_name}.{conn.device_pin_name}")

        # Check if this is a multi-tier diagram (has device-to-device connections)
        has_device_to_device = any(conn.is_device_connection() for conn in diagram.connections)

        # Check for conflicts (ignore power/ground pins which can be shared)
        for pin_num, devices in pin_usage.items():
            if len(devices) > 1:
                board_pin = diagram.board.get_pin_by_number(pin_num)
                if board_pin:
                    # Power and ground pins can be shared in simple diagrams
                    if board_pin.role in (
                        PinRole.POWER_3V3,
                        PinRole.POWER_5V,
                        PinRole.GROUND,
                    ):
                        # For multi-tier diagrams, error on shared power/ground
                        # In real hardware, you cannot physically connect multiple wires to one pin
                        # Use breadboard power rails or device-to-device chaining instead
                        if has_device_to_device and len(devices) > 1:
                            issues.append(
                                ValidationIssue(
                                    level=ValidationLevel.ERROR,
                                    message=(
                                        f"Multiple devices share {board_pin.role.value} pin "
                                        f"{pin_num}: {', '.join(devices)}. "
                                        "In real hardware, you cannot physically connect "
                                        "multiple wires to a single pin. Use breadboard power "
                                        "rails or chain power/ground through device-to-device "
                                        "connections."
                                    ),
                                    location=f"Pin {pin_num}",
                                )
                            )
                        # For non-multi-tier diagrams, just warn
                        elif len(devices) > 1:
                            issues.append(
                                ValidationIssue(
                                    level=ValidationLevel.WARNING,
                                    message=(
                                        f"Multiple devices share {board_pin.role.value} pin "
                                        f"{pin_num}: {', '.join(devices)}. "
                                        "Consider using a breadboard with power rails for "
                                        "cleaner wiring."
                                    ),
                                    location=f"Pin {pin_num}",
                                )
                            )
                        continue

                    # I2C pins can be shared (it's a bus)
                    if board_pin.role in (PinRole.I2C_SDA, PinRole.I2C_SCL):
                        # This is OK, but note it
                        issues.append(
                            ValidationIssue(
                                level=ValidationLevel.INFO,
                                message=f"I2C pin {board_pin.name} shared by: {', '.join(devices)}",
                                location=f"Pin {pin_num}",
                            )
                        )
                        continue

                    # SPI pins can be shared (chip select distinguishes devices)
                    if board_pin.role in (
                        PinRole.SPI_MOSI,
                        PinRole.SPI_MISO,
                        PinRole.SPI_SCLK,
                    ):
                        issues.append(
                            ValidationIssue(
                                level=ValidationLevel.INFO,
                                message=f"SPI pin {board_pin.name} shared by: {', '.join(devices)}",
                                location=f"Pin {pin_num}",
                            )
                        )
                        continue

                    # All other pins should not be shared
                    device_list = ", ".join(devices)
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            message=(
                                f"Pin {pin_num} ({board_pin.name}) used by "
                                f"multiple devices: {device_list}"
                            ),
                            location=f"Pin {pin_num}",
                        )
                    )

        return issues

    def _check_voltage_mismatches(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check for voltage compatibility issues.

        Detects cases where 5V devices are connected to 3.3V pins or vice versa.
        """
        issues: list[ValidationIssue] = []

        # Build device lookup dictionary for O(1) access (performance optimization)
        device_by_name = {device.name: device for device in diagram.devices}

        for conn in diagram.connections:
            board_pin = diagram.board.get_pin_by_number(conn.board_pin)
            if not board_pin:
                continue

            device = device_by_name.get(conn.device_name)
            if not device:
                continue

            device_pin = device.get_pin_by_name(conn.device_pin_name)
            if not device_pin:
                continue

            # Check power pin compatibility
            if board_pin.role == PinRole.POWER_5V and device_pin.role == PinRole.POWER_3V3:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"5V board pin connected to 3.3V device pin "
                            f"'{device_pin.name}' on {conn.device_name}"
                        ),
                        location=(
                            f"Pin {conn.board_pin} → {conn.device_name}.{conn.device_pin_name}"
                        ),
                    )
                )

            if board_pin.role == PinRole.POWER_3V3 and device_pin.role == PinRole.POWER_5V:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=(
                            f"3.3V board pin connected to 5V device pin "
                            f"'{device_pin.name}' on {conn.device_name} "
                            "(device may not function properly)"
                        ),
                        location=(
                            f"Pin {conn.board_pin} → {conn.device_name}.{conn.device_pin_name}"
                        ),
                    )
                )

        return issues

    def _check_pin_role_compatibility(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check if pin roles are compatible across all connections.

        Validates that the pin roles on both ends of each connection are compatible,
        checking both board-to-device and device-to-device connections using the
        pin compatibility matrix.
        """
        log.debug("checking_pin_role_compatibility")
        issues: list[ValidationIssue] = []

        # Build device lookup dictionary for O(1) access
        device_by_name = {device.name: device for device in diagram.devices}

        for i, conn in enumerate(diagram.connections, 1):
            # Get source and target pin roles
            source_role: PinRole | None = None
            target_role: PinRole | None = None
            location = f"Connection #{i}"

            # Get target device and pin
            target_device = device_by_name.get(conn.device_name)
            if not target_device:
                continue  # Will be caught by connection validity check

            target_device_pin = target_device.get_pin_by_name(conn.device_pin_name)
            if not target_device_pin:
                continue  # Will be caught by connection validity check

            target_role = target_device_pin.role

            # Determine source role based on connection type
            if conn.is_board_connection():
                # Board-to-device connection
                board_pin = diagram.board.get_pin_by_number(conn.board_pin)
                if not board_pin:
                    continue  # Will be caught by connection validity check

                source_role = board_pin.role
                location = f"Pin {conn.board_pin} → {conn.device_name}.{conn.device_pin_name}"

            elif conn.is_device_connection():
                # Device-to-device connection
                source_device = device_by_name.get(conn.source_device)
                if not source_device:
                    continue  # Will be caught by connection validity check

                source_device_pin = source_device.get_pin_by_name(conn.source_pin)
                if not source_device_pin:
                    continue  # Will be caught by connection validity check

                source_role = source_device_pin.role
                location = (
                    f"{conn.source_device}.{conn.source_pin} → "
                    f"{conn.device_name}.{conn.device_pin_name}"
                )

            # Check compatibility using the matrix
            if source_role and target_role:
                is_compatible, severity = check_pin_compatibility(source_role, target_role)

                if not is_compatible:
                    message = (
                        f"Incompatible pin roles: {source_role.value} "
                        f"connected to {target_role.value}"
                    )

                    if severity == "error":
                        level = ValidationLevel.ERROR
                    else:
                        level = ValidationLevel.WARNING

                    issues.append(
                        ValidationIssue(
                            level=level,
                            message=message,
                            location=location,
                        )
                    )
                elif severity == "warning":
                    # Compatible but questionable connection
                    message = (
                        f"Unusual pin connection: {source_role.value} to {target_role.value} "
                        "(verify this is intentional)"
                    )
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            message=message,
                            location=location,
                        )
                    )

        return issues

    def _check_i2c_address_conflicts(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check for I2C address conflicts between devices.

        Multiple I2C devices on the same bus must have unique addresses.
        Uses device registry metadata for I2C addresses when available.
        """
        log.debug("checking_i2c_conflicts")
        issues: list[ValidationIssue] = []

        # Find all devices connected to I2C bus
        i2c_device_names: list[str] = []
        for conn in diagram.connections:
            board_pin = diagram.board.get_pin_by_number(conn.board_pin)
            if (
                board_pin
                and board_pin.role in (PinRole.I2C_SDA, PinRole.I2C_SCL)
                and conn.device_name not in i2c_device_names
            ):
                i2c_device_names.append(conn.device_name)

        # Get registry for device metadata lookups
        registry = get_registry()

        # Build device lookup dictionary for O(1) access (performance optimization)
        device_by_name = {device.name: device for device in diagram.devices}

        # Check for address conflicts using registry metadata
        address_usage: dict[int, list[str]] = {}
        for device_name in i2c_device_names:
            # Find the device object (using O(1) dictionary lookup)
            device = device_by_name.get(device_name)
            if not device:
                continue

            # Try to get I2C address from registry via type_id
            i2c_address = None
            if device.type_id:
                template = registry.get(device.type_id)
                if template and template.i2c_address is not None:
                    i2c_address = template.i2c_address

            # Group devices by address
            if i2c_address is not None:
                if i2c_address not in address_usage:
                    address_usage[i2c_address] = []
                address_usage[i2c_address].append(device_name)

        # Report conflicts
        for addr, devices in address_usage.items():
            if len(devices) > 1:
                device_list = ", ".join(devices)
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=(
                            f"I2C address conflict at 0x{addr:02X}: {device_list} (default address)"
                        ),
                        location="I2C Bus",
                    )
                )

        return issues

    def _check_current_limits(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check if total current draw exceeds GPIO pin limits.

        Each GPIO pin on Raspberry Pi can source/sink up to 16mA.
        """
        issues: list[ValidationIssue] = []

        # Count how many connections are on each GPIO pin
        gpio_load_count: dict[int, int] = {}
        for conn in diagram.connections:
            board_pin = diagram.board.get_pin_by_number(conn.board_pin)
            if board_pin and board_pin.role == PinRole.GPIO:
                gpio_load_count[conn.board_pin] = gpio_load_count.get(conn.board_pin, 0) + 1

        # Warn if multiple devices on one GPIO (likely current issue)
        for pin_num, count in gpio_load_count.items():
            if count > 1:
                board_pin = diagram.board.get_pin_by_number(pin_num)
                if board_pin:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            message=(
                                f"GPIO {board_pin.name} driving {count} "
                                f"devices (max current: "
                                f"{self.MAX_GPIO_CURRENT_MA}mA per pin)"
                            ),
                            location=f"Pin {pin_num}",
                        )
                    )

        return issues

    def _check_connection_validity(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check if all connections reference valid pins and devices."""
        issues: list[ValidationIssue] = []

        # Build device lookup dictionary for O(1) access (performance optimization)
        device_by_name = {device.name: device for device in diagram.devices}

        for i, conn in enumerate(diagram.connections, 1):
            # Check source is valid (board pin or device/pin)
            if conn.is_board_connection():
                # Check board pin exists
                board_pin = diagram.board.get_pin_by_number(conn.board_pin)
                if not board_pin:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            message=f"Invalid board pin number: {conn.board_pin}",
                            location=f"Connection #{i}",
                        )
                    )
                    continue

            elif conn.is_device_connection():
                # Check source device exists
                source_device = device_by_name.get(conn.source_device)
                if not source_device:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            message=f"Source device '{conn.source_device}' not found in diagram",
                            location=f"Connection #{i}",
                        )
                    )
                    continue

                # Check source device pin exists
                source_pin = source_device.get_pin_by_name(conn.source_pin)
                if not source_pin:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            message=(
                                f"Pin '{conn.source_pin}' not found on source device "
                                f"'{conn.source_device}'"
                            ),
                            location=f"Connection #{i}",
                        )
                    )
                    continue

            # Check target device exists (using O(1) dictionary lookup)
            device = device_by_name.get(conn.device_name)
            if not device:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Device '{conn.device_name}' not found in diagram",
                        location=f"Connection #{i}",
                    )
                )
                continue

            # Check device pin exists
            device_pin = device.get_pin_by_name(conn.device_pin_name)
            if not device_pin:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"Pin '{conn.device_pin_name}' not found on device '{conn.device_name}'"
                        ),
                        location=f"Connection #{i}",
                    )
                )

        return issues

    def _check_stub_wires(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check for 'stub wires' - data pins connected but serving no functional purpose.

        A stub wire occurs when:
        - Data output pin (DOUT, MISO, OUT, TX) is connected to board but nothing reads it
        - Data input pin (DIN, MOSI, IN, RX) is connected but no data is being sent
        - Only one half of a bidirectional protocol (e.g., MISO without MOSI) is connected

        This helps catch wiring reference examples that should only show control lines.
        """
        log.debug("checking_stub_wires")
        issues: list[ValidationIssue] = []

        # Build device lookup dictionary
        device_by_name = {device.name: device for device in diagram.devices}

        # Data output roles that should have a functional purpose
        data_output_roles = {
            PinRole.SPI_MISO,  # SPI data out
            PinRole.UART_TX,  # UART transmit
            # Note: GPIO and general OUT pins can have many uses, so we don't flag them
        }

        # Track which SPI data pins are connected per device
        spi_data_pins_per_device: dict[str, set[str]] = {}

        for conn in diagram.connections:
            # Only check board-to-device connections
            if not conn.is_board_connection():
                continue

            device = device_by_name.get(conn.device_name)
            if not device:
                continue

            device_pin = device.get_pin_by_name(conn.device_pin_name)
            if not device_pin:
                continue

            # Track SPI data pins
            if device_pin.role in {PinRole.SPI_MOSI, PinRole.SPI_MISO}:
                if conn.device_name not in spi_data_pins_per_device:
                    spi_data_pins_per_device[conn.device_name] = set()
                spi_data_pins_per_device[conn.device_name].add(device_pin.role.value)

        # Check for incomplete SPI connections (one data line without the other)
        for device_name, spi_pins in spi_data_pins_per_device.items():
            has_mosi = "SPI_MOSI" in spi_pins
            has_miso = "SPI_MISO" in spi_pins

            if has_mosi and not has_miso:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=(
                            f"Potential stub wire: MOSI connected but MISO not connected "
                            f"on {device_name}. For wiring reference examples, consider "
                            "removing MOSI connection (show pin but no wire). "
                            "For functional examples, add MISO connection."
                        ),
                        location=f"Device: {device_name}",
                    )
                )

            if has_miso and not has_mosi:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=(
                            f"Potential stub wire: MISO connected but MOSI not connected "
                            f"on {device_name}. For wiring reference examples, consider "
                            "removing MISO connection (show pin but no wire). "
                            "For functional examples, add MOSI connection."
                        ),
                        location=f"Device: {device_name}",
                    )
                )

        # Check for data output pins with no apparent consumer
        # Only flag if it's a simple single-device scenario
        if len(diagram.devices) == 1:
            for conn in diagram.connections:
                if not conn.is_board_connection():
                    continue

                device = device_by_name.get(conn.device_name)
                if not device:
                    continue

                device_pin = device.get_pin_by_name(conn.device_pin_name)
                if not device_pin:
                    continue

                # Check if it's a data output pin in a single-device circuit
                if device_pin.role in data_output_roles:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.INFO,
                            message=(
                                f"Data output pin {conn.device_pin_name} "
                                f"({device_pin.role.value}) connected in single-device circuit. "
                                "For wiring reference examples, consider removing this connection "
                                "(show pin but no wire)."
                            ),
                            location=f"{conn.device_name}.{conn.device_pin_name}",
                        )
                    )

        return issues
