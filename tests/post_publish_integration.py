"""Post-publish integration tests - single source of truth for CI and validation.

This module contains integration tests that are used by both:
1. Local validation script (scripts/validate-post-publish-tests.sh)
2. GitHub Actions workflow (.github/workflows/publish.yml)

By maintaining a single source of truth, we avoid test drift and flaky failures.
"""

import sys
import tempfile
from pathlib import Path

from pinviz import Connection, Diagram, SVGRenderer, boards
from pinviz.config_loader import ConfigLoader
from pinviz.devices import get_registry
from pinviz.validation import DiagramValidator, ValidationLevel


def test_core_imports():
    """Test that all core modules can be imported."""
    # Already imported above, but verify key attributes exist
    assert hasattr(boards, "raspberry_pi_5")
    assert Connection is not None
    assert Diagram is not None
    assert SVGRenderer is not None
    print("✓ Core imports work")


def test_basic_api():
    """Test basic diagram creation with registry API."""
    with tempfile.TemporaryDirectory() as tmpdir:
        board = boards.raspberry_pi_5()
        registry = get_registry()
        led = registry.create("led", color_name="Red")
        connections = [
            Connection(11, "Red LED", "+"),
            Connection(6, "Red LED", "-"),
        ]
        diagram = Diagram("Test", board, [led], connections)
        renderer = SVGRenderer()

        output_path = Path(tmpdir) / "test.svg"
        renderer.render(diagram, str(output_path))

        assert output_path.exists(), "SVG file should be created"
        assert output_path.stat().st_size > 0, "SVG file should not be empty"
        print("✓ Basic API works correctly")


def test_device_templates():
    """Test device registry and templates."""
    # Test boards
    rpi5 = boards.raspberry_pi_5()
    rpi4 = boards.raspberry_pi_4()
    assert len(rpi5.pins) == 40, "Raspberry Pi 5 should have 40 pins"
    assert len(rpi4.pins) == 40, "Raspberry Pi 4 should have 40 pins"

    # Test devices using registry - dynamically get available devices
    registry = get_registry()
    available_devices = registry.list_all()
    assert len(available_devices) > 0, "Should have at least one device template"

    # Test a few known devices that should always exist
    required_devices = {
        "bh1750": 5,  # BH1750 should have 5 pins
        "led": 2,  # LED should have 2 pins
        "button": 2,  # Button should have 2 pins
        "ds18b20": 3,  # DS18B20 should have 3 pins
    }

    for device_id, expected_pins in required_devices.items():
        device = registry.create(device_id)
        assert len(device.pins) == expected_pins, (
            f"{device_id} should have {expected_pins} pins, got {len(device.pins)}"
        )

    print("✓ All device templates functional")


def test_validation_api():
    """Test validation Python API."""
    loader = ConfigLoader()
    registry = get_registry()

    # Get a guaranteed available device dynamically
    available_devices = registry.list_all()
    # Look for i2c_device or fall back to first available
    test_device = None
    for device in available_devices:
        if device.type_id == "i2c_device":
            test_device = "i2c_device"
            break
    if not test_device:
        test_device = available_devices[0].type_id if available_devices else "led"

    # Test valid config
    valid_config = {
        "title": "API Test",
        "board": "rpi5",
        "devices": [{"type": test_device, "name": "Sensor"}],
        "connections": [
            {"board_pin": 1, "device": "Sensor", "device_pin": "VCC"},
            {"board_pin": 3, "device": "Sensor", "device_pin": "SDA"},
        ],
    }

    diagram = loader.load_from_dict(valid_config)
    validator = DiagramValidator()
    issues = validator.validate(diagram)

    errors = [i for i in issues if i.level == ValidationLevel.ERROR]
    if len(errors) > 0:
        print(f"✗ Valid config generated {len(errors)} errors:")
        for error in errors:
            print(f"  - {error.message}")
        sys.exit(1)

    # Test invalid config - multiple devices connected to same pin
    invalid_config = {
        "title": "API Test Invalid",
        "board": "rpi5",
        "devices": [
            {"type": "led", "name": "LED1"},
            {"type": "led", "name": "LED2"},
        ],
        "connections": [
            {"board_pin": 11, "device": "LED1", "device_pin": "+"},
            {"board_pin": 11, "device": "LED2", "device_pin": "+"},
        ],
    }

    diagram = loader.load_from_dict(invalid_config)
    issues = validator.validate(diagram)
    errors = [i for i in issues if i.level == ValidationLevel.ERROR]

    if len(errors) == 0:
        print("✗ Invalid config should have generated errors")
        sys.exit(1)

    if "Pin 11" not in errors[0].message:
        print(f"✗ Error message missing pin information: {errors[0].message}")
        sys.exit(1)

    print("✓ Validation API works correctly")


def test_all_examples():
    """Test all built-in examples can be generated."""
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        examples = ["bh1750", "ir_led", "i2c_spi"]
        for example in examples:
            output_path = Path(tmpdir) / f"{example}.svg"

            # Use subprocess to call the CLI
            result = subprocess.run(
                ["pinviz", "example", example, "-o", str(output_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"✗ Example {example} failed:")
                print(result.stderr)
                sys.exit(1)

            assert output_path.exists(), f"Example {example} should generate SVG"
            assert output_path.stat().st_size > 0, f"Example {example} SVG should not be empty"

    print("✓ All examples work correctly")


def test_board_aliases():
    """Test board functions are accessible."""
    # Test that all main board functions exist and work
    rpi5 = boards.raspberry_pi_5()
    rpi4 = boards.raspberry_pi_4()
    pico = boards.raspberry_pi_pico()

    assert rpi5.name == "Raspberry Pi 5"
    assert rpi4.name == "Raspberry Pi 4 Model B"
    assert pico.name == "Raspberry Pi Pico"

    # Verify all have pins
    assert len(rpi5.pins) == 40
    assert len(rpi4.pins) == 40
    assert len(pico.pins) == 40

    print("✓ Board functions work correctly")


def test_wire_styles():
    """Test different wire routing styles."""
    with tempfile.TemporaryDirectory() as tmpdir:
        board = boards.raspberry_pi_5()
        registry = get_registry()
        led = registry.create("led")

        for style in ["orthogonal", "curved", "mixed"]:
            connections = [
                Connection(11, "LED", "+", style=style),
                Connection(6, "LED", "-", style=style),
            ]
            diagram = Diagram(f"Test {style}", board, [led], connections)
            renderer = SVGRenderer()

            output_path = Path(tmpdir) / f"test_{style}.svg"
            renderer.render(diagram, str(output_path))

            assert output_path.exists(), f"Wire style {style} should generate SVG"
            assert output_path.stat().st_size > 0, f"Wire style {style} SVG should not be empty"

    print("✓ Wire styles work correctly")


def run_all_tests():
    """Run all integration tests."""
    print("Running post-publish integration tests...")
    print()

    tests = [
        ("Core imports", test_core_imports),
        ("Basic API", test_basic_api),
        ("Device templates", test_device_templates),
        ("Validation API", test_validation_api),
        ("All examples", test_all_examples),
        ("Board aliases", test_board_aliases),
        ("Wire styles", test_wire_styles),
    ]

    for i, (name, test_func) in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] Testing {name}...")
        try:
            test_func()
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)
        print()

    print("=" * 50)
    print("✓ ALL INTEGRATION TESTS PASSED!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
