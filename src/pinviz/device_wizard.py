"""Interactive device configuration wizard for pinviz."""

import json
import re
import sys
from pathlib import Path

import questionary
from questionary import Choice

from .devices import get_registry

# Available device categories
CATEGORIES = [
    Choice(title="Sensors (temperature, light, motion, etc.)", value="sensors"),
    Choice(title="LEDs and lighting", value="leds"),
    Choice(title="Displays (OLED, LCD, etc.)", value="displays"),
    Choice(title="Input/Output (buttons, switches, etc.)", value="io"),
    Choice(title="Other", value="other"),
]

# Common pin roles with descriptions
PIN_ROLES = [
    Choice(title="3.3V power supply (PinRole.POWER_3V3)", value="3V3"),
    Choice(title="5V power supply (PinRole.POWER_5V)", value="5V"),
    Choice(title="Ground (PinRole.GROUND)", value="GND"),
    Choice(title="General Purpose I/O (PinRole.GPIO)", value="GPIO"),
    Choice(title="I2C Serial Data (PinRole.I2C_SDA)", value="I2C_SDA"),
    Choice(title="I2C Serial Clock (PinRole.I2C_SCL)", value="I2C_SCL"),
    Choice(title="SPI Master Out Slave In (PinRole.SPI_MOSI)", value="SPI_MOSI"),
    Choice(title="SPI Master In Slave Out (PinRole.SPI_MISO)", value="SPI_MISO"),
    Choice(title="SPI Serial Clock (PinRole.SPI_SCLK)", value="SPI_SCLK"),
    Choice(title="SPI Chip Enable 0 (PinRole.SPI_CE0)", value="SPI_CE0"),
    Choice(title="SPI Chip Enable 1 (PinRole.SPI_CE1)", value="SPI_CE1"),
    Choice(title="UART Transmit (PinRole.UART_TX)", value="UART_TX"),
    Choice(title="UART Receive (PinRole.UART_RX)", value="UART_RX"),
    Choice(title="Pulse Width Modulation (PinRole.PWM)", value="PWM"),
    Choice(title="PCM Audio Clock (PinRole.PCM_CLK)", value="PCM_CLK"),
    Choice(title="PCM Frame Sync (PinRole.PCM_FS)", value="PCM_FS"),
    Choice(title="PCM Data In (PinRole.PCM_DIN)", value="PCM_DIN"),
    Choice(title="PCM Data Out (PinRole.PCM_DOUT)", value="PCM_DOUT"),
    Choice(title="I2C EEPROM (PinRole.I2C_EEPROM)", value="I2C_EEPROM"),
]

# Pin name patterns for auto-suggestion
# Maps common pin name patterns to suggested roles
# IMPORTANT: More specific patterns must come BEFORE generic patterns
# due to first-match-wins strategy
PIN_NAME_HINTS: dict[tuple[str, ...], list[str]] = {
    # Special case: explicit voltage pins (MUST come before generic power pins)
    ("3v3", "3.3v", "vcc_3v3"): ["3V3"],
    ("5v", "vcc_5v"): ["5V"],
    # Power pins (variable voltage inputs like VIN, VCC)
    ("vin", "vcc", "v+", "vdd", "vbus"): ["5V", "3V3"],
    # Ground pins (removed "g" to avoid false matches like "gpio")
    ("gnd", "ground", "v-", "vss"): ["GND"],
    # I2C pins
    ("sda", "sdio", "sdi_i2c"): ["I2C_SDA"],
    ("scl", "sck_i2c", "scl_i2c"): ["I2C_SCL"],
    # SPI pins
    ("mosi", "copi"): ["SPI_MOSI"],
    ("miso", "cipo"): ["SPI_MISO"],
    # Ambiguous SPI data pins (perspective-dependent)
    ("sdi",): ["SPI_MISO", "SPI_MOSI"],  # Could be either depending on device perspective
    ("sdo",): ["SPI_MOSI", "SPI_MISO"],  # Could be either depending on device perspective
    ("din",): ["SPI_MISO", "SPI_MOSI"],  # Could be either depending on device perspective
    ("dout",): ["SPI_MOSI", "SPI_MISO"],  # Could be either depending on device perspective
    ("sck", "sclk", "sck_spi"): ["SPI_SCLK"],
    ("clk",): ["SPI_SCLK", "PWM", "GPIO"],  # Ambiguous - could be SPI, PWM, or generic clock
    ("cs", "ce", "ce0", "ss"): ["SPI_CE0"],
    ("ce1",): ["SPI_CE1"],
    # UART pins
    ("tx", "txd", "uart_tx", "serial_tx", "txd0"): ["UART_TX"],
    ("rx", "rxd", "uart_rx", "serial_rx", "rxd0"): ["UART_RX"],
    # PWM pins
    ("pwm",): ["PWM"],
}

# Contextual hints for ambiguous pin names
# Provides inline help when users enter certain pin names
PIN_CONTEXT_HINTS: dict[tuple[str, ...], str] = {
    # Power input pins
    ("vin", "vcc", "vdd", "vbus"): (
        "💡 VIN/VCC accepts flexible power (3-5V). For Raspberry Pi, typically use 3V3."
    ),
    ("vbat",): ("💡 Battery backup power - different from VIN, usually for RTC or backup memory."),
    # Power output pins
    ("3vo", "3v3_out", "vout"): (
        "💡 Voltage output - this pin PROVIDES 3.3V, don't connect it to power."
    ),
    ("ioref",): ("💡 I/O reference voltage indicator - OUTPUT pin showing logic level (Arduino)."),
    # I2C address selection pins
    ("addr", "address", "a0", "a1", "a2", "sa0", "ad0", "ado"): (
        "💡 Address pin for I2C - usually tied to GND or 3V3 to set device address."
    ),
    # SPI chip select
    ("cs", "ss"): ("💡 Chip Select / Slave Select for SPI - connect to GPIO or SPI_CE0/CE1."),
    # SPI data pins with perspective ambiguity
    ("din", "dout", "sdi", "sdo"): (
        "💡 Data In/Out - for SPI: DIN=MOSI, DOUT=MISO; may vary by device perspective."
    ),
    # Display control pins
    ("dc", "d/c", "rs"): (
        "💡 Data/Command pin for displays - connect to GPIO to control display mode."
    ),
    # Clock pins
    ("clk",): ("💡 Clock signal - for SPI use SPI_SCLK, otherwise connect to GPIO."),
    # Enable/control pins
    ("en", "enable", "chip_enable"): (
        "💡 Enable/Chip Enable - controls when device is active (usually tie to 3V3)."
    ),
    ("ce",): ("💡 Chip Enable - for SPI use SPI_CE0/CE1, otherwise tie to 3V3 or GPIO."),
    ("run",): ("💡 Run/Enable pin for microcontrollers - tie to 3V3 or use for reset control."),
    ("shdn", "shutdown"): (
        "💡 Shutdown control - tie to 3V3 for normal operation, GND to shutdown."
    ),
    # Reset pins
    ("rst", "reset", "res"): (
        "💡 Reset pin - usually pulled high to 3V3 or controlled by a GPIO pin."
    ),
    # Interrupt/status pins
    ("int", "interrupt", "irq"): ("💡 Interrupt pin - connects to a GPIO pin to signal events."),
    ("drdy", "rdy", "busy"): (
        "💡 Data Ready/Busy status pin - connect to GPIO to read device status."
    ),
    # Boot mode pins
    ("boot", "boot0"): ("💡 Boot mode selection - usually tie to GND for normal operation."),
    # Ground variations
    ("agnd", "dgnd"): ("💡 Analog/Digital Ground - connect BOTH to GND (star ground if possible)."),
    # Write protect
    ("wp",): ("💡 Write Protect pin - tie to GND to allow writes, 3V3 to protect (EEPROMs/flash)."),
    # No connect / test pins
    ("nc",): ("💡 No Connect - leave unconnected (do NOT wire this pin)."),
    ("test",): ("💡 Factory test pin - leave unconnected for normal operation."),
}


def get_context_hint_for_pin(pin_name: str) -> str | None:
    """Get contextual hint for a pin name if available.

    Args:
        pin_name: The name of the pin to get context hint for

    Returns:
        Hint string if available, None otherwise
    """
    pin_lower = pin_name.lower().strip()

    # Check if pin matches any hint patterns
    for patterns, hint in PIN_CONTEXT_HINTS.items():
        for pattern in patterns:
            # Use same word boundary matching as role suggestions
            # Allow digits after pattern to match "SCL1", "SDA2", etc.
            regex = r"(?:^|[_\-])" + re.escape(pattern) + r"(?:[_\-\d]|$)"
            if re.search(regex, pin_lower):
                return hint
    return None


def get_role_choices_for_pin(pin_name: str, detected_i2c: bool = False) -> list[Choice]:
    """Get role choices with suggestions prioritized based on pin name.

    Uses word boundary matching to avoid false positives. Patterns must appear
    as complete words (at start/end or separated by underscore/hyphen), not as
    arbitrary substrings within other words.

    Pattern matching uses first-match-wins strategy: patterns are checked in the
    order defined in PIN_NAME_HINTS, so pattern order determines priority when
    multiple patterns could match. More specific patterns should be defined before
    more generic ones.

    Args:
        pin_name: The name of the pin to get role choices for
        detected_i2c: Whether I2C pins have already been configured

    Returns:
        List of Choice objects with suggested roles marked and placed first

    Examples:
        >>> get_role_choices_for_pin("VIN")  # Matches - suggests 5V, 3V3
        >>> get_role_choices_for_pin("SDA")  # Matches - suggests I2C_SDA
        >>> get_role_choices_for_pin("SCL1")  # Matches with numbers - suggests I2C_SCL
        >>> get_role_choices_for_pin("DISCONNECT")  # No match - contains "sco" but not as word
    """
    pin_lower = pin_name.lower().strip()

    # Find matching suggestions using word boundary matching
    # Patterns are checked in order; first match wins
    suggested_roles: list[str] = []
    for patterns, roles in PIN_NAME_HINTS.items():
        for pattern in patterns:
            # Match pattern as whole word or separated by underscore/hyphen
            # Regex: (?:^|[_\-]) = start of string or underscore/hyphen
            #        pattern = the literal pattern to match
            #        (?:[_\-\d]|$) = underscore/hyphen/digit or end of string
            # This allows matching "SCL1", "SDA2", "UART2_TX", etc.
            regex = r"(?:^|[_\-])" + re.escape(pattern) + r"(?:[_\-\d]|$)"
            if re.search(regex, pin_lower):
                suggested_roles = roles
                break
        if suggested_roles:
            break

    # If we have suggestions, reorder the choices
    if suggested_roles:
        choices: list[Choice] = []

        # Add suggested roles first with ⭐ marker and context
        for role in suggested_roles:
            # Find matching choice to get the base description
            matching_choice = next((c for c in PIN_ROLES if c.value == role), None)
            if matching_choice:
                # Build description with context
                base_desc = matching_choice.title.split("(")[0].strip()

                # Add context based on role and whether I2C was detected
                context = ""
                if role == "3V3":
                    if detected_i2c:
                        context = " - recommended for I2C devices on Raspberry Pi"
                    else:
                        context = " - for Raspberry Pi 3.3V rail"
                elif role == "5V":
                    context = " - for Arduino/5V power sources"

                choices.append(
                    Choice(
                        title=f"⭐ {base_desc}{context} (suggested)",
                        value=role,
                    )
                )

        # Add separator
        choices.append(Choice(title="─" * 40, value="separator", disabled=True))

        # Add remaining roles (not already suggested).
        # Create fresh Choice objects to avoid shortcut_key pollution: questionary
        # mutates Choice.shortcut_key in-place during select rendering, so reusing
        # the global PIN_ROLES objects across multiple select calls causes duplicate
        # shortcut key errors on subsequent pins.
        choices.extend(
            [
                Choice(title=c.title, value=c.value)
                for c in PIN_ROLES
                if c.value not in suggested_roles
            ]
        )

        return choices

    # No suggestions — return fresh copies for the same reason
    return [Choice(title=c.title, value=c.value) for c in PIN_ROLES]


def validate_device_id(device_id: str) -> bool:
    """Validate device ID format.

    Args:
        device_id: Device identifier to validate

    Returns:
        True if valid (lowercase alphanumeric with underscores/hyphens only)
    """
    if not device_id:
        return False
    # Must be lowercase alphanumeric with underscores or hyphens
    return all(c.isalnum() or c in ("_", "-") for c in device_id) and device_id[0].isalpha()


def validate_i2c_address(address: str) -> bool:
    """Validate I2C address format.

    Args:
        address: I2C address to validate

    Returns:
        True if valid hex format (0xNN)
    """
    if not address:
        return True  # Optional field
    # Must be hex format like 0x76
    if not address.startswith("0x"):
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False


def validate_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid URL format
    """
    if not url:
        return True  # Optional field
    return url.startswith(("http://", "https://"))


def check_duplicate_device_id(device_id: str) -> bool:
    """Check if device ID already exists in registry.

    Args:
        device_id: Device identifier to check

    Returns:
        True if device ID already exists
    """
    registry = get_registry()
    try:
        registry.create(device_id)
        return True  # Device exists
    except (KeyError, ValueError):
        return False  # Device doesn't exist


async def run_wizard() -> dict | None:
    """Run interactive device configuration wizard.

    Returns:
        Device configuration dict, or None if cancelled
    """
    print("\n🚀 Device Configuration Wizard")
    print("=" * 60)
    print("This wizard will help you create a new device configuration.")
    print("Press Ctrl+C at any time to cancel.\n")

    try:
        # Basic device information
        device_name = await questionary.text(
            "Device name (e.g., 'BME280 Environmental Sensor'):",
            validate=lambda text: len(text) > 0 or "Device name cannot be empty",
        ).ask_async()

        if device_name is None:
            return None

        device_id = await questionary.text(
            "Device ID (lowercase, alphanumeric with underscores, e.g., 'bme280'):",
            validate=lambda text: validate_device_id(text) or "Invalid ID format",
        ).ask_async()

        if device_id is None:
            return None

        # Check for duplicates
        if check_duplicate_device_id(device_id):
            print(f"\n⚠️  Warning: Device ID '{device_id}' already exists in registry!")
            overwrite = await questionary.confirm(
                "Do you want to continue anyway? (will create duplicate in different location)"
            ).ask_async()
            if not overwrite:
                return None

        category = await questionary.select(
            "Device category:",
            choices=CATEGORIES,
        ).ask_async()

        if category is None:
            return None

        description = await questionary.text(
            "Short description (optional, press Enter to skip):",
            default="",
        ).ask_async()

        if description is None:
            return None

        # Pin configuration
        print("\n📌 Pin Configuration")
        print("-" * 60)

        num_pins = await questionary.text(
            "Number of pins:",
            validate=lambda text: text.isdigit() and int(text) > 0 or "Must be a positive integer",
        ).ask_async()

        if num_pins is None:
            return None

        num_pins = int(num_pins)
        pins = []

        for i in range(num_pins):
            print(f"\nPin {i + 1}:")

            pin_name = await questionary.text(
                "  Name (e.g., 'VCC', 'SDA', 'CTRL'):",
                validate=lambda text: len(text) > 0 or "Pin name cannot be empty",
            ).ask_async()

            if pin_name is None:
                return None

            # Show contextual hint if available
            hint = get_context_hint_for_pin(pin_name)
            if hint:
                print(f"  {hint}")

            # Detect if we've already seen I2C pins
            detected_i2c = any(pin["role"] in ["I2C_SDA", "I2C_SCL"] for pin in pins)

            # Get role choices with suggestions based on pin name
            role_choices = get_role_choices_for_pin(pin_name, detected_i2c=detected_i2c)

            pin_role = await questionary.select(
                "  Role:",
                choices=role_choices,
            ).ask_async()

            if pin_role is None:
                return None

            pins.append({"name": pin_name, "role": pin_role})

        # Optional metadata
        print("\n📝 Optional Metadata")
        print("-" * 60)

        i2c_address = await questionary.text(
            "I2C address (e.g., '0x76', press Enter to skip):",
            default="",
            validate=lambda text: validate_i2c_address(text) or "Invalid I2C address format",
        ).ask_async()

        if i2c_address is None:
            return None

        datasheet_url = await questionary.text(
            "Datasheet URL (press Enter to skip):",
            default="",
            validate=lambda text: validate_url(text) or "Invalid URL format",
        ).ask_async()

        if datasheet_url is None:
            return None

        notes = await questionary.text(
            "Setup notes (e.g., 'Requires 4.7kΩ pull-up resistor', press Enter to skip):",
            default="",
        ).ask_async()

        if notes is None:
            return None

        # Build configuration dict
        config = {
            "id": device_id,
            "name": device_name,
            "category": category,
            "pins": pins,
        }

        # Add optional fields
        if description:
            config["description"] = description
        if i2c_address:
            config["i2c_address"] = i2c_address
        if datasheet_url:
            config["datasheet_url"] = datasheet_url
        if notes:
            config["notes"] = notes

        # Preview
        print("\n📄 Configuration Preview")
        print("-" * 60)
        print(json.dumps(config, indent=2))
        print()

        # Confirm
        confirm = await questionary.confirm(
            "Save this configuration?",
            default=True,
        ).ask_async()

        if not confirm:
            print("❌ Configuration cancelled.")
            return None

        return config

    except KeyboardInterrupt:
        print("\n\n❌ Wizard cancelled by user.")
        return None


def print_wiring_summary(config: dict) -> None:
    """Print a helpful wiring summary for the configured device.

    Args:
        config: Device configuration dict with pins
    """
    pins = config.get("pins", [])
    if not pins:
        return

    # Detect device characteristics
    has_i2c = any(pin["role"] in ["I2C_SDA", "I2C_SCL"] for pin in pins)
    has_spi = any(
        pin["role"] in ["SPI_MOSI", "SPI_MISO", "SPI_SCLK", "SPI_CE0", "SPI_CE1"] for pin in pins
    )
    has_uart = any(pin["role"] in ["UART_TX", "UART_RX"] for pin in pins)

    # Raspberry Pi pin mapping
    rpi_pins = {
        "3V3": "Pin 1 or 17",
        "5V": "Pin 2 or 4",
        "GND": "Pin 6, 9, 14, 20, 25, 30, 34, or 39",
        "I2C_SDA": "Pin 3 (GPIO 2)",
        "I2C_SCL": "Pin 5 (GPIO 3)",
        "SPI_MOSI": "Pin 19 (GPIO 10)",
        "SPI_MISO": "Pin 21 (GPIO 9)",
        "SPI_SCLK": "Pin 23 (GPIO 11)",
        "SPI_CE0": "Pin 24 (GPIO 8)",
        "SPI_CE1": "Pin 26 (GPIO 7)",
        "UART_TX": "Pin 8 (GPIO 14)",
        "UART_RX": "Pin 10 (GPIO 15)",
    }

    print("\n" + "=" * 60)
    print("📋 Quick Wiring Guide for Raspberry Pi")
    print("=" * 60)
    print(f"\n{'Device Pin':<15} {'Role':<12} {'Connect To'}")
    print("-" * 60)

    for pin in pins:
        pin_name = pin["name"]
        pin_role = pin["role"]
        rpi_connection = rpi_pins.get(pin_role, "See GPIO pinout")

        print(f"{pin_name:<15} {pin_role:<12} {rpi_connection}")

    # Add protocol-specific tips
    if has_i2c:
        i2c_addr = config.get("i2c_address", "")
        print("\n💡 I2C Device Tips:")
        print("   • Enable I2C: sudo raspi-config → Interface Options → I2C")
        print("   • Test connection: i2cdetect -y 1")
        if i2c_addr:
            print(f"   • Expected address: {i2c_addr}")

    if has_spi:
        print("\n💡 SPI Device Tips:")
        print("   • Enable SPI: sudo raspi-config → Interface Options → SPI")

    if has_uart:
        print("\n💡 UART Device Tips:")
        print("   • Enable serial: sudo raspi-config → Interface Options → Serial")
        print("   • Disable console over serial if needed")

    print("\n" + "=" * 60 + "\n")


def save_device_config(config: dict, output_path: Path | None = None) -> Path:
    """Save device configuration to JSON file.

    Args:
        config: Device configuration dict
        output_path: Optional custom output path. If None, saves to
                     device_configs/{category}/{id}.json

    Returns:
        Path where configuration was saved
    """
    if output_path is None:
        # Default path: src/pinviz/device_configs/{category}/{id}.json
        # Find src/pinviz directory
        module_dir = Path(__file__).parent
        device_configs_dir = module_dir / "device_configs" / config["category"]
        device_configs_dir.mkdir(parents=True, exist_ok=True)
        output_path = device_configs_dir / f"{config['id']}.json"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")  # Add trailing newline

    return output_path


def test_device_config(device_id: str) -> bool:
    """Test loading the newly created device.

    Args:
        device_id: Device identifier to test

    Returns:
        True if device loads successfully
    """
    try:
        registry = get_registry()
        device = registry.create(device_id)
        print("\n✅ Device loaded successfully:")
        print(f"   Name: {device.name}")
        print(f"   Pins: {len(device.pins)}")
        for pin in device.pins:
            print(f"     - {pin.name} ({pin.role.value})")
        return True
    except Exception as e:
        print(f"\n❌ Failed to load device: {e}")
        return False


def print_contribution_message(config: dict, output_path: Path) -> None:
    """Print message encouraging users to contribute their device config.

    Args:
        config: Device configuration dict
        output_path: Path where the device config was saved
    """
    device_id = config["id"]
    device_name = config["name"]
    category = config["category"]

    # Get relative path from project root
    relative_path = f"src/pinviz/device_configs/{category}/{device_id}.json"

    print("\n" + "=" * 60)
    print("📤 Contribute this device to help other users!")
    print("=" * 60)
    print("\nQuick contribution steps:")
    print()
    print("# 1. Fork and clone")
    print("gh repo fork nordstad/PinViz --clone")
    print("cd PinViz")
    print()
    print("# 2. Copy your device config")
    print(f"cp {output_path} \\")
    print(f"   {relative_path}")
    print()
    print("# 3. Create PR")
    print(f"git checkout -b add-{device_id}-device")
    print(f"git add {relative_path}")
    print(f'git commit -m "feat: add {device_name}"')
    print(f"git push -u origin add-{device_id}-device")
    print(f'gh pr create --title "feat: add {device_name}" --body "Adds support for {device_name}"')
    print()
    print("Full guide: https://pinviz.dev/contributing/devices")
    print("=" * 60 + "\n")


async def main() -> int:
    """Main wizard entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    config = await run_wizard()

    if config is None:
        return 1

    try:
        output_path = save_device_config(config)
        print(f"\n✅ Configuration saved to: {output_path}")

        # Test loading the device
        print("\n🔍 Testing device configuration...")
        if test_device_config(config["id"]):
            print(f"\n🎉 Success! Device '{config['id']}' is ready to use.")

            # Show wiring summary
            print_wiring_summary(config)

            print("Usage:")
            print(f"  Python: registry.create('{config['id']}')")
            print(f'  YAML:   type: "{config["id"]}"')

            # Show contribution message
            print_contribution_message(config, output_path)

            return 0
        else:
            print(f"\n⚠️  Device saved but failed to load. Check configuration at {output_path}")
            return 1

    except Exception as e:
        print(f"\n❌ Error saving configuration: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(main()))
