#!/usr/bin/env python3
"""Regenerate the ESP32-S3-DevKitC-1 board artwork SVG for PinViz.

Unlike the other board assets (Fritzing-derived), the ESP32-S3-DevKitC-1 board
image is generated from this script so the artwork stays reproducible and the pin
pad coordinates provably match the board config.

Output: ``src/pinviz/assets/esp32_s3_devkitc1_mod.svg``

The layout constants below MUST stay in sync with
``src/pinviz/board_configs/esp32_s3_devkitc1.json``:
    left_col_x=12, right_col_x=108, start_y=42, row_spacing=9.2, width=120, height=262
Pin bubbles (PIN_RADIUS=4.5 in viewBox units) are drawn by PinViz on top of the
gold pads; silkscreen GPIO labels sit inboard, clear of the bubbles.

Usage:
    python scripts/gen_esp32_s3_devkitc1_svg.py
"""

# ruff: noqa: E501  (SVG element strings are intentionally kept on one line)

from pathlib import Path

W, H = 120.0, 262.0
LEFT_X, RIGHT_X = 12.0, 108.0
START_Y, ROW = 42.0, 9.2
N = 22  # pins per side
TOP = 8.0  # canvas headroom above the board edge so the USB-C can overhang it

# Silkscreen text per row (top -> bottom). Left = J1 (odd pins), Right = J3 (even).
LEFT = ["3V3", "3V3", "RST", "IO4", "IO5", "IO6", "IO7", "IO15", "IO16", "IO17",
        "IO18", "IO8", "IO3", "IO46", "IO9", "IO10", "IO11", "IO12", "IO13",
        "IO14", "5V", "GND"]
RIGHT = ["GND", "TX", "RX", "IO1", "IO2", "IO42", "IO41", "IO40", "IO39", "IO38",
         "IO37", "IO36", "IO35", "IO0", "IO45", "IO48", "IO47", "IO21", "IO20",
         "IO19", "GND", "GND"]


def build() -> str:
    s = ['<?xml version="1.0" encoding="UTF-8"?>']
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-TOP} {W} {H + TOP}" '
             f'width="{W}" height="{H + TOP}">')
    # --- PCB ---
    s.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" ry="7" '
             f'fill="#1b1b20" stroke="#3a3a42" stroke-width="1.2"/>')
    s.append(f'<rect x="5" y="5" width="{W - 10}" height="{H - 10}" rx="5" ry="5" '
             f'fill="none" stroke="#2c2c34" stroke-width="0.5"/>')
    # --- mounting holes (4 corners); bottom holes sit clear below the last pin row ---
    hole_top, hole_bot = 9.0, H - 11.0
    for hx, hy in [(9, hole_top), (W - 9, hole_top), (9, hole_bot), (W - 9, hole_bot)]:
        s.append(f'<circle cx="{hx}" cy="{hy}" r="3.6" fill="#0d0d10" stroke="#9a9aa0" stroke-width="1"/>')
        s.append(f'<circle cx="{hx}" cy="{hy}" r="2.0" fill="#050506"/>')
    # --- USB-C receptacle, top-down (orthographic) view: only the metal shell is
    #     seen from above; the plug opening faces off the top edge (overhangs y<0). ---
    ux = 60.0
    s.append(f'<rect x="{ux - 13}" y="-6.5" width="26" height="17.5" rx="2.6" '
             f'fill="#d3d6dc" stroke="#7d818a" stroke-width="0.9"/>')
    s.append(f'<rect x="{ux - 11.5}" y="-4.9" width="23" height="14.3" rx="1.6" '
             f'fill="none" stroke="#b9bdc4" stroke-width="0.5"/>')
    for lx in (ux - 11.5, ux + 8.5):
        s.append(f'<rect x="{lx}" y="11" width="3" height="2.4" rx="0.4" fill="#b7bac0"/>')
    # --- BOOT / RST buttons ---
    for bx, lbl in [(18, "BOOT"), (90, "RST")]:
        s.append(f'<rect x="{bx}" y="17" width="12" height="9" rx="1.2" fill="#2b2b33" stroke="#565660" stroke-width="0.5"/>')
        s.append(f'<rect x="{bx + 3.5}" y="19" width="5" height="5" rx="0.8" fill="#9a9aa4"/>')
        s.append(f'<text x="{bx + 6}" y="31.5" font-family="Arial, sans-serif" font-size="3" '
                 f'fill="#8f8f98" text-anchor="middle">{lbl}</text>')
    # --- RGB LED (offset from the USB so it is not mistaken for it) ---
    s.append('<rect x="43" y="18.5" width="5" height="5" rx="0.6" fill="#f2f2f5" stroke="#8a8a90" stroke-width="0.4"/>')
    s.append('<rect x="44.2" y="19.7" width="2.6" height="2.6" rx="0.4" fill="#9fd0ff"/>')
    s.append('<text x="45.5" y="28.5" font-family="Arial, sans-serif" font-size="2.6" '
             'fill="#7f7f88" text-anchor="middle">RGB</text>')
    # --- ESP32-S3-WROOM module (shield can) ---
    mx, my, mw, mh = 34.0, 52.0, 52.0, 104.0
    s.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="2.5" '
             f'fill="#bfc3c9" stroke="#7a7e86" stroke-width="1"/>')
    s.append(f'<rect x="{mx + 1.6}" y="{my + 1.6}" width="{mw - 3.2}" height="{mh - 3.2}" rx="1.8" '
             f'fill="none" stroke="#9aa0a8" stroke-width="0.5"/>')
    s.append(f'<rect x="{mx + 6}" y="{my + 4}" width="{mw - 12}" height="15" rx="1" fill="#d7dbe0" stroke="#a7adb5" stroke-width="0.5"/>')
    for i in range(6):
        ax = mx + 9 + i * 6
        s.append(f'<path d="M{ax},{my + 16} l3,-9 l3,9" fill="none" stroke="#9aa0a8" stroke-width="0.6"/>')
    s.append(f'<text x="{mx + mw / 2}" y="{my + 42}" font-family="Arial, sans-serif" font-size="6.4" '
             f'font-weight="bold" fill="#3c3f45" text-anchor="middle">ESP32-S3</text>')
    s.append(f'<text x="{mx + mw / 2}" y="{my + 52}" font-family="Arial, sans-serif" font-size="4.4" '
             f'fill="#4c4f55" text-anchor="middle">WROOM-1</text>')
    s.append(f'<text x="{mx + mw / 2}" y="{my + 90}" font-family="Arial, sans-serif" font-size="3.2" '
             f'fill="#6a6d75" text-anchor="middle">FCC ID  2AC7Z</text>')
    # --- header strips (black plastic) behind pads ---
    strip_y = START_Y - 5
    strip_h = (N - 1) * ROW + 10
    for cx in (LEFT_X, RIGHT_X):
        s.append(f'<rect x="{cx - 5}" y="{strip_y}" width="10" height="{strip_h}" rx="1.5" '
                 f'fill="#0b0b0d" stroke="#33333a" stroke-width="0.5"/>')
    # --- pads + silkscreen labels ---
    def label(x, y, txt, anchor, dx):
        s.append(f'<text x="{x + dx}" y="{y + 1.4}" font-family="Consolas, Menlo, monospace" '
                 f'font-size="4" fill="#e9e9ef" text-anchor="{anchor}">{txt}</text>')

    for i in range(N):
        y = START_Y + i * ROW
        s.append(f'<circle cx="{LEFT_X}" cy="{y}" r="4.4" fill="#d8b24a" stroke="#8a6f22" stroke-width="0.5"/>')
        s.append(f'<circle cx="{RIGHT_X}" cy="{y}" r="4.4" fill="#d8b24a" stroke="#8a6f22" stroke-width="0.5"/>')
        label(LEFT_X, y, LEFT[i], "start", 6.5)   # inboard, right of left pad
        label(RIGHT_X, y, RIGHT[i], "end", -6.5)  # inboard, left of right pad
    s.append("</svg>")
    return "\n".join(s) + "\n"


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "src" / "pinviz" / "assets" / "esp32_s3_devkitc1_mod.svg"
    out.write_text(build())
    print(f"wrote {out}")
    print(f"config -> left_col_x={LEFT_X} right_col_x={RIGHT_X} "
          f"start_y={START_Y} row_spacing={ROW} width={W} height={H}")


if __name__ == "__main__":
    main()
