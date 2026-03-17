"""Adapters from MCP records to core PinViz model objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from ..devices import get_registry
from ..model import Device, DevicePin, PinRole, Point


class McpDeviceAdapter:
    """Adapt MCP device dictionaries into ``Device`` model instances."""

    _CATEGORY_COLORS = {
        "display": "#4A90E2",
        "sensor": "#50E3C2",
        "actuator": "#F5A623",
        "hat": "#BD10E0",
        "breakout": "#7ED321",
        "component": "#F8E71C",
    }

    def __init__(self):
        self._registry = get_registry()

    def adapt_many(self, devices_data: list[dict[str, Any]]) -> list[Device]:
        """Adapt multiple MCP device records."""
        return [self.adapt(device_data) for device_data in devices_data]

    def adapt(self, device_data: Mapping[str, Any]) -> Device:
        """Adapt a single MCP device record."""
        device_id = device_data.get("id")
        device_name = str(device_data["name"])

        if device_id:
            try:
                device = self._registry.create(str(device_id))
            except ValueError:
                device = None
            else:
                if device.name != device_name:
                    device = replace(device, name=device_name)

                return self._apply_metadata_overrides(device, device_data, str(device_id))

        return self._build_manual_device(device_data)

    def get_device_color(self, category: str | None) -> str:
        """Get a fallback device color from its category."""
        return self._CATEGORY_COLORS.get(category or "", "#4A90E2")

    def _build_manual_device(self, device_data: Mapping[str, Any]) -> Device:
        device_id = device_data.get("id")
        device_name = str(device_data["name"])
        pins_data = list(device_data.get("pins", []))

        device_pins = [
            DevicePin(
                name=str(pin_data["name"]),
                role=self._coerce_role(str(pin_data["role"])),
                position=Point(0, index * 10),
            )
            for index, pin_data in enumerate(pins_data)
        ]

        return Device(
            name=device_name,
            pins=device_pins,
            width=120.0,
            height=max(60.0, len(device_pins) * 10 + 20),
            position=Point(0, 0),
            color=self.get_device_color(device_data.get("category")),
            type_id=str(device_id) if device_id is not None else None,
            description=device_data.get("description"),
            url=device_data.get("datasheet_url"),
            category=device_data.get("category"),
            i2c_address=self._parse_i2c_address(device_data.get("i2c_address")),
        )

    def _apply_metadata_overrides(
        self,
        device: Device,
        device_data: Mapping[str, Any],
        type_id: str,
    ) -> Device:
        device.type_id = type_id
        if device_data.get("description"):
            device.description = device_data["description"]
        if device_data.get("datasheet_url"):
            device.url = device_data["datasheet_url"]
        if device_data.get("category"):
            device.category = device_data["category"]

        adapted_i2c_address = self._parse_i2c_address(device_data.get("i2c_address"))
        if adapted_i2c_address is not None:
            device.i2c_address = adapted_i2c_address

        return device

    def _coerce_role(self, role: str) -> PinRole:
        try:
            return PinRole(role)
        except ValueError:
            try:
                return PinRole(role.upper())
            except ValueError as exc:
                raise ValueError(f"Unknown MCP pin role: {role}") from exc

    def _parse_i2c_address(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value, 16 if value.startswith("0x") else 10)
        return None
