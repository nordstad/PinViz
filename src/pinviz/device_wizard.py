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
    Choice("sensors", "Sensors (temperature, light, motion, etc.)"),
    Choice("leds", "LEDs and lighting"),
    Choice("displays", "Displays (OLED, LCD, etc.)"),
    Choice("io", "Input/Output (buttons, switches, etc.)"),
    Choice("other", "Other"),
]

# Common pin roles with descriptions
PIN_ROLES = [
    Choice("3V3", "3.3V power supply (PinRole.POWER_3V3)"),
    Choice("5V", "5V power supply (PinRole.POWER_5V)"),
    Choice("GND", "Ground (PinRole.GROUND)"),
    Choice("GPIO", "General Purpose I/O (PinRole.GPIO)"),
    Choice("I2C_SDA", "I2C Serial Data (PinRole.I2C_SDA)"),
    Choice("I2C_SCL", "I2C Serial Clock (PinRole.I2C_SCL)"),
    Choice("SPI_MOSI", "SPI Master Out Slave In (PinRole.SPI_MOSI)"),
    Choice("SPI_MISO", "SPI Master In Slave Out (PinRole.SPI_MISO)"),
    Choice("SPI_SCLK", "SPI Serial Clock (PinRole.SPI_SCLK)"),
    Choice("SPI_CE0", "SPI Chip Enable 0 (PinRole.SPI_CE0)"),
    Choice("SPI_CE1", "SPI Chip Enable 1 (PinRole.SPI_CE1)"),
    Choice("UART_TX", "UART Transmit (PinRole.UART_TX)"),
    Choice("UART_RX", "UART Receive (PinRole.UART_RX)"),
    Choice("PWM", "Pulse Width Modulation (PinRole.PWM)"),
    Choice("PCM_CLK", "PCM Audio Clock (PinRole.PCM_CLK)"),
    Choice("PCM_FS", "PCM Frame Sync (PinRole.PCM_FS)"),
    Choice("PCM_DIN", "PCM Data In (PinRole.PCM_DIN)"),
    Choice("PCM_DOUT", "PCM Data Out (PinRole.PCM_DOUT)"),
    Choice("I2C_EEPROM", "I2C EEPROM (PinRole.I2C_EEPROM)"),
]

# Pin name patterns for auto-suggestion
# Maps common pin name patterns to suggested roles
PIN_NAME_HINTS: dict[tuple[str, ...], list[str]] = {
    # Power pins (variable voltage inputs like VIN, VCC)
    ("vin", "vcc", "v+", "vdd", "vbus"): ["5V", "3V3"],
    # Ground pins (removed "g" to avoid false matches like "gpio")
    ("gnd", "ground", "v-", "vss"): ["GND"],
    # I2C pins
    ("sda", "sdio", "sdi_i2c"): ["I2C_SDA"],
    ("scl", "sck_i2c", "scl_i2c"): ["I2C_SCL"],
    # SPI pins
    ("mosi", "sdi", "copi", "dout"): ["SPI_MOSI"],
    ("miso", "sdo", "cipo", "din"): ["SPI_MISO"],
    ("sck", "sclk", "clk", "sck_spi"): ["SPI_SCLK"],
    ("cs", "ce", "ce0", "ss"): ["SPI_CE0"],
    ("ce1",): ["SPI_CE1"],
    # UART pins
    ("tx", "txd", "uart_tx"): ["UART_TX"],
    ("rx", "rxd", "uart_rx"): ["UART_RX"],
    # PWM pins
    ("pwm",): ["PWM"],
    # Special case: explicit voltage pins
    ("3v3", "3.3v", "vcc_3v3"): ["3V3"],
    ("5v", "vcc_5v"): ["5V"],
}

# Contextual hints for ambiguous pin names
# Provides inline help when users enter certain pin names
PIN_CONTEXT_HINTS: dict[tuple[str, ...], str] = {
    ("vin", "vcc", "vdd", "vbus"): (
        "💡 VIN/VCC accepts flexible power (3-5V). For Raspberry Pi, typically use 3V3."
    ),
    ("addr", "address", "a0", "a1", "a2"): (
        "💡 Address pin for I2C - usually tied to GND or 3V3 to set device address."
    ),
    ("en", "enable", "ce", "chip_enable"): (
        "💡 Enable/Chip Enable - controls when device is active (usually tie to 3V3)."
    ),
    ("rst", "reset", "res"): (
        "💡 Reset pin - usually pulled high to 3V3 or controlled by a GPIO pin."
    ),
    ("int", "interrupt", "irq"): ("💡 Interrupt pin - connects to a GPIO pin to signal events."),
    ("3vo", "3v3_out", "vout"): (
        "💡 Voltage output - this pin PROVIDES 3.3V, don't connect it to power."
    ),
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
            regex = r"(?:^|[_\-])" + re.escape(pattern) + r"(?:[_\-]|$)"
            if re.search(regex, pin_lower):
                return hint
    return None


def get_role_choices_for_pin(pin_name: str, detected_i2c: bool = False) -> list[Choice]:
    """Get role choices with suggestions prioritized based on pin name.

    Uses word boundary matching to avoid false positives. Patterns must appear
    as complete words (at start/end or separated by underscore/hyphen), not as
    arbitrary substrings within other words.

    Args:
        pin_name: The name of the pin to get role choices for

    Returns:
        List of Choice objects with suggested roles marked and placed first

    Examples:
        >>> get_role_choices_for_pin("VIN")  # Matches - suggests 5V, 3V3
        >>> get_role_choices_for_pin("SDA")  # Matches - suggests I2C_SDA
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
            #        (?:[_\-]|$) = underscore/hyphen or end of string
            regex = r"(?:^|[_\-])" + re.escape(pattern) + r"(?:[_\-]|$)"
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
            # Note: Choice.title = short name (1st param), .value = description (2nd param)
            matching_choice = next((c for c in PIN_ROLES if c.title == role), None)
            if matching_choice:
                # Build description with context
                base_desc = matching_choice.value.split("(")[0].strip()

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
                        role,
                        f"⭐ {base_desc}{context} (suggested)",
                    )
                )

        # Add separator
        choices.append(Choice("separator", "─" * 40, disabled=True))

        # Add remaining roles (not already suggested)
        choices.extend([c for c in PIN_ROLES if c.title not in suggested_roles])

        return choices

    # No suggestions, return original list
    return list(PIN_ROLES)


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
