#!/bin/bash

# Quick test script for Pi Zero MCP functionality
# Run this after restarting Claude Desktop

echo "🧪 Testing Pi Zero MCP Server Integration"
echo "=========================================="
echo ""

# Test 1: CLI functionality (should always work)
echo "✓ Test 1: CLI with explicit board name"
uv run pinviz render test_pi_zero_mcp.yaml -o /tmp/quick_cli_test.svg
if [ $? -eq 0 ]; then
    echo "  ✅ CLI test passed"
else
    echo "  ❌ CLI test failed"
fi
echo ""

# Test 2: Test different aliases in YAML configs
echo "✓ Test 2: Config loader with various aliases"
ALIASES=("pi zero" "raspberry pi zero 2w" "zero 2w" "rpi zero")
for alias in "${ALIASES[@]}"; do
    cat > /tmp/test_alias_temp.yaml << EOF
title: "Test $alias"
board: "$alias"
devices:
  - type: bh1750
connections:
  - board_pin: 1
    device: BH1750
    device_pin: VCC
  - board_pin: 3
    device: BH1750
    device_pin: SDA
  - board_pin: 5
    device: BH1750
    device_pin: SCL
  - board_pin: 9
    device: BH1750
    device_pin: GND
EOF

    uv run pinviz render /tmp/test_alias_temp.yaml -o /tmp/test_"${alias// /_}".svg 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "  ✅ Alias '$alias' works"
    else
        echo "  ❌ Alias '$alias' failed"
    fi
done
echo ""

echo "✓ Test 3: MCP Server Test"
echo "  ⚠️  MCP server tests require Claude Desktop restart"
echo "  After restart, test these prompts:"
echo "    - 'connect BH1750 to my Pi Zero'"
echo "    - 'wire sensor to raspberry pi zero 2w'"
echo "    - 'add LED to zero 2w'"
echo ""

echo "📊 Test Summary"
echo "=============="
echo "CLI tests completed above."
echo "MCP tests require Claude Desktop restart."
echo ""
echo "To test MCP after restart:"
echo "  1. Quit Claude Desktop completely"
echo "  2. Relaunch Claude Desktop"
echo "  3. In chat, try: 'connect BH1750 to my Pi Zero'"
echo ""
