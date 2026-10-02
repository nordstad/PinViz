"""Breadboard layout seats stepsticks on the holes and renders headlessly."""

import xml.etree.ElementTree as ET

import pytest

from pinviz.breadboard import (
    PI_ORIGIN,
    PI_SCALE,
    STEPSTICK_LABELS,
    STEPSTICK_LEFT,
    STEPSTICK_RIGHT,
    BreadboardRenderer,
    module_row_offset,
    stepstick_seat,
)
from pinviz.config_loader import ConfigLoader
from pinviz.devices import get_registry
from pinviz.model import Device, LayoutMode
from pinviz.render_svg import SVGRenderer

ONE_DRIVER = """
title: "One stepstick"
board: raspberry_pi_4
layout: breadboard
show_title: true
show_board_name: false
devices:
  - type: breadboard_rail
    name: Rails
    breadboard: {role: rail}
  - type: tmc2209
    name: D1
    breadboard: {role: module}
{extra_devices}
connections:
  - {board_pin: 36, device: D1, device_pin: STEP, color: "#E2B000"}
  - from: {device: Rails, device_pin: "+3V3"}
    to: {device: D1, device_pin: MS1}
    color: "#F08C00"
  - from: {device: Rails, device_pin: "+24V"}
    to: {device: D1, device_pin: VM}
    color: "#D31212"
{extra_connections}
"""


def _render_yaml(tmp_path, text):
    config = tmp_path / "config.yaml"
    config.write_text(text, encoding="utf-8")
    diagram = ConfigLoader(emit_validation_output=False).load_from_file(config)
    output = tmp_path / "config.svg"
    SVGRenderer().render(diagram, output)
    return diagram, output.read_text(encoding="utf-8")


def _render(tmp_path, extra_devices="", extra_connections=""):
    return _render_yaml(
        tmp_path,
        ONE_DRIVER.replace("{extra_devices}", extra_devices).replace(
            "{extra_connections}", extra_connections
        ),
    )


def test_stepstick_seats_as_the_silkscreen_reads():
    """EN top left, DIR bottom left, VM top right, GND bottom right."""
    device = Device(name="D1", pins=[], type_id="tmc2209")
    assert STEPSTICK_LEFT == ("EN", "MS1", "MS2", "PDN", "PDN_ALT", "CLK", "STEP", "DIR")
    assert STEPSTICK_RIGHT == ("VM", "VMGND", "A2", "A1", "B1", "B2", "VDD", "IOGND")
    assert stepstick_seat(device, "EN") == ("b", 0)
    assert stepstick_seat(device, "STEP") == ("b", 6)
    assert stepstick_seat(device, "DIR") == ("b", 7)
    assert stepstick_seat(device, "VM") == ("f", 0)
    assert stepstick_seat(device, "A2") == ("f", 2)
    assert stepstick_seat(device, "VDD") == ("f", 6)
    assert module_row_offset(device, "IOGND") == 7


def test_stepstick_part_matches_the_seat_order():
    """The device JSON lists the pins in the same order the renderer seats them."""
    device = get_registry().create("tmc2209")
    names = tuple(pin.name for pin in device.pins)
    assert names == STEPSTICK_LEFT + STEPSTICK_RIGHT
    assert STEPSTICK_LABELS == {"PDN_ALT": "PDN", "VMGND": "GND", "IOGND": "GND"}


def test_unknown_stepstick_pin_is_rejected():
    device = Device(name="D1", pins=[], type_id="tmc2209")
    with pytest.raises(ValueError, match="no stepstick pin"):
        stepstick_seat(device, "UART")


def test_breadboard_yaml_renders(tmp_path):
    diagram, text = _render(tmp_path)
    assert diagram.layout_mode == LayoutMode.BREADBOARD
    assert "D1" in text
    assert ">36</text>" in text  # header pin numbers are drawn like the schematic
    assert ">STEP D1</text>" in text  # the tag next to header pin 36
    assert "5V open" not in text


def test_capacitor_plugs_into_the_rails(tmp_path):
    _diagram, text = _render(
        tmp_path,
        extra_devices="""  - type: electrolytic
    name: C1
    breadboard: {role: capacitor}""",
        extra_connections="""  - from: {device: C1, device_pin: "+"}
    to: {device: Rails, device_pin: "+24V"}
    color: "#D31212"
  - from: {device: C1, device_pin: "-"}
    to: {device: Rails, device_pin: MGND}
    color: "#1A1A1A\"""",
    )
    assert "C1" in text
    assert "stripe (-) on MGND" in text
    assert "+ on +24V" in text


def test_floating_part_fails_the_render(tmp_path):
    with pytest.raises(ValueError, match="no connections for C1"):
        _render(
            tmp_path,
            extra_devices="""  - type: electrolytic
    name: C1
    breadboard: {role: capacitor}""",
        )


CUSTOM_MOTOR = """  - name: Pump
    breadboard: {role: motor}
    pins:
      - {name: A, role: GPIO}
      - {name: B, role: GPIO}"""


def test_custom_device_can_be_a_motor(tmp_path):
    diagram, text = _render(
        tmp_path,
        extra_devices=CUSTOM_MOTOR,
        extra_connections=(
            "  - {from: {device: D1, device_pin: A1}, to: {device: Pump, device_pin: A}}"
        ),
    )
    assert next(d for d in diagram.devices if d.name == "Pump").placement.role == "motor"
    assert "Pump" in text


def test_custom_device_without_a_role_is_rejected(tmp_path):
    no_role = CUSTOM_MOTOR.replace("    breadboard: {role: motor}\n", "")
    with pytest.raises(ValueError, match="cannot draw Pump \\(custom device\\)"):
        _render(
            tmp_path,
            extra_devices=no_role,
            extra_connections=(
                "  - {from: {device: D1, device_pin: A1}, to: {device: Pump, device_pin: A}}"
            ),
        )


FULL_BUILD = """
title: "Full build"
board: raspberry_pi_5
layout: breadboard
show_legend: true
devices:
  - {type: breadboard_rail, name: Rails}
  - {type: tmc2209, name: D1}
  - {type: nema17, name: M1}
  - {type: psu_24v, name: PSU}
  - {type: electrolytic, name: C1}
connections:
  - {board_pin: 1, device: Rails, device_pin: "+3V3"}
  - {board_pin: 6, device: Rails, device_pin: GND}
  - {board_pin: 36, device: D1, device_pin: STEP}
  - {board_pin: 9, device: D1, device_pin: IOGND}
  - {from: {device: Rails, device_pin: "+3V3"}, to: {device: D1, device_pin: MS1}}
  - {from: {device: Rails, device_pin: "+3V3"}, to: {device: D1, device_pin: VDD}}
  - {from: {device: Rails, device_pin: "+24V"}, to: {device: D1, device_pin: VM}}
  - {from: {device: Rails, device_pin: MGND}, to: {device: D1, device_pin: VMGND}}
  - {from: {device: D1, device_pin: A1}, to: {device: M1, device_pin: A1}}
  - {from: {device: D1, device_pin: A2}, to: {device: M1, device_pin: A2}}
  - {from: {device: PSU, device_pin: "+V"}, to: {device: Rails, device_pin: "+24V"}}
  - {from: {device: PSU, device_pin: "-V"}, to: {device: Rails, device_pin: MGND}}
  - {from: {device: C1, device_pin: "+"}, to: {device: Rails, device_pin: "+24V"}}
  - {from: {device: C1, device_pin: "-"}, to: {device: Rails, device_pin: MGND}}
"""


def test_full_build_renders_motor_supply_and_ground_tie(tmp_path):
    _diagram, text = _render_yaml(tmp_path, FULL_BUILD)
    assert "M1" in text
    assert "PSU" in text
    assert ">-V GND</text>" in text
    assert ">+V 24V</text>" in text
    assert "stripe (-) on MGND" in text


def test_canvas_is_tall_enough_for_the_board(tmp_path):
    _diagram, text = _render_yaml(tmp_path, FULL_BUILD)
    height = float(ET.fromstring(text).attrib["height"])
    assert height > PI_ORIGIN[1] + 307.46 * PI_SCALE


def test_legend_only_with_show_legend(tmp_path):
    _diagram, with_legend = _render_yaml(tmp_path, FULL_BUILD)
    _diagram, without = _render_yaml(tmp_path, FULL_BUILD.replace("show_legend: true\n", ""))
    assert "Device Specifications" in with_legend
    assert "Device Specifications" not in without


def test_dark_theme_changes_the_background(tmp_path):
    _diagram, light = _render(tmp_path)
    dark_yaml = ONE_DRIVER.replace("layout: breadboard", "layout: breadboard\ntheme: dark")
    _diagram, dark = _render_yaml(
        tmp_path, dark_yaml.replace("{extra_devices}", "").replace("{extra_connections}", "")
    )
    assert 'fill="#1E1E1E"' in dark
    assert 'fill="#1E1E1E"' not in light


def test_wire_without_color_uses_the_pin_role_color(tmp_path):
    yaml = ONE_DRIVER.replace(', color: "#E2B000"', "")
    _diagram, text = _render_yaml(
        tmp_path, yaml.replace("{extra_devices}", "").replace("{extra_connections}", "")
    )
    # Board pin 36 is a plain GPIO
    assert 'stroke="#808080"' in text


def test_unsupported_board_is_rejected(tmp_path):
    yaml = ONE_DRIVER.replace("raspberry_pi_4", "pico").replace("board_pin: 36", "board_pin: 5")
    with pytest.raises(ValueError, match="Raspberry Pi 4 and 5"):
        _render_yaml(
            tmp_path, yaml.replace("{extra_devices}", "").replace("{extra_connections}", "")
        )


def test_unsupported_device_type_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="cannot draw L \\(bh1750\\)"):
        _render(
            tmp_path,
            extra_devices="  - {type: bh1750, name: L}",
            extra_connections="  - {board_pin: 1, device: L, device_pin: VCC}",
        )


def test_overlapping_modules_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="overlap"):
        _render(
            tmp_path,
            extra_devices="  - {type: tmc2209, name: D2, breadboard: {row: 6}}",
            extra_connections="  - {board_pin: 38, device: D2, device_pin: STEP}",
        )


def test_module_row_above_the_lanes_is_rejected(tmp_path):
    yaml = ONE_DRIVER.replace("breadboard: {role: module}", "breadboard: {row: 0}")
    with pytest.raises(ValueError, match="at least"):
        _render_yaml(
            tmp_path, yaml.replace("{extra_devices}", "").replace("{extra_connections}", "")
        )


def test_capacitor_needs_both_legs(tmp_path):
    with pytest.raises(ValueError, match="needs both legs"):
        _render(
            tmp_path,
            extra_devices="  - {type: electrolytic, name: C1}",
            extra_connections=(
                '  - {from: {device: C1, device_pin: "+"}, to: {device: Rails, device_pin: "+24V"}}'
            ),
        )


def test_board_pin_cannot_feed_a_motor(tmp_path):
    with pytest.raises(ValueError, match="cannot wire board pin"):
        _render(
            tmp_path,
            extra_devices="  - {type: nema17, name: M1}",
            extra_connections="  - {board_pin: 11, device: M1, device_pin: A1}",
        )


def test_en_hops_up_the_board_edge_to_the_top_pin(tmp_path):
    """EN leaves the header after STEP and DIR but is the top pin, so it lands
    below the ribbon and climbs the left edge once instead of crossing them."""
    diagram, text = _render(
        tmp_path,
        extra_connections="""  - {board_pin: 38, device: D1, device_pin: DIR, color: "#1F9D55"}
  - {board_pin: 40, device: D1, device_pin: EN, color: "#7C3AED"}
  - from: {device: Rails, device_pin: MGND}
    to: {device: D1, device_pin: VMGND}
    color: "#1A1A1A"
  - from: {device: Rails, device_pin: MGND}
    to: {device: D1, device_pin: IOGND}
    color: "#1A1A1A"
  - from: {device: Rails, device_pin: "+3V3"}
    to: {device: D1, device_pin: VDD}
    color: "#F08C00\"""",
    )
    assert ">PDN<" in text
    assert "PDN_UART" not in text
    assert ">VDD<" in text
    assert ">A2<" in text and ">A1<" in text and ">B1<" in text and ">B2<" in text
    renderer = BreadboardRenderer()
    renderer.render(diagram, tmp_path / "again.svg")
    y_en = renderer.geo.y(renderer.module_row["D1"])
    y_dir = renderer.geo.y(renderer.module_row["D1"] + 7)
    # The hop turns the corner at the board edge, on the EN row, below DIR.
    assert f"Q {renderer.x_hop:.1f} {y_en:.1f}" in text
    assert f"Q {renderer.x_hop:.1f} {y_dir + 0.9 * renderer.geo.pitch:.1f}" in text


def test_white_wire_gets_the_schematic_dark_halo(tmp_path):
    _diagram, text = _render(
        tmp_path,
        extra_connections="""  - {board_pin: 38, device: D1, device_pin: DIR, color: "#FFFFFF"}""",
    )
    assert 'stroke="#2C2C2C"' in text


def test_logic_gnd_must_use_the_right_hand_rail(tmp_path):
    with pytest.raises(ValueError, match="right-hand ground rail"):
        _render(
            tmp_path,
            extra_connections="""  - from: {device: Rails, device_pin: GND}
    to: {device: D1, device_pin: IOGND}
    color: "#1A1A1A\"""",
        )
