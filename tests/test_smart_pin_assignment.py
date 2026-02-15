"""Tests for smart pin assignment feature."""

import yaml

from pinviz import boards
from pinviz.config_loader import ConfigLoader
from pinviz.model import PinRole


def test_board_pin_role_gnd_assignment():
    """Test that board_pin_role assigns GND pins correctly."""
    config_yaml = """
    title: "Test GND Distribution"
    board: "esp8266_nodemcu"
    devices:
      - type: "led"
        name: "LED1"
      - type: "led"
        name: "LED2"
    connections:
      - board_pin_role: "GND"
        device: "LED1"
        device_pin: "-"
      - board_pin_role: "GND"
        device: "LED2"
        device_pin: "-"
    """
    loader = ConfigLoader()
    config_dict = yaml.safe_load(config_yaml)
    diagram = loader.load_from_dict(config_dict)

    # Check that connections were assigned to different GND pins
    assert len(diagram.connections) == 2
    assert diagram.connections[0].board_pin != diagram.connections[1].board_pin

    # Verify both pins are GND
    board = boards.load_board_from_config("esp8266_nodemcu")
    pin1 = board.get_pin_by_number(diagram.connections[0].board_pin)
    pin2 = board.get_pin_by_number(diagram.connections[1].board_pin)
    assert pin1.role == PinRole.GROUND
    assert pin2.role == PinRole.GROUND


def test_board_pin_role_3v3_assignment():
    """Test that board_pin_role assigns 3V3 pins correctly."""
    config_yaml = """
    title: "Test 3V3 Distribution"
    board: "esp8266_nodemcu"
    devices:
      - type: "bh1750"
        name: "Sensor1"
      - type: "bh1750"
        name: "Sensor2"
    connections:
      - board_pin_role: "3V3"
        device: "Sensor1"
        device_pin: "VCC"
      - board_pin_role: "3V3"
        device: "Sensor2"
        device_pin: "VCC"
    """
    loader = ConfigLoader()
    config_dict = yaml.safe_load(config_yaml)
    diagram = loader.load_from_dict(config_dict)

    # Check that connections were assigned
    assert len(diagram.connections) == 2

    # Verify both pins are 3V3
    board = boards.load_board_from_config("esp8266_nodemcu")
    pin1 = board.get_pin_by_number(diagram.connections[0].board_pin)
    pin2 = board.get_pin_by_number(diagram.connections[1].board_pin)
    assert pin1.role == PinRole.POWER_3V3
    assert pin2.role == PinRole.POWER_3V3


def test_board_pin_role_round_robin():
    """Test that pin assignment cycles through available pins."""
    config_yaml = """
    title: "Test Round Robin"
    board: "esp8266_nodemcu"
    devices:
      - type: "led"
        name: "LED1"
      - type: "led"
        name: "LED2"
      - type: "led"
        name: "LED3"
      - type: "led"
        name: "LED4"
      - type: "led"
        name: "LED5"
    connections:
      - board_pin_role: "GND"
        device: "LED1"
        device_pin: "-"
      - board_pin_role: "GND"
        device: "LED2"
        device_pin: "-"
      - board_pin_role: "GND"
        device: "LED3"
        device_pin: "-"
      - board_pin_role: "GND"
        device: "LED4"
        device_pin: "-"
      - board_pin_role: "GND"
        device: "LED5"
        device_pin: "-"
    """
    loader = ConfigLoader()
    config_dict = yaml.safe_load(config_yaml)
    diagram = loader.load_from_dict(config_dict)

    # ESP8266 NodeMCU has 4 GND pins, so 5th connection should wrap around
    assert len(diagram.connections) == 5

    # First 4 should be unique, 5th should reuse first
    assigned_pins = [conn.board_pin for conn in diagram.connections]
    assert assigned_pins[0] == assigned_pins[4]  # Round robin


def test_esp32_board_svg_scale():
    """Test ESP32 board loads with svg_scale attribute."""
    board = boards.load_board_from_config("esp32_devkit_v1")
    assert board is not None
    assert hasattr(board, "svg_scale")
    assert board.svg_scale > 0


def test_esp8266_board_dual_sided_layout():
    """Test ESP8266 NodeMCU dual-sided layout."""
    board = boards.load_board_from_config("esp8266_nodemcu")

    # Verify pins are on both sides (different X coordinates)
    x_coords = {pin.position.x for pin in board.pins if pin.position}
    assert len(x_coords) >= 2, "Should have pins on both sides"


def test_wemos_d1_mini_compact_board():
    """Test Wemos D1 Mini compact board loads correctly."""
    board = boards.load_board_from_config("wemos_d1_mini")
    assert board is not None
    assert len(board.pins) == 16
    assert board.width < 120  # Compact form factor (smaller than standard Pi boards)
