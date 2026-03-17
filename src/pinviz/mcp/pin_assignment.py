"""
Intelligent Pin Assignment for PinViz MCP Server.

This module implements algorithms for automatic pin assignment, handling:
- GPIO availability tracking
- I2C bus sharing
- SPI chip select allocation
- Power rail distribution
- Conflict detection and resolution
"""

from dataclasses import dataclass, field
from typing import Protocol

from pinviz.model import Component, PinRole


@dataclass
class PinAssignment:
    """A single pin-to-pin assignment."""

    board_pin_number: int  # Physical pin number on board
    device_name: str  # Name of device
    device_pin_name: str  # Pin name on device
    pin_role: PinRole  # Role of the pin
    components: list[Component] = field(default_factory=list)  # Inline components on wire


@dataclass
class PinAllocationState:
    """Tracks which pins are allocated and which are available."""

    # Tracks used pin numbers
    used_pins: set[int] = field(default_factory=set)

    # I2C bus tracking (multiple devices can share I2C)
    i2c_sda_pin: int | None = None
    i2c_scl_pin: int | None = None
    i2c_devices: list[str] = field(default_factory=list)

    # SPI bus tracking
    spi_mosi_pin: int | None = None
    spi_miso_pin: int | None = None
    spi_sclk_pin: int | None = None
    spi_ce0_assigned: bool = False
    spi_ce1_assigned: bool = False

    # Power rail tracking (count of devices using each)
    power_3v3_count: int = 0
    power_5v_count: int = 0
    ground_count: int = 0

    # Available GPIO pins (BCM numbers)
    available_gpio: list[int] = field(
        default_factory=lambda: [
            2,
            3,
            4,
            17,
            27,
            22,
            10,
            9,
            11,
            5,
            6,
            13,
            19,
            26,
            14,
            15,
            18,
            23,
            24,
            25,
            8,
            7,
            12,
            16,
            20,
            21,
        ]
    )


class PinAssignmentStrategy(Protocol):
    """Strategy interface for protocol-specific device assignment."""

    def assign(self, assigner: "PinAssigner", devices: list[dict]) -> list[str]:
        """Assign pins for a group of devices."""


class I2CPinAssignmentStrategy:
    """Assign pins for devices on the shared I2C bus."""

    def assign(self, assigner: "PinAssigner", devices: list[dict]) -> list[str]:
        warnings = []
        for device in devices:
            warnings.extend(assigner._assign_i2c_device(device))
        return warnings


class SPIPinAssignmentStrategy:
    """Assign pins for SPI devices with shared bus lines and unique chip selects."""

    def assign(self, assigner: "PinAssigner", devices: list[dict]) -> list[str]:
        warnings = []
        spi_devices = list(devices)

        if len(spi_devices) > 2:
            warnings.append(
                f"Warning: {len(spi_devices)} SPI devices requested, "
                f"but only 2 chip selects available (CE0, CE1)"
            )
            spi_devices = spi_devices[:2]

        for device in spi_devices:
            warnings.extend(assigner._assign_spi_device(device))

        return warnings


class DefaultPinAssignmentStrategy:
    """Assign pins for devices using direct GPIO and support pins."""

    def assign(self, assigner: "PinAssigner", devices: list[dict]) -> list[str]:
        warnings = []
        for device in devices:
            warnings.extend(assigner._assign_gpio_device(device))
        return warnings


class PinAssigner:
    """
    Intelligent pin assignment algorithm.

    Automatically assigns board pins to device pins based on their roles,
    handling shared buses (I2C, SPI) and preventing conflicts.
    """

    # Pin mappings for Raspberry Pi 5 (physical pin number -> BCM GPIO)
    GPIO_BCM_TO_PHYSICAL = {
        2: 3,
        3: 5,
        4: 7,
        17: 11,
        27: 13,
        22: 15,
        10: 19,
        9: 21,
        11: 23,
        5: 29,
        6: 31,
        13: 33,
        19: 35,
        26: 37,
        14: 8,
        15: 10,
        18: 12,
        23: 16,
        24: 18,
        25: 22,
        8: 24,
        7: 26,
        12: 32,
        16: 36,
        20: 38,
        21: 40,
    }

    # Fixed special pins
    I2C_SDA_PIN = 3  # Physical pin 3 (GPIO2/SDA1)
    I2C_SCL_PIN = 5  # Physical pin 5 (GPIO3/SCL1)
    SPI_MOSI_PIN = 19  # Physical pin 19 (GPIO10)
    SPI_MISO_PIN = 21  # Physical pin 21 (GPIO9)
    SPI_SCLK_PIN = 23  # Physical pin 23 (GPIO11)
    SPI_CE0_PIN = 24  # Physical pin 24 (GPIO8)
    SPI_CE1_PIN = 26  # Physical pin 26 (GPIO7)

    # Power pins (multiple available)
    POWER_3V3_PINS = [1, 17]  # Physical pins 1, 17
    POWER_5V_PINS = [2, 4]  # Physical pins 2, 4
    GROUND_PINS = [6, 9, 14, 20, 25, 30, 34, 39]  # Physical GND pins
    PWM_PINS = [32, 33, 12, 35]  # Physical PWM-capable pins
    FIXED_ROLE_PINS = {
        PinRole.UART_TX: 8,
        PinRole.UART_RX: 10,
        PinRole.PCM_CLK: 12,
        PinRole.PCM_FS: 35,
        PinRole.PCM_DIN: 38,
        PinRole.PCM_DOUT: 40,
        PinRole.I2C_EEPROM: 27,
    }

    def __init__(self):
        """Initialize the pin assigner."""
        self.state = PinAllocationState()
        self.assignments: list[PinAssignment] = []
        self._strategies: dict[str, PinAssignmentStrategy] = {
            "I2C": I2CPinAssignmentStrategy(),
            "SPI": SPIPinAssignmentStrategy(),
        }
        self._default_strategy = DefaultPinAssignmentStrategy()

    def assign_pins(self, devices_data: list[dict]) -> tuple[list[PinAssignment], list[str]]:
        """
        Assign board pins to all devices.

        Args:
            devices_data: List of device dictionaries from database

        Returns:
            Tuple of (assignments, warnings)
            - assignments: List of PinAssignment objects
            - warnings: List of warning messages
        """
        self.state = PinAllocationState()
        self.assignments = []
        warnings = []

        grouped_devices = {"I2C": [], "SPI": [], "DEFAULT": []}
        for device_data in devices_data:
            strategy_key = self._get_strategy_key(device_data)
            grouped_devices[strategy_key].append(device_data)

        for strategy_key, devices in grouped_devices.items():
            if not devices:
                continue

            strategy = (
                self._default_strategy
                if strategy_key == "DEFAULT"
                else self._strategies[strategy_key]
            )
            warnings.extend(strategy.assign(self, devices))

        # Check for power overload
        if self.state.power_3v3_count > 4:
            warnings.append(
                f"Warning: {self.state.power_3v3_count} devices using 3.3V. "
                f"Check total current draw."
            )
        if self.state.power_5v_count > 4:
            warnings.append(
                f"Warning: {self.state.power_5v_count} devices using 5V. Check total current draw."
            )

        return self.assignments, warnings

    def _get_strategy_key(self, device_data: dict) -> str:
        protocols = device_data.get("protocols", [])
        if "I2C" in protocols:
            return "I2C"
        if "SPI" in protocols:
            return "SPI"
        return "DEFAULT"

    def _append_assignment(
        self,
        board_pin_number: int,
        device_name: str,
        device_pin_name: str,
        pin_role: PinRole,
    ) -> None:
        self.assignments.append(
            PinAssignment(
                board_pin_number=board_pin_number,
                device_name=device_name,
                device_pin_name=device_pin_name,
                pin_role=pin_role,
            )
        )

    def _assign_general_pin(
        self,
        device_name: str,
        pin_name: str,
        pin_role: PinRole,
    ) -> list[str]:
        warnings = []

        if pin_role == PinRole.GPIO:
            board_pin = self._assign_gpio_pin()
            if board_pin is None:
                warnings.append(f"Error: No GPIO pins available for {device_name}/{pin_name}")
            else:
                self._append_assignment(board_pin, device_name, pin_name, pin_role)
        elif pin_role == PinRole.PWM:
            board_pin = self._assign_from_candidates(self.PWM_PINS)
            if board_pin is None:
                warnings.append(f"Warning: No PWM pins available for {device_name}/{pin_name}")
            else:
                self._append_assignment(board_pin, device_name, pin_name, pin_role)
        elif pin_role == PinRole.POWER_3V3:
            self._append_assignment(
                self._assign_power_pin(PinRole.POWER_3V3),
                device_name,
                pin_name,
                pin_role,
            )
        elif pin_role == PinRole.POWER_5V:
            self._append_assignment(
                self._assign_power_pin(PinRole.POWER_5V),
                device_name,
                pin_name,
                pin_role,
            )
        elif pin_role == PinRole.GROUND:
            self._append_assignment(self._assign_ground_pin(), device_name, pin_name, pin_role)
        elif pin_role in self.FIXED_ROLE_PINS:
            board_pin = self._assign_fixed_role_pin(pin_role)
            if board_pin is None:
                warnings.append(
                    f"Warning: Fixed {pin_role.value} pin unavailable for {device_name}/{pin_name}"
                )
            else:
                self._append_assignment(board_pin, device_name, pin_name, pin_role)
        else:
            warnings.append(
                f"Warning: Unsupported pin role {pin_role.value} for {device_name}/{pin_name}"
            )

        return warnings

    def _assign_gpio_pin(self) -> int | None:
        while self.state.available_gpio:
            gpio_bcm = self.state.available_gpio.pop(0)
            board_pin = self.GPIO_BCM_TO_PHYSICAL[gpio_bcm]
            if board_pin in self.state.used_pins:
                continue

            self.state.used_pins.add(board_pin)
            return board_pin

        return None

    def _assign_from_candidates(self, candidate_pins: list[int]) -> int | None:
        for board_pin in candidate_pins:
            if board_pin not in self.state.used_pins:
                self.state.used_pins.add(board_pin)
                return board_pin
        return None

    def _assign_fixed_role_pin(self, pin_role: PinRole) -> int | None:
        board_pin = self.FIXED_ROLE_PINS[pin_role]
        if board_pin in self.state.used_pins:
            return None

        self.state.used_pins.add(board_pin)
        return board_pin

    def _assign_i2c_device(self, device: dict) -> list[str]:
        """Assign pins for an I2C device."""
        warnings = []
        device_name = device["name"]

        # Assign I2C bus pins (shared across all I2C devices)
        if self.state.i2c_sda_pin is None:
            self.state.i2c_sda_pin = self.I2C_SDA_PIN
            self.state.i2c_scl_pin = self.I2C_SCL_PIN
            self.state.used_pins.add(self.I2C_SDA_PIN)
            self.state.used_pins.add(self.I2C_SCL_PIN)

        self.state.i2c_devices.append(device_name)

        # Assign each device pin
        for pin in device["pins"]:
            pin_name = pin["name"]
            pin_role = PinRole(pin["role"])

            if pin_role == PinRole.I2C_SDA:
                self._append_assignment(self.I2C_SDA_PIN, device_name, pin_name, pin_role)
            elif pin_role == PinRole.I2C_SCL:
                self._append_assignment(self.I2C_SCL_PIN, device_name, pin_name, pin_role)
            else:
                warnings.extend(self._assign_general_pin(device_name, pin_name, pin_role))

        # Check for I2C address conflicts
        if len(self.state.i2c_devices) > 1:
            # Would need to check I2C addresses from device data
            device_addr = device.get("i2c_address")
            if device_addr:
                warnings.append(
                    f"Info: {device_name} uses I2C address {device_addr}. Ensure no conflicts."
                )

        return warnings

    def _assign_spi_device(self, device: dict) -> list[str]:
        """Assign pins for an SPI device."""
        warnings = []
        device_name = device["name"]

        # Assign SPI bus pins (shared)
        if self.state.spi_mosi_pin is None:
            self.state.spi_mosi_pin = self.SPI_MOSI_PIN
            self.state.spi_miso_pin = self.SPI_MISO_PIN
            self.state.spi_sclk_pin = self.SPI_SCLK_PIN
            self.state.used_pins.add(self.SPI_MOSI_PIN)
            self.state.used_pins.add(self.SPI_MISO_PIN)
            self.state.used_pins.add(self.SPI_SCLK_PIN)

        # Assign chip select (CE0 or CE1)
        ce_pin = None
        if not self.state.spi_ce0_assigned:
            ce_pin = self.SPI_CE0_PIN
            self.state.spi_ce0_assigned = True
            self.state.used_pins.add(ce_pin)
        elif not self.state.spi_ce1_assigned:
            ce_pin = self.SPI_CE1_PIN
            self.state.spi_ce1_assigned = True
            self.state.used_pins.add(ce_pin)
        else:
            warnings.append(f"Error: No chip select available for {device_name}")
            return warnings

        # Assign each device pin
        for pin in device["pins"]:
            pin_name = pin["name"]
            pin_role = PinRole(pin["role"])

            if pin_role == PinRole.SPI_MOSI:
                self._append_assignment(self.SPI_MOSI_PIN, device_name, pin_name, pin_role)
            elif pin_role == PinRole.SPI_MISO:
                self._append_assignment(self.SPI_MISO_PIN, device_name, pin_name, pin_role)
            elif pin_role == PinRole.SPI_SCLK:
                self._append_assignment(self.SPI_SCLK_PIN, device_name, pin_name, pin_role)
            elif pin_role in (PinRole.SPI_CE0, PinRole.SPI_CE1):
                # Use the assigned CE pin
                self._append_assignment(ce_pin, device_name, pin_name, pin_role)
            else:
                warnings.extend(self._assign_general_pin(device_name, pin_name, pin_role))

        return warnings

    def _assign_gpio_device(self, device: dict) -> list[str]:
        """Assign pins for a GPIO-based device."""
        warnings = []
        device_name = device["name"]

        for pin in device["pins"]:
            pin_name = pin["name"]
            pin_role = PinRole(pin["role"])
            warnings.extend(self._assign_general_pin(device_name, pin_name, pin_role))

        return warnings

    def _assign_power_pin(self, role: PinRole) -> int:
        """Assign a power pin (3.3V or 5V)."""
        if role == PinRole.POWER_3V3:
            self.state.power_3v3_count += 1
            # Alternate between available 3.3V pins
            return self.POWER_3V3_PINS[(self.state.power_3v3_count - 1) % len(self.POWER_3V3_PINS)]
        elif role == PinRole.POWER_5V:
            self.state.power_5v_count += 1
            # Alternate between available 5V pins
            return self.POWER_5V_PINS[(self.state.power_5v_count - 1) % len(self.POWER_5V_PINS)]
        else:
            raise ValueError(f"Invalid power role: {role}")

    def _assign_ground_pin(self) -> int:
        """Assign a ground pin."""
        self.state.ground_count += 1
        # Alternate between available ground pins
        return self.GROUND_PINS[(self.state.ground_count - 1) % len(self.GROUND_PINS)]
