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

from pinviz.model import Board, Component, PinRole


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

    # Available GPIO pins (physical pin numbers)
    available_gpio: list[int] = field(default_factory=list)


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

    # Roles that have a single fixed pin on most boards
    FIXED_ROLES = frozenset(
        {
            PinRole.UART_TX,
            PinRole.UART_RX,
            PinRole.PCM_CLK,
            PinRole.PCM_FS,
            PinRole.PCM_DIN,
            PinRole.PCM_DOUT,
            PinRole.I2C_EEPROM,
        }
    )

    def __init__(self, board: Board):
        """Initialize the pin assigner with a board.

        Args:
            board: Board object whose pins define available assignments.
        """
        self._pin_map = board.pins_by_role()
        self.state = PinAllocationState(
            available_gpio=list(self._pin_map.get(PinRole.GPIO, [])),
        )
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
        self.state = PinAllocationState(
            available_gpio=list(self._pin_map.get(PinRole.GPIO, [])),
        )
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
            board_pin = self._assign_from_candidates(self._pin_map.get(PinRole.PWM, []))
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
        elif pin_role in self.FIXED_ROLES:
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
            board_pin = self.state.available_gpio.pop(0)
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
        pins = self._pin_map.get(pin_role, [])
        if not pins:
            return None
        board_pin = pins[0]
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
            sda_pins = self._pin_map.get(PinRole.I2C_SDA, [])
            scl_pins = self._pin_map.get(PinRole.I2C_SCL, [])
            if not sda_pins or not scl_pins:
                warnings.append(f"Error: Board has no I2C pins for {device_name}")
                return warnings
            self.state.i2c_sda_pin = sda_pins[0]
            self.state.i2c_scl_pin = scl_pins[0]
            self.state.used_pins.add(self.state.i2c_sda_pin)
            self.state.used_pins.add(self.state.i2c_scl_pin)

        self.state.i2c_devices.append(device_name)

        # Assign each device pin
        for pin in device["pins"]:
            pin_name = pin["name"]
            pin_role = PinRole(pin["role"])

            if pin_role == PinRole.I2C_SDA:
                self._append_assignment(self.state.i2c_sda_pin, device_name, pin_name, pin_role)
            elif pin_role == PinRole.I2C_SCL:
                self._append_assignment(self.state.i2c_scl_pin, device_name, pin_name, pin_role)
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
            mosi_pins = self._pin_map.get(PinRole.SPI_MOSI, [])
            miso_pins = self._pin_map.get(PinRole.SPI_MISO, [])
            sclk_pins = self._pin_map.get(PinRole.SPI_SCLK, [])
            if not mosi_pins or not sclk_pins:
                warnings.append(f"Error: Board has no SPI pins for {device_name}")
                return warnings
            self.state.spi_mosi_pin = mosi_pins[0]
            self.state.spi_miso_pin = miso_pins[0] if miso_pins else None
            self.state.spi_sclk_pin = sclk_pins[0]
            self.state.used_pins.add(self.state.spi_mosi_pin)
            if self.state.spi_miso_pin is not None:
                self.state.used_pins.add(self.state.spi_miso_pin)
            self.state.used_pins.add(self.state.spi_sclk_pin)

        # Assign chip select (CE0 or CE1)
        ce0_pins = self._pin_map.get(PinRole.SPI_CE0, [])
        ce1_pins = self._pin_map.get(PinRole.SPI_CE1, [])
        ce_pin = None
        if not self.state.spi_ce0_assigned and ce0_pins:
            ce_pin = ce0_pins[0]
            self.state.spi_ce0_assigned = True
            self.state.used_pins.add(ce_pin)
        elif not self.state.spi_ce1_assigned and ce1_pins:
            ce_pin = ce1_pins[0]
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
                self._append_assignment(self.state.spi_mosi_pin, device_name, pin_name, pin_role)
            elif pin_role == PinRole.SPI_MISO:
                self._append_assignment(self.state.spi_miso_pin, device_name, pin_name, pin_role)
            elif pin_role == PinRole.SPI_SCLK:
                self._append_assignment(self.state.spi_sclk_pin, device_name, pin_name, pin_role)
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
        pins = self._pin_map.get(role, [])
        if not pins:
            raise ValueError(f"Board has no pins for role: {role}")
        if role == PinRole.POWER_3V3:
            self.state.power_3v3_count += 1
            return pins[(self.state.power_3v3_count - 1) % len(pins)]
        elif role == PinRole.POWER_5V:
            self.state.power_5v_count += 1
            return pins[(self.state.power_5v_count - 1) % len(pins)]
        else:
            raise ValueError(f"Invalid power role: {role}")

    def _assign_ground_pin(self) -> int:
        """Assign a ground pin."""
        pins = self._pin_map.get(PinRole.GROUND, [])
        if not pins:
            raise ValueError("Board has no ground pins")
        self.state.ground_count += 1
        return pins[(self.state.ground_count - 1) % len(pins)]
