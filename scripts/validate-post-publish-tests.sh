#!/usr/bin/env bash
#
# Validate Post-Publish Tests
#
# This script runs the shared integration tests (tests/post_publish_integration.py)
# to catch issues BEFORE publishing to PyPI.
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

# Check if shared test file exists
TEST_FILE="tests/post_publish_integration.py"
if [ ! -f "$TEST_FILE" ]; then
    echo -e "${RED}✗ Shared test file not found: $TEST_FILE${NC}"
    exit 1
fi

echo "[1/2] Running shared integration tests..."
echo ""

# Run the shared integration tests
uv run python "$TEST_FILE" || {
    echo -e "${RED}✗ Integration tests failed${NC}"
    exit 1
}

echo ""
echo "[2/2] Checking workflow for outdated API patterns..."

WORKFLOW_FILE=".github/workflows/publish.yml"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo -e "${RED}✗ Workflow file not found: $WORKFLOW_FILE${NC}"
    exit 1
fi

# Check if workflow uses the shared test file
if ! grep -q "tests/post_publish_integration.py" "$WORKFLOW_FILE"; then
    echo -e "${YELLOW}⚠ Warning: Workflow doesn't use shared test file${NC}"
    echo "  The workflow should run: uv run python tests/post_publish_integration.py"
    echo "  This ensures tests stay in sync."
fi

# Check for outdated direct API patterns (these should be rare now)
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
