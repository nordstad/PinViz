"""Device database management for PinViz MCP server.

This module provides functionality to load, query, and manage the device database.
"""

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import jsonschema


@dataclass
class DevicePin:
    """Represents a pin on a device."""

    name: str
    role: str
    position: int
    description: str | None = None
    optional: bool = False


@dataclass
class Device:
    """Represents a device in the database."""

    id: str
    name: str
    category: str
    description: str
    pins: list[DevicePin]
    protocols: list[str]
    voltage: str
    manufacturer: str | None = None
    datasheet_url: str | None = None
    i2c_address: str | None = None
    i2c_addresses: list[str] | None = None
    current_draw: str | None = None
    dimensions: dict | None = None
    tags: list[str] | None = None
    notes: str | None = None
    requires_pullup: bool = False

    def to_dict(self) -> dict:
        """Convert device to dictionary representation."""
        result = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "pins": [
                {
                    "name": pin.name,
                    "role": pin.role,
                    "position": pin.position,
                    "description": pin.description,
                    "optional": pin.optional,
                }
                for pin in self.pins
            ],
            "protocols": self.protocols,
            "voltage": self.voltage,
        }

        # Add optional fields
        if self.manufacturer:
            result["manufacturer"] = self.manufacturer
        if self.datasheet_url:
            result["datasheet_url"] = self.datasheet_url
        if self.i2c_address:
            result["i2c_address"] = self.i2c_address
        if self.i2c_addresses:
            result["i2c_addresses"] = self.i2c_addresses
        if self.current_draw:
            result["current_draw"] = self.current_draw
        if self.dimensions:
            result["dimensions"] = self.dimensions
        if self.tags:
            result["tags"] = self.tags
        if self.notes:
            result["notes"] = self.notes
        if self.requires_pullup:
            result["requires_pullup"] = self.requires_pullup

        return result


class DeviceManager:
    """Manages the device database with query and validation capabilities."""

    def __init__(
        self,
        database_path: Path | None = None,
        user_database_path: Path | None = None,
        schema_path: Path | None = None,
    ):
        """Initialize the device manager.

        Args:
            database_path: Path to the main device database JSON file
            user_database_path: Path to the user devices JSON file
            schema_path: Path to the JSON schema file
        """
        self.devices_dir = Path(__file__).parent / "devices"

        if database_path is None:
            database_path = self.devices_dir / "database.json"
        if user_database_path is None:
            user_database_path = self.devices_dir / "user_devices.json"
        if schema_path is None:
            schema_path = self.devices_dir / "schema.json"

        self.database_path = database_path
        self.user_database_path = user_database_path
        self.schema_path = schema_path

        self.schema = self._load_schema()
        # Load both main and user devices
        self.devices = self._load_database(self.database_path)
        self.user_devices = self._load_database(self.user_database_path)
        # Combine both lists (user devices override main devices if ID conflicts)
        self._merge_devices()
        self._device_index = {device.id: device for device in self.devices}

    def _load_schema(self) -> dict:
        """Load the JSON schema for validation."""
        with open(self.schema_path) as f:
            return json.load(f)

    def _merge_devices(self) -> None:
        """Merge main and user devices, with user devices taking precedence."""
        # Create a dict of device IDs to devices from main database
        device_dict = {device.id: device for device in self.devices}

        # Add/override with user devices
        for user_device in self.user_devices:
            device_dict[user_device.id] = user_device

        # Update the devices list
        self.devices = list(device_dict.values())

    def _load_database(self, database_path: Path) -> list[Device]:
        """Load and parse a device database file.

        Args:
            database_path: Path to the database JSON file

        Returns:
            List of Device objects
        """
        # Skip if file doesn't exist (for user_devices.json)
        if not database_path.exists():
            return []

        with open(database_path) as f:
            data = json.load(f)

        # Validate against schema
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Device database validation failed: {e.message}") from e

        # Parse devices
        devices = []
        for device_data in data["devices"]:
            pins = [
                DevicePin(
                    name=pin["name"],
                    role=pin["role"],
                    position=pin["position"],
                    description=pin.get("description"),
                    optional=pin.get("optional", False),
                )
                for pin in device_data["pins"]
            ]

            device = Device(
                id=device_data["id"],
                name=device_data["name"],
                category=device_data["category"],
                description=device_data["description"],
                pins=pins,
                protocols=device_data["protocols"],
                voltage=device_data["voltage"],
                manufacturer=device_data.get("manufacturer"),
                datasheet_url=device_data.get("datasheet_url"),
                i2c_address=device_data.get("i2c_address"),
                i2c_addresses=device_data.get("i2c_addresses"),
                current_draw=device_data.get("current_draw"),
                dimensions=device_data.get("dimensions"),
                tags=device_data.get("tags"),
                notes=device_data.get("notes"),
                requires_pullup=device_data.get("requires_pullup", False),
            )
            devices.append(device)

        return devices

    def get_device_by_id(self, device_id: str) -> Device | None:
        """Get a device by its unique ID.

        Args:
            device_id: The device ID to look up

        Returns:
            The device if found, None otherwise
        """
        return self._device_index.get(device_id)

    def get_device_by_name(self, name: str, fuzzy: bool = True) -> Device | None:
        """Get a device by name with optional fuzzy matching.

        Args:
            name: The device name to search for
            fuzzy: Whether to use fuzzy matching (default: True)

        Returns:
            The best matching device if found, None otherwise
        """
        name_lower = name.lower()

        # Try exact match first
        for device in self.devices:
            if device.name.lower() == name_lower or device.id.lower() == name_lower:
                return device

        # Try fuzzy matching if enabled
        if fuzzy:
            best_match = None
            best_score = 0.0

            for device in self.devices:
                # Check name similarity
                name_score = SequenceMatcher(None, name_lower, device.name.lower()).ratio()
                id_score = SequenceMatcher(None, name_lower, device.id.lower()).ratio()
                score = max(name_score, id_score)

                # Check tags if available
                if device.tags:
                    for tag in device.tags:
                        tag_score = SequenceMatcher(None, name_lower, tag.lower()).ratio()
                        score = max(score, tag_score)

                if score > best_score and score > 0.6:  # Threshold for fuzzy matching
                    best_score = score
                    best_match = device

            return best_match

        return None

    def search_devices(
        self,
        query: str | None = None,
        category: str | None = None,
        protocol: str | None = None,
        voltage: str | None = None,
        tags: list[str] | None = None,
    ) -> list[Device]:
        """Search devices with multiple criteria.

        Args:
            query: Text query to search in name, description, and tags
            category: Filter by device category
            protocol: Filter by supported protocol
            voltage: Filter by voltage requirement
            tags: Filter by tags (all must match)

        Returns:
            List of matching devices
        """
        results = self.devices.copy()

        # Filter by category
        if category:
            results = [d for d in results if d.category == category]

        # Filter by protocol
        if protocol:
            results = [d for d in results if protocol.upper() in d.protocols]

        # Filter by voltage
        if voltage:
            results = [d for d in results if d.voltage == voltage]

        # Filter by tags
        if tags:
            results = [
                d
                for d in results
                if d.tags and all(tag.lower() in [t.lower() for t in d.tags] for tag in tags)
            ]

        # Text query search
        if query:
            query_lower = query.lower()
            filtered_results = []

            for device in results:
                # Search in name
                if query_lower in device.name.lower():
                    filtered_results.append(device)
                    continue

                # Search in description
                if query_lower in device.description.lower():
                    filtered_results.append(device)
                    continue

                # Search in tags
                if device.tags and any(query_lower in tag.lower() for tag in device.tags):
                    filtered_results.append(device)
                    continue

            results = filtered_results

        return results

    def list_categories(self) -> list[str]:
        """Get a list of all unique device categories."""
        return sorted({device.category for device in self.devices})

    def list_protocols(self) -> list[str]:
        """Get a list of all unique protocols."""
        protocols = set()
        for device in self.devices:
            protocols.update(device.protocols)
        return sorted(protocols)

    def get_devices_by_category(self, category: str) -> list[Device]:
        """Get all devices in a specific category.

        Args:
            category: The category to filter by

        Returns:
            List of devices in the specified category
        """
        return [d for d in self.devices if d.category == category]

    def validate_device(self, device_data: dict) -> bool:
        """Validate a device entry against the schema.

        Args:
            device_data: Device data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Wrap in devices array for schema validation
            jsonschema.validate({"devices": [device_data]}, self.schema)
            return True
        except jsonschema.ValidationError:
            return False

    def get_summary(self) -> dict:
        """Get a summary of the device database.

        Returns:
            Dictionary with database statistics
        """
        return {
            "total_devices": len(self.devices),
            "user_devices": len(self.user_devices),
            "main_devices": len(self.devices) - len(self.user_devices),
            "categories": {
                category: len(self.get_devices_by_category(category))
                for category in self.list_categories()
            },
            "protocols": self.list_protocols(),
        }

    def add_user_device(self, device: Device) -> None:
        """Add a device to the user devices database.

        Args:
            device: Device to add to user database
        """
        # Add to user devices list
        self.user_devices.append(device)

        # Update merged devices list and index
        self._device_index[device.id] = device
        self.devices = list(self._device_index.values())

        # Save to file
        self._save_user_devices()

    def remove_user_device(self, device_id: str) -> bool:
        """Remove a device from the user devices database.

        Args:
            device_id: ID of the device to remove

        Returns:
            True if device was removed, False if not found
        """
        # Find and remove from user devices list
        original_len = len(self.user_devices)
        self.user_devices = [d for d in self.user_devices if d.id != device_id]

        if len(self.user_devices) == original_len:
            return False  # Device not found

        # Rebuild merged devices
        self.devices = self._load_database(self.database_path)
        self._merge_devices()
        self._device_index = {device.id: device for device in self.devices}

        # Save to file
        self._save_user_devices()
        return True

    def _save_user_devices(self) -> None:
        """Save user devices to the user_devices.json file."""
        data = {
            "$schema": "./schema.json",
            "devices": [device.to_dict() for device in self.user_devices],
        }

        with open(self.user_database_path, "w") as f:
            json.dump(data, f, indent=2)

    def is_user_device(self, device_id: str) -> bool:
        """Check if a device is from the user database.

        Args:
            device_id: Device ID to check

        Returns:
            True if device is in user database, False otherwise
        """
        return any(d.id == device_id for d in self.user_devices)
