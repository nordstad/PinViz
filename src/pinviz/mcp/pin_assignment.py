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

from pinviz.model import PinRole


@dataclass
class PinAssignment:
    """A single pin-to-pin assignment."""

    board_pin_number: int  # Physical pin number on board
    device_name: str  # Name of device
    device_pin_name: str  # Pin name on device
    pin_role: PinRole  # Role of the pin


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

    def __init__(self):
        """Initialize the pin assigner."""
        self.state = PinAllocationState()
        self.assignments: list[PinAssignment] = []

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

        # First pass: Identify device protocols and requirements
        i2c_devices = []
        spi_devices = []
        gpio_devices = []

        for device_data in devices_data:
            protocols = device_data.get("protocols", [])
            if "I2C" in protocols:
                i2c_devices.append(device_data)
            elif "SPI" in protocols:
                spi_devices.append(device_data)
            else:
                gpio_devices.append(device_data)

        # Check SPI device limit
        if len(spi_devices) > 2:
            warnings.append(
                f"Warning: {len(spi_devices)} SPI devices requested, "
                f"but only 2 chip selects available (CE0, CE1)"
            )
            spi_devices = spi_devices[:2]  # Limit to 2

        # Assign I2C devices (they share the bus)
        for device in i2c_devices:
            device_warnings = self._assign_i2c_device(device)
            warnings.extend(device_warnings)

        # Assign SPI devices (they share MOSI/MISO/SCLK but need separate CE)
        for device in spi_devices:
            device_warnings = self._assign_spi_device(device)
            warnings.extend(device_warnings)

        # Assign GPIO-based devices
        for device in gpio_devices:
            device_warnings = self._assign_gpio_device(device)
            warnings.extend(device_warnings)

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
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=self.I2C_SDA_PIN,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.I2C_SCL:
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=self.I2C_SCL_PIN,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.POWER_3V3:
                board_pin = self._assign_power_pin(PinRole.POWER_3V3)
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.POWER_5V:
                board_pin = self._assign_power_pin(PinRole.POWER_5V)
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.GROUND:
                board_pin = self._assign_ground_pin()
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )

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
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=self.SPI_MOSI_PIN,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.SPI_MISO:
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=self.SPI_MISO_PIN,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.SPI_SCLK:
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=self.SPI_SCLK_PIN,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role in (PinRole.SPI_CE0, PinRole.SPI_CE1):
                # Use the assigned CE pin
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=ce_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.POWER_3V3:
                board_pin = self._assign_power_pin(PinRole.POWER_3V3)
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.POWER_5V:
                board_pin = self._assign_power_pin(PinRole.POWER_5V)
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.GROUND:
                board_pin = self._assign_ground_pin()
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )

        return warnings

    def _assign_gpio_device(self, device: dict) -> list[str]:
        """Assign pins for a GPIO-based device."""
        warnings = []
        device_name = device["name"]

        for pin in device["pins"]:
            pin_name = pin["name"]
            pin_role = PinRole(pin["role"])

            if pin_role == PinRole.GPIO:
                # Allocate a free GPIO pin
                if not self.state.available_gpio:
                    warnings.append(f"Error: No GPIO pins available for {device_name}/{pin_name}")
                    continue

                gpio_bcm = self.state.available_gpio.pop(0)
                board_pin = self.GPIO_BCM_TO_PHYSICAL[gpio_bcm]
                self.state.used_pins.add(board_pin)

                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.POWER_3V3:
                board_pin = self._assign_power_pin(PinRole.POWER_3V3)
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.POWER_5V:
                board_pin = self._assign_power_pin(PinRole.POWER_5V)
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.GROUND:
                board_pin = self._assign_ground_pin()
                self.assignments.append(
                    PinAssignment(
                        board_pin_number=board_pin,
                        device_name=device_name,
                        device_pin_name=pin_name,
                        pin_role=pin_role,
                    )
                )
            elif pin_role == PinRole.PWM:
                # PWM pins are specific GPIO pins that support PWM
                # GPIO12 (pin 32), GPIO13 (pin 33), GPIO18 (pin 12), GPIO19 (pin 35)
                pwm_pins = [12, 33, 12, 35]  # Physical pins
                assigned = False
                for pwm_pin in pwm_pins:
                    if pwm_pin not in self.state.used_pins:
                        self.state.used_pins.add(pwm_pin)
                        self.assignments.append(
                            PinAssignment(
                                board_pin_number=pwm_pin,
                                device_name=device_name,
                                device_pin_name=pin_name,
                                pin_role=pin_role,
                            )
                        )
                        assigned = True
                        break

                if not assigned:
                    warnings.append(f"Warning: No PWM pins available for {device_name}/{pin_name}")

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
