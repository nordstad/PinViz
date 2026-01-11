#!/usr/bin/env python3
"""Verify Pico pin positions are correct."""

from pinviz import boards

board = boards.raspberry_pi_pico()

print("Verifying Raspberry Pi Pico pin positions...")
print("=" * 60)

# Top header - should be reversed (pin 20 on left, pin 1 on right)
print("\nTOP HEADER (should go 20->1 from left to right):")
print(f"Pin 20: x={board.get_pin_by_number(20).position.x:.1f}, y={board.get_pin_by_number(20).position.y:.1f}")
print(f"Pin 19: x={board.get_pin_by_number(19).position.x:.1f}, y={board.get_pin_by_number(19).position.y:.1f}")
print(f"Pin 2:  x={board.get_pin_by_number(2).position.x:.1f}, y={board.get_pin_by_number(2).position.y:.1f}")
print(f"Pin 1:  x={board.get_pin_by_number(1).position.x:.1f}, y={board.get_pin_by_number(1).position.y:.1f}")

# Bottom header - should be normal (pin 21 on left, pin 40 on right)
print("\nBOTTOM HEADER (should go 21->40 from left to right):")
print(f"Pin 21: x={board.get_pin_by_number(21).position.x:.1f}, y={board.get_pin_by_number(21).position.y:.1f}")
print(f"Pin 22: x={board.get_pin_by_number(22).position.x:.1f}, y={board.get_pin_by_number(22).position.y:.1f}")
print(f"Pin 39: x={board.get_pin_by_number(39).position.x:.1f}, y={board.get_pin_by_number(39).position.y:.1f}")
print(f"Pin 40: x={board.get_pin_by_number(40).position.x:.1f}, y={board.get_pin_by_number(40).position.y:.1f}")

# Verification
print("\n" + "=" * 60)
print("VERIFICATION:")

# Top header: Pin 20 should be leftmost (x=30.0), Pin 1 rightmost (x=220.0)
top_20 = board.get_pin_by_number(20).position.x
top_1 = board.get_pin_by_number(1).position.x
if top_20 < top_1:
    print("✅ Top header: Pin 20 is LEFT of Pin 1 (CORRECT - reversed order)")
else:
    print("❌ Top header: Pin 20 is RIGHT of Pin 1 (WRONG - should be reversed)")

# Bottom header: Pin 21 should be leftmost (x=30.0), Pin 40 rightmost (x=220.0)
bot_21 = board.get_pin_by_number(21).position.x
bot_40 = board.get_pin_by_number(40).position.x
if bot_21 < bot_40:
    print("✅ Bottom header: Pin 21 is LEFT of Pin 40 (CORRECT - normal order)")
else:
    print("❌ Bottom header: Pin 21 is RIGHT of Pin 40 (WRONG - should be normal)")

# Check spacing is uniform
print("\nSpacing verification:")
top_spacing = board.get_pin_by_number(19).position.x - board.get_pin_by_number(20).position.x
bot_spacing = board.get_pin_by_number(22).position.x - board.get_pin_by_number(21).position.x
print(f"Top header spacing: {top_spacing:.1f} (should be 10.0)")
print(f"Bottom header spacing: {bot_spacing:.1f} (should be 10.0)")
