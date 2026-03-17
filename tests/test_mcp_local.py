#!/usr/bin/env python3
"""Local MCP pipeline tests.

These tests also support direct script execution for quick local diagnostics.
"""

import sys
import tempfile
from pathlib import Path

try:
    from pinviz.mcp.connection_builder import ConnectionBuilder
    from pinviz.mcp.device_manager import DeviceManager
    from pinviz.mcp.parser import PromptParser
    from pinviz.mcp.pin_assignment import PinAssigner
    from pinviz.render_svg import SVGRenderer
except ModuleNotFoundError:
    # Allow running this file directly without editable install.
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from pinviz.mcp.connection_builder import ConnectionBuilder
    from pinviz.mcp.device_manager import DeviceManager
    from pinviz.mcp.parser import PromptParser
    from pinviz.mcp.pin_assignment import PinAssigner
    from pinviz.render_svg import SVGRenderer


def test_device_manager():
    """Device manager basic behavior."""
    dm = DeviceManager()

    all_devices = dm.search_devices()
    sensors = dm.search_devices(category="sensor")
    i2c_devices = dm.search_devices(protocol="I2C")
    bme280 = dm.get_device_by_name("BME280")

    assert len(all_devices) > 0
    assert len(sensors) > 0
    assert len(i2c_devices) > 0
    assert bme280 is not None
    assert bme280.name.startswith("BME280")


def test_prompt_parser():
    """Natural-language parser should extract board/devices."""
    parser = PromptParser()

    test_prompts = [
        "Connect BME280 and BH1750",
        "I need a temperature sensor",
        "LED and button",
    ]

    for prompt in test_prompts:
        result = parser.parse(prompt)
        assert result.board
        assert isinstance(result.devices, list)


def test_pin_assignment():
    """I2C devices should share SDA/SCL bus pins."""
    dm = DeviceManager()
    assigner = PinAssigner()

    bme280 = dm.get_device_by_name("BME280")
    bh1750 = dm.get_device_by_name("BH1750")
    assert bme280 is not None
    assert bh1750 is not None

    devices = [bme280.to_dict(), bh1750.to_dict()]
    assignments, _warnings = assigner.assign_pins(devices)

    i2c_sda_pins = set()
    i2c_scl_pins = set()
    for assignment in assignments:
        if assignment.pin_role.name == "I2C_SDA":
            i2c_sda_pins.add(assignment.board_pin_number)
        elif assignment.pin_role.name == "I2C_SCL":
            i2c_scl_pins.add(assignment.board_pin_number)

    assert len(i2c_sda_pins) == 1
    assert len(i2c_scl_pins) == 1


def test_diagram_generation(tmp_path):
    """Prompt-to-diagram pipeline should produce an SVG."""
    prompt = "Connect BME280 sensor and LED"
    output_file = tmp_path / "test_mcp_output.svg"

    dm = DeviceManager()
    parser = PromptParser()
    assigner = PinAssigner()
    builder = ConnectionBuilder()
    renderer = SVGRenderer()

    parsed = parser.parse(prompt)
    device_specs = []
    for device_name in parsed.devices:
        device = dm.get_device_by_name(device_name)
        if device:
            device_specs.append(device.to_dict())

    assert device_specs

    assignments, _warnings = assigner.assign_pins(device_specs)
    diagram = builder.build_diagram(
        assignments=assignments,
        devices_data=device_specs,
        title=prompt,
        board_name=parsed.board,
    )
    renderer.render(diagram, output_file)

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_database_summary():
    """Database should expose non-empty category/protocol groupings."""
    dm = DeviceManager()

    categories = {}
    protocols = {}

    for device in dm.search_devices():
        categories[device.category] = categories.get(device.category, 0) + 1
        for protocol in device.protocols:
            protocols[protocol] = protocols.get(protocol, 0) + 1

    assert categories
    assert protocols
    assert len(dm.search_devices()) > 0


def main():
    """Run all MCP local tests manually."""
    print("=" * 70)
    print("PinViz MCP Server - Local Testing")
    print("=" * 70)

    def _run_diagram_generation():
        with tempfile.TemporaryDirectory() as tmpdir:
            test_diagram_generation(Path(tmpdir))

    tests = [
        ("Device Manager", test_device_manager),
        ("Prompt Parser", test_prompt_parser),
        ("Pin Assignment", test_pin_assignment),
        ("Diagram Generation", _run_diagram_generation),
        ("Database Summary", test_database_summary),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, True))
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\n{passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
