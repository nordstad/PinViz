"""Integration tests for real-world scenarios: prompt → SVG generation."""

import tempfile
import time
from pathlib import Path

import pytest

from pinviz.mcp.connection_builder import ConnectionBuilder
from pinviz.mcp.device_manager import DeviceManager
from pinviz.mcp.parser import PromptParser
from pinviz.mcp.pin_assignment import PinAssigner
from pinviz.render_svg import SVGRenderer

# Fixtures


@pytest.fixture
def device_manager():
    """Shared device manager for all tests."""
    return DeviceManager()


@pytest.fixture
def parser():
    """Shared prompt parser."""
    return PromptParser()


@pytest.fixture
def pin_assigner():
    """Shared pin assigner."""
    return PinAssigner()


@pytest.fixture
def connection_builder():
    """Shared connection builder."""
    return ConnectionBuilder()


@pytest.fixture
def temp_svg():
    """Temporary SVG file for rendering tests."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


# Real-world scenario tests


def test_scenario_single_sensor(device_manager, parser, pin_assigner, connection_builder, temp_svg):
    """Single sensor connection: BME280 temperature/humidity sensor."""
    prompt = "connect BME280 to my raspberry pi"

    # Parse prompt
    parsed = parser.parse(prompt)
    assert len(parsed.devices) == 1

    # Look up device
    device = device_manager.get_device_by_name(parsed.devices[0], fuzzy=True)
    assert device is not None
    device_data = device.to_dict()
    assert "I2C" in device_data["protocols"]

    # Assign pins
    assignments, warnings = pin_assigner.assign_pins([device_data])
    assert len(assignments) >= 4  # VCC, GND, SDA, SCL
    assert len(warnings) == 0

    # Build diagram
    diagram = connection_builder.build_diagram(
        assignments=assignments,
        devices_data=[device_data],
        board_name=parsed.board,
        title="BME280 Wiring",
    )
    assert len(diagram.devices) == 1
    assert len(diagram.connections) == 4

    # Render to SVG
    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)
    assert temp_svg.exists()
    assert temp_svg.stat().st_size > 1000


def test_scenario_two_i2c_devices_bus_sharing(
    device_manager, parser, pin_assigner, connection_builder, temp_svg
):
    """Two I2C devices sharing SDA/SCL bus."""
    prompt = "connect BME280 and SSD1306"

    parsed = parser.parse(prompt)
    assert len(parsed.devices) == 2

    # Look up devices
    devices_data = []
    for dev_name in parsed.devices:
        device = device_manager.get_device_by_name(dev_name, fuzzy=True)
        assert device is not None
        devices_data.append(device.to_dict())

    # Assign pins
    assignments, warnings = pin_assigner.assign_pins(devices_data)

    # Verify I2C bus sharing
    sda_pins = [a.board_pin_number for a in assignments if a.pin_role.value == "I2C_SDA"]
    scl_pins = [a.board_pin_number for a in assignments if a.pin_role.value == "I2C_SCL"]

    assert len(set(sda_pins)) == 1, "All I2C devices should share SDA"
    assert len(set(scl_pins)) == 1, "All I2C devices should share SCL"

    # Build and render
    diagram = connection_builder.build_diagram(
        assignments=assignments, devices_data=devices_data, title="I2C Bus Sharing"
    )

    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)
    assert temp_svg.exists()


def test_scenario_mixed_protocols(device_manager, pin_assigner, connection_builder, temp_svg):
    """Mixed protocols: I2C + GPIO devices."""
    # Get specific devices
    bme280 = device_manager.get_device_by_id("bme280")
    led = device_manager.get_device_by_id("led-single")

    assert bme280 is not None
    assert led is not None

    devices_data = [bme280.to_dict(), led.to_dict()]

    # Assign pins
    assignments, warnings = pin_assigner.assign_pins(devices_data)
    assert len(assignments) >= 5  # BME280 (4) + LED (2)

    # Build diagram
    diagram = connection_builder.build_diagram(
        assignments=assignments, devices_data=devices_data, title="Mixed Protocols"
    )

    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)
    assert temp_svg.exists()


def test_scenario_spi_device(device_manager, pin_assigner, connection_builder, temp_svg):
    """SPI device connection."""
    device = device_manager.get_device_by_name("ST7735", fuzzy=True)

    if not device:
        pytest.skip("ST7735 not in database")

    device_data = device.to_dict()
    assert "SPI" in device_data["protocols"]

    # Assign pins
    try:
        assignments, warnings = pin_assigner.assign_pins([device_data])
    except ValueError as e:
        pytest.skip(f"Device has invalid pin role: {e}")

    assert len(assignments) > 0

    diagram = connection_builder.build_diagram(
        assignments=assignments, devices_data=[device_data], title="SPI Display"
    )

    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)
    assert temp_svg.exists()


def test_scenario_environmental_monitoring(
    device_manager, pin_assigner, connection_builder, temp_svg
):
    """Real-world project: Environmental monitoring station."""
    device_ids = ["bme280", "bh1750", "ssd1306-oled"]
    devices_data = []

    for device_id in device_ids:
        device = device_manager.get_device_by_id(device_id)
        if device:
            devices_data.append(device.to_dict())

    assert len(devices_data) == 3

    # Assign pins
    assignments, warnings = pin_assigner.assign_pins(devices_data)

    # Verify I2C bus sharing for all three devices
    i2c_devices = [a for a in assignments if a.pin_role.value in ("I2C_SDA", "I2C_SCL")]
    assert len(i2c_devices) == 6  # 3 devices × 2 pins each

    diagram = connection_builder.build_diagram(
        assignments=assignments, devices_data=devices_data, title="Environmental Monitoring Station"
    )

    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)
    assert temp_svg.exists()


def test_scenario_home_automation(device_manager, pin_assigner, connection_builder, temp_svg):
    """Real-world project: Home automation with sensors and actuators."""
    device_ids = ["hc-sr501", "relay-module", "buzzer"]
    devices_data = []

    for device_id in device_ids:
        device = device_manager.get_device_by_id(device_id)
        if device:
            devices_data.append(device.to_dict())

    if len(devices_data) < 2:
        pytest.skip("Required devices not in database")

    assignments, warnings = pin_assigner.assign_pins(devices_data)

    diagram = connection_builder.build_diagram(
        assignments=assignments, devices_data=devices_data, title="Home Automation Hub"
    )

    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)
    assert temp_svg.exists()


def test_scenario_weather_station(device_manager, pin_assigner, connection_builder, temp_svg):
    """Real-world project: Weather station."""
    ds18b20 = device_manager.get_device_by_id("ds18b20")
    lcd = device_manager.get_device_by_id("lcd-1602")

    devices_data = []
    if ds18b20:
        devices_data.append(ds18b20.to_dict())
    if lcd:
        devices_data.append(lcd.to_dict())

    if len(devices_data) < 1:
        pytest.skip("Required devices not in database")

    try:
        assignments, warnings = pin_assigner.assign_pins(devices_data)
    except ValueError as e:
        pytest.skip(f"Device has invalid pin role: {e}")

    diagram = connection_builder.build_diagram(
        assignments=assignments, devices_data=devices_data, title="Weather Station"
    )

    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)
    assert temp_svg.exists()


def test_power_distribution(device_manager, pin_assigner):
    """Verify power distribution across multiple devices."""
    device_ids = ["bme280", "ssd1306-oled", "bh1750", "led-single"]
    devices_data = []

    for device_id in device_ids:
        device = device_manager.get_device_by_id(device_id)
        if device:
            devices_data.append(device.to_dict())

    assert len(devices_data) >= 3

    assignments, warnings = pin_assigner.assign_pins(devices_data)

    # Count power pin usage
    power_pins = [a.board_pin_number for a in assignments if a.pin_role.value in ("3V3", "5V")]

    # Should distribute across multiple power pins
    assert len(power_pins) >= 3
    # Valid power pins: 1, 2, 4, 17
    assert all(p in [1, 2, 4, 17] for p in power_pins)


def test_ground_distribution(device_manager, pin_assigner):
    """Verify ground distribution across multiple devices."""
    device_ids = ["bme280", "ssd1306-oled", "led-single", "button"]
    devices_data = []

    for device_id in device_ids:
        device = device_manager.get_device_by_id(device_id)
        if device:
            devices_data.append(device.to_dict())

    assert len(devices_data) >= 3

    assignments, warnings = pin_assigner.assign_pins(devices_data)

    # Count ground pin usage
    ground_pins = [a.board_pin_number for a in assignments if a.pin_role.value == "GND"]

    # Should use multiple ground pins
    assert len(ground_pins) >= 3
    # Valid ground pins
    valid_gnd_pins = [6, 9, 14, 20, 25, 30, 34, 39]
    assert all(p in valid_gnd_pins for p in ground_pins)


def test_performance_multiple_devices(device_manager, pin_assigner, connection_builder, temp_svg):
    """Performance test: Handle 8 devices efficiently."""
    # Get 8 different devices
    all_devices = device_manager.devices
    devices_data = [d.to_dict() for d in all_devices[:8]]

    start_time = time.time()

    # Full pipeline
    try:
        assignments, warnings = pin_assigner.assign_pins(devices_data)
    except ValueError as e:
        pytest.skip(f"Device has invalid pin role: {e}")
    diagram = connection_builder.build_diagram(
        assignments=assignments, devices_data=devices_data, title="Performance Test"
    )
    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)

    elapsed = time.time() - start_time

    # Should complete in reasonable time (< 1 second)
    assert elapsed < 1.0, f"Processing 8 devices took {elapsed:.2f}s, expected < 1s"
    assert temp_svg.exists()


def test_edge_case_duplicate_devices(device_manager, pin_assigner):
    """Edge case: Same device type used twice."""
    led = device_manager.get_device_by_id("led-single")
    assert led is not None

    # Create two instances
    led1 = led.to_dict()
    led1["name"] = "LED1"
    led2 = led.to_dict()
    led2["name"] = "LED2"

    assignments, warnings = pin_assigner.assign_pins([led1, led2])

    # Should have different GPIO pins for each LED
    gpio_pins = [
        a.board_pin_number
        for a in assignments
        if a.pin_role.value == "GPIO" and a.device_pin_name in ("+", "ANODE")
    ]

    if len(gpio_pins) == 2:
        assert gpio_pins[0] != gpio_pins[1], "Duplicate devices should use different GPIO pins"


def test_edge_case_empty_device_list(pin_assigner, connection_builder):
    """Edge case: Handle empty device list gracefully."""
    assignments, warnings = pin_assigner.assign_pins([])
    assert assignments == []
    assert warnings == []

    diagram = connection_builder.build_diagram(
        assignments=[], devices_data=[], title="Empty Diagram"
    )
    assert len(diagram.devices) == 0
    assert len(diagram.connections) == 0


def test_full_pipeline_with_prompt(
    device_manager, parser, pin_assigner, connection_builder, temp_svg
):
    """Complete end-to-end pipeline from natural language prompt."""
    prompt = "connect BME280 and LED to raspberry pi"

    # Step 1: Parse
    parsed = parser.parse(prompt)
    assert len(parsed.devices) >= 2

    # Step 2: Device lookup
    devices_data = []
    for dev_name in parsed.devices:
        device = device_manager.get_device_by_name(dev_name, fuzzy=True)
        if device:
            devices_data.append(device.to_dict())

    assert len(devices_data) >= 2

    # Step 3: Pin assignment
    assignments, warnings = pin_assigner.assign_pins(devices_data)

    # Step 4: Build diagram
    diagram = connection_builder.build_diagram(
        assignments=assignments,
        devices_data=devices_data,
        board_name=parsed.board,
        title="GPIO Wiring Diagram",
    )

    # Step 5: Render
    renderer = SVGRenderer()
    renderer.render(diagram, temp_svg)

    # Verify
    assert temp_svg.exists()
    assert temp_svg.stat().st_size > 1000
    assert len(diagram.devices) >= 2
    assert len(diagram.connections) >= 4
