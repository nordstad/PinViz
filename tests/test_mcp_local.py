#!/usr/bin/env python3
"""Local test script for PinViz MCP Server functionality.

This script tests the MCP server tools without needing Claude Desktop.
"""

import sys
from pathlib import Path

# Add src to path so we can import pinviz.mcp
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pinviz.mcp.connection_builder import ConnectionBuilder
from pinviz.mcp.device_manager import DeviceManager
from pinviz.mcp.parser import PromptParser
from pinviz.mcp.pin_assignment import PinAssigner
from pinviz.render_svg import SVGRenderer


def test_device_manager():
    """Test 1: Device Manager functionality."""
    print("\n" + "=" * 70)
    print("TEST 1: Device Manager - List Devices")
    print("=" * 70)

    dm = DeviceManager()

    # Test listing all devices
    all_devices = dm.search_devices()
    print(f"✓ Total devices in database: {len(all_devices)}")

    # Test filtering by category
    sensors = dm.search_devices(category="sensor")
    print(f"✓ Sensors found: {len(sensors)}")

    # Test filtering by protocol
    i2c_devices = dm.search_devices(protocol="I2C")
    print(f"✓ I2C devices found: {len(i2c_devices)}")

    # Test getting specific device
    bme280 = dm.get_device_by_name("BME280")
    assert bme280 is not None, "BME280 not found"
    print(f"✓ Found BME280: {bme280.name}")
    print(f"  - Category: {bme280.category}")
    print(f"  - Protocols: {', '.join(bme280.protocols)}")
    print(f"  - Pins: {len(bme280.pins)}")


def test_prompt_parser():
    """Test 2: Natural Language Parser."""
    print("\n" + "=" * 70)
    print("TEST 2: Natural Language Parser")
    print("=" * 70)

    parser = PromptParser()

    test_prompts = [
        "Connect BME280 and BH1750",
        "I need a temperature sensor",
        "LED and button",
    ]

    for prompt in test_prompts:
        result = parser.parse(prompt)
        print(f"\n✓ Prompt: '{prompt}'")
        print(f"  Devices found: {result.devices}")
        print(f"  Board: {result.board}")


def test_pin_assignment():
    """Test 3: Pin Assignment Logic."""
    print("\n" + "=" * 70)
    print("TEST 3: Pin Assignment - I2C Bus Sharing")
    print("=" * 70)

    dm = DeviceManager()
    assigner = PinAssigner()

    # Test I2C bus sharing with two sensors
    bme280 = dm.get_device_by_name("BME280")
    bh1750 = dm.get_device_by_name("BH1750")

    assert bme280 is not None, "BME280 not found"
    assert bh1750 is not None, "BH1750 not found"

    devices = [bme280.to_dict(), bh1750.to_dict()]
    assignments, warnings = assigner.assign_pins(devices)

    print(f"✓ Assigned pins: {len(assignments)} assignments")
    print(f"  Warnings: {len(warnings)}")

    # Check I2C bus sharing
    i2c_sda_pins = set()
    i2c_scl_pins = set()
    for assignment in assignments:
        if assignment.pin_role.name == "I2C_SDA":
            i2c_sda_pins.add(assignment.board_pin_number)
        elif assignment.pin_role.name == "I2C_SCL":
            i2c_scl_pins.add(assignment.board_pin_number)

    assert len(i2c_sda_pins) == 1 and len(i2c_scl_pins) == 1, "I2C bus sharing failed"
    print("✓ I2C bus shared correctly:")
    print(f"  - SDA on pin {list(i2c_sda_pins)[0]}")
    print(f"  - SCL on pin {list(i2c_scl_pins)[0]}")


def test_diagram_generation():
    """Test 4: Full Pipeline - Prompt to Diagram."""
    print("\n" + "=" * 70)
    print("TEST 4: Full Pipeline - Generate Diagram from Prompt")
    print("=" * 70)

    prompt = "Connect BME280 sensor and LED"
    output_file = "test_mcp_output.svg"

    print(f"✓ Input prompt: '{prompt}'")
    print(f"✓ Output file: {output_file}")

    # Initialize components
    dm = DeviceManager()
    parser = PromptParser()
    assigner = PinAssigner()
    builder = ConnectionBuilder()
    renderer = SVGRenderer()

    # Step 1: Parse prompt
    parsed = parser.parse(prompt)
    print("\n1. Parse prompt:")
    print(f"   Devices: {parsed.devices}")

    # Step 2: Get device specs
    device_specs = []
    for device_name in parsed.devices:
        device = dm.get_device_by_name(device_name)
        if device:
            device_specs.append(device.to_dict())
            print(f"   ✓ Found: {device.name}")
        else:
            print(f"   ✗ Not found: {device_name}")

    assert len(device_specs) > 0, "No devices found"

    # Step 3: Assign pins
    assignments, warnings = assigner.assign_pins(device_specs)
    print("\n2. Assign pins:")
    print(f"   Assignments: {len(assignments)} devices")
    if warnings:
        print(f"   Warnings: {warnings}")

    # Step 4: Build diagram
    diagram = builder.build_diagram(
        assignments=assignments,
        devices_data=device_specs,
        title=prompt,
        board_name=parsed.board,
    )
    print("\n3. Build diagram:")
    print(f"   Title: {diagram.title}")
    print(f"   Board: {diagram.board.name}")
    print(f"   Devices: {len(diagram.devices)}")
    print(f"   Connections: {len(diagram.connections)}")

    # Step 5: Render SVG
    renderer.render(diagram, output_file)

    assert Path(output_file).exists(), f"Failed to create {output_file}"
    size = Path(output_file).stat().st_size
    print("\n4. Render SVG:")
    print(f"   ✓ File created: {output_file}")
    print(f"   ✓ Size: {size:,} bytes")


def test_database_summary():
    """Test 5: Database Statistics."""
    print("\n" + "=" * 70)
    print("TEST 5: Database Summary")
    print("=" * 70)

    dm = DeviceManager()

    # Count devices by category
    categories = {}
    protocols = {}

    for device in dm.search_devices():
        categories[device.category] = categories.get(device.category, 0) + 1
        for protocol in device.protocols:
            protocols[protocol] = protocols.get(protocol, 0) + 1

    print("\nDevices by Category:")
    for category, count in sorted(categories.items()):
        print(f"  {category:12s}: {count:2d} devices")

    print("\nDevices by Protocol:")
    for protocol, count in sorted(protocols.items()):
        print(f"  {protocol:12s}: {count:2d} devices")

    print(f"\n✓ Total: {len(dm.search_devices())} devices")


def main():
    """Run all MCP server tests."""
    print("=" * 70)
    print("PinViz MCP Server - Local Testing")
    print("=" * 70)

    tests = [
        ("Device Manager", test_device_manager),
        ("Prompt Parser", test_prompt_parser),
        ("Pin Assignment", test_pin_assignment),
        ("Diagram Generation", test_diagram_generation),
        ("Database Summary", test_database_summary),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, success in results if success)

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All MCP server functionality working!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
