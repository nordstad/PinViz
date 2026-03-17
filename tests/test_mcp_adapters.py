"""Tests for MCP model adapters."""

import pytest

from pinviz.mcp.adapters import McpDeviceAdapter
from pinviz.model import PinRole


def test_manual_adapter_normalizes_lowercase_pin_roles():
    """Lowercase MCP role strings should still map to PinRole values."""
    adapter = McpDeviceAdapter()

    device = adapter.adapt({"name": "Lowercase GPIO", "pins": [{"name": "SIG", "role": "gpio"}]})

    assert device.pins[0].role == PinRole.GPIO


def test_manual_adapter_rejects_unknown_pin_roles():
    """Unknown MCP role strings should fail with a clear error."""
    adapter = McpDeviceAdapter()

    with pytest.raises(ValueError, match="Unknown MCP pin role: mystery"):
        adapter.adapt({"name": "Broken Device", "pins": [{"name": "SIG", "role": "mystery"}]})


def test_parse_i2c_address_handles_ints_and_unsupported_types():
    """Address parsing should preserve ints and ignore unsupported values."""
    adapter = McpDeviceAdapter()

    assert adapter._parse_i2c_address(42) == 42
    assert adapter._parse_i2c_address(["0x2A"]) is None
