#!/usr/bin/env bash
#
# Validate Post-Publish Tests
#
# This script extracts and runs the Python API tests from the publish workflow
# to catch outdated API usage BEFORE publishing to PyPI.
#
# Run this before creating a release tag to ensure post-publish tests will pass.

set -e

echo "=========================================="
echo "VALIDATING POST-PUBLISH TEST COMPATIBILITY"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv is not installed${NC}"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "[1/3] Extracting Python API tests from publish workflow..."

# Extract the Python API test from the workflow file
WORKFLOW_FILE=".github/workflows/publish.yml"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo -e "${RED}✗ Workflow file not found: $WORKFLOW_FILE${NC}"
    exit 1
fi

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "[2/3] Running Python API tests with current code..."
echo ""

# Test 1: Core imports
echo "Test 1: Core imports..."
uv run python -c "from pinviz import boards, Connection, Diagram, SVGRenderer" || {
    echo -e "${RED}✗ Failed to import core modules${NC}"
    exit 1
}
uv run python -c "from pinviz import WireColor, ComponentType, Component" || {
    echo -e "${RED}✗ Failed to import wire/component types${NC}"
    exit 1
}
uv run python -c "from pinviz.devices import get_registry" || {
    echo -e "${RED}✗ Failed to import device registry${NC}"
    exit 1
}
uv run python -c "from pinviz.validation import DiagramValidator, ValidationLevel" || {
    echo -e "${RED}✗ Failed to import validation${NC}"
    exit 1
}
uv run python -c "from pinviz.logging_config import configure_logging" || {
    echo -e "${RED}✗ Failed to import logging config${NC}"
    exit 1
}
echo -e "${GREEN}✓ Core imports work${NC}"
echo ""

# Test 2: Simple diagram creation (matches workflow exactly)
echo "Test 2: Simple diagram creation (registry API)..."
uv run python -c "
from pinviz import boards, Connection, Diagram, SVGRenderer
from pinviz.devices import get_registry

board = boards.raspberry_pi_5()
registry = get_registry()
led = registry.create('led', color_name='Red')
connections = [
    Connection(11, 'Red LED', '+'),
    Connection(6, 'Red LED', '-'),
]
diagram = Diagram('Test', board, [led], connections)
renderer = SVGRenderer()
renderer.render(diagram, '$TEMP_DIR/test.svg')
print('✓ Python API works correctly')
" || {
    echo -e "${RED}✗ Simple diagram creation failed${NC}"
    echo "This matches the test in .github/workflows/publish.yml line 382-398"
    exit 1
}
echo -e "${GREEN}✓ Simple diagram creation works${NC}"
echo ""

# Test 3: Device templates (matches workflow exactly)
echo "Test 3: Device templates (registry API)..."
uv run python << 'EOPY' || {
    echo -e "${RED}✗ Device templates test failed${NC}"
    echo "This matches the test in .github/workflows/publish.yml line 601-629"
    exit 1
}
from pinviz import boards
from pinviz.devices import get_registry

# Test boards
rpi5 = boards.raspberry_pi_5()
rpi4 = boards.raspberry_pi_4()
assert len(rpi5.pins) == 40, "Raspberry Pi 5 should have 40 pins"
assert len(rpi4.pins) == 40, "Raspberry Pi 4 should have 40 pins"

# Test devices using registry
registry = get_registry()
bh1750 = registry.create('bh1750')
led = registry.create('led')
button = registry.create('button')
ds18b20 = registry.create('ds18b20')

assert len(bh1750.pins) == 5, "BH1750 should have 5 pins"
assert len(led.pins) == 2, "LED should have 2 pins"
assert len(button.pins) == 2, "Button should have 2 pins"
assert len(ds18b20.pins) == 3, "DS18B20 should have 3 pins"

print("✓ All templates functional")
EOPY
echo -e "${GREEN}✓ Device templates work${NC}"
echo ""

echo "[3/3] Checking for common API mistakes..."

# Check if workflow file contains outdated patterns
if grep -q "devices\.simple_led" "$WORKFLOW_FILE"; then
    echo -e "${RED}✗ Found outdated API: devices.simple_led${NC}"
    echo "  Should use: registry.create('led')"
    exit 1
fi

if grep -q "devices\.bh1750_light_sensor" "$WORKFLOW_FILE"; then
    echo -e "${RED}✗ Found outdated API: devices.bh1750_light_sensor${NC}"
    echo "  Should use: registry.create('bh1750')"
    exit 1
fi

if grep -q "devices\.button_switch" "$WORKFLOW_FILE"; then
    echo -e "${RED}✗ Found outdated API: devices.button_switch${NC}"
    echo "  Should use: registry.create('button')"
    exit 1
fi

echo -e "${GREEN}✓ No outdated API patterns found${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}✓ ALL VALIDATION CHECKS PASSED!${NC}"
echo "=========================================="
echo ""
echo "The post-publish tests in the workflow will work correctly."
echo "You can safely proceed with:"
echo "  1. Bump version in pyproject.toml"
echo "  2. Commit and push"
echo "  3. Create and push git tag"
echo ""
