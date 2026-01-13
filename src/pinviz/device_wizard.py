"""Interactive device configuration wizard for pinviz."""

import json
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


def get_role_choices_for_pin(pin_name: str) -> list[Choice]:
    """Get role choices with suggestions prioritized based on pin name.

    Args:
        pin_name: The name of the pin to get role choices for

    Returns:
        List of Choice objects with suggested roles marked and placed first
    """
    pin_lower = pin_name.lower().strip()

    # Find matching suggestions
    suggested_roles: list[str] = []
    for patterns, roles in PIN_NAME_HINTS.items():
        if any(pattern in pin_lower for pattern in patterns):
            suggested_roles = roles
            break

    # If we have suggestions, reorder the choices
    if suggested_roles:
        choices: list[Choice] = []

        # Add suggested roles first with ⭐ marker
        for role in suggested_roles:
            # Note: Choice.title = short name (1st param), .value = description (2nd param)
            matching_choice = next((c for c in PIN_ROLES if c.title == role), None)
            if matching_choice:
                choices.append(
                    Choice(
                        role,
                        f"⭐ {matching_choice.value.split('(')[0].strip()} (suggested)",
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

            # Get role choices with suggestions based on pin name
            role_choices = get_role_choices_for_pin(pin_name)

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
            print("\nUsage:")
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
