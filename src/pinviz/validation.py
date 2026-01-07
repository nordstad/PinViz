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

from .model import Diagram, PinRole


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

    # Default I2C addresses for common devices (7-bit addresses)
    DEFAULT_I2C_ADDRESSES = {
        "BH1750": 0x23,  # Can also be 0x5C if ADDR pin is high
        "BME280": 0x76,  # Can also be 0x77
        "BME680": 0x76,  # Can also be 0x77
        "MPU6050": 0x68,  # Can also be 0x69
        "ADS1115": 0x48,  # Can be 0x48-0x4B
    }

    def validate(self, diagram: Diagram) -> list[ValidationIssue]:
        """Validate a diagram and return all issues found.

        Args:
            diagram: The diagram to validate

        Returns:
            List of validation issues (errors, warnings, info)
        """
        issues: list[ValidationIssue] = []
        issues.extend(self._check_pin_conflicts(diagram))
        issues.extend(self._check_voltage_mismatches(diagram))
        issues.extend(self._check_i2c_address_conflicts(diagram))
        issues.extend(self._check_current_limits(diagram))
        issues.extend(self._check_connection_validity(diagram))
        return issues

    def _check_pin_conflicts(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check for multiple devices connected to the same GPIO pin.

        This checks for duplicate physical pin usage, which is usually an error
        except for pins like power/ground that can be shared.
        """
        issues: list[ValidationIssue] = []
        pin_usage: dict[int, list[str]] = {}

        for conn in diagram.connections:
            if conn.board_pin not in pin_usage:
                pin_usage[conn.board_pin] = []
            pin_usage[conn.board_pin].append(f"{conn.device_name}.{conn.device_pin_name}")

        # Check for conflicts (ignore power/ground pins which can be shared)
        for pin_num, devices in pin_usage.items():
            if len(devices) > 1:
                board_pin = diagram.board.get_pin_by_number(pin_num)
                if board_pin:
                    # Power and ground pins can be shared safely
                    if board_pin.role in (
                        PinRole.POWER_3V3,
                        PinRole.POWER_5V,
                        PinRole.GROUND,
                    ):
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

        for conn in diagram.connections:
            board_pin = diagram.board.get_pin_by_number(conn.board_pin)
            if not board_pin:
                continue

            device = next((d for d in diagram.devices if d.name == conn.device_name), None)
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

    def _check_i2c_address_conflicts(self, diagram: Diagram) -> list[ValidationIssue]:
        """Check for I2C address conflicts between devices.

        Multiple I2C devices on the same bus must have unique addresses.
        """
        issues: list[ValidationIssue] = []

        # Find all devices connected to I2C bus
        i2c_devices: list[str] = []
        for conn in diagram.connections:
            board_pin = diagram.board.get_pin_by_number(conn.board_pin)
            if (
                board_pin
                and board_pin.role in (PinRole.I2C_SDA, PinRole.I2C_SCL)
                and conn.device_name not in i2c_devices
            ):
                i2c_devices.append(conn.device_name)

        # Check for address conflicts using default addresses
        address_usage: dict[int, list[str]] = {}
        for device_name in i2c_devices:
            # Try to determine device type from name
            device_type = None
            for known_type in self.DEFAULT_I2C_ADDRESSES:
                if known_type in device_name:
                    device_type = known_type
                    break

            if device_type:
                addr = self.DEFAULT_I2C_ADDRESSES[device_type]
                if addr not in address_usage:
                    address_usage[addr] = []
                address_usage[addr].append(device_name)

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

        for i, conn in enumerate(diagram.connections, 1):
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

            # Check device exists
            device = next((d for d in diagram.devices if d.name == conn.device_name), None)
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
