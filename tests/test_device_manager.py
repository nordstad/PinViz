"""Unit tests for the PinViz MCP device manager."""

import json
from pathlib import Path

import pytest

from pinviz_mcp.device_manager import DeviceManager, DevicePin


class TestDeviceManager:
    """Test suite for DeviceManager class."""

    @pytest.fixture
    def device_manager(self):
        """Create a DeviceManager instance for testing."""
        return DeviceManager()

    def test_load_database(self, device_manager):
        """Test that the database loads successfully."""
        assert len(device_manager.devices) > 0
        assert len(device_manager.devices) >= 25  # Should have at least 25 devices

    def test_load_schema(self, device_manager):
        """Test that the schema loads successfully."""
        assert device_manager.schema is not None
        assert "$schema" in device_manager.schema

    def test_get_device_by_id_exact(self, device_manager):
        """Test getting a device by exact ID match."""
        device = device_manager.get_device_by_id("bh1750")
        assert device is not None
        assert device.id == "bh1750"
        assert device.name == "BH1750 Light Sensor"

    def test_get_device_by_id_nonexistent(self, device_manager):
        """Test getting a non-existent device by ID."""
        device = device_manager.get_device_by_id("nonexistent-device")
        assert device is None

    def test_get_device_by_name_exact(self, device_manager):
        """Test getting a device by exact name match."""
        device = device_manager.get_device_by_name("BH1750 Light Sensor")
        assert device is not None
        assert device.id == "bh1750"

    def test_get_device_by_name_case_insensitive(self, device_manager):
        """Test case-insensitive name matching."""
        device = device_manager.get_device_by_name("bh1750 light sensor")
        assert device is not None
        assert device.id == "bh1750"

    def test_get_device_by_name_fuzzy(self, device_manager):
        """Test fuzzy name matching."""
        # "bh1750" should fuzzy match to "BH1750 Light Sensor"
        device = device_manager.get_device_by_name("bh1750", fuzzy=True)
        assert device is not None
        assert device.id == "bh1750"

        # "oled" should fuzzy match to an OLED display
        device = device_manager.get_device_by_name("oled", fuzzy=True)
        assert device is not None
        assert "oled" in device.id.lower()

    def test_get_device_by_name_no_fuzzy(self, device_manager):
        """Test name matching without fuzzy search."""
        # "light sensor" is a partial match that should only work with fuzzy
        device = device_manager.get_device_by_name("light sensor", fuzzy=False)
        assert device is None  # Should not find partial match without fuzzy

    def test_search_devices_by_category(self, device_manager):
        """Test searching devices by category."""
        displays = device_manager.search_devices(category="display")
        assert len(displays) >= 5  # Should have at least 5 displays
        assert all(d.category == "display" for d in displays)

        sensors = device_manager.search_devices(category="sensor")
        assert len(sensors) >= 10  # Should have at least 10 sensors
        assert all(d.category == "sensor" for d in sensors)

    def test_search_devices_by_protocol(self, device_manager):
        """Test searching devices by protocol."""
        i2c_devices = device_manager.search_devices(protocol="I2C")
        assert len(i2c_devices) > 0
        assert all("I2C" in d.protocols for d in i2c_devices)

        spi_devices = device_manager.search_devices(protocol="SPI")
        assert len(spi_devices) > 0
        assert all("SPI" in d.protocols for d in spi_devices)

    def test_search_devices_by_voltage(self, device_manager):
        """Test searching devices by voltage."""
        devices_3v3 = device_manager.search_devices(voltage="3.3V")
        assert len(devices_3v3) > 0
        assert all(d.voltage == "3.3V" for d in devices_3v3)

    def test_search_devices_by_query(self, device_manager):
        """Test searching devices by text query."""
        # Search in name
        results = device_manager.search_devices(query="BH1750")
        assert len(results) > 0
        assert any("BH1750" in d.name for d in results)

        # Search in description
        results = device_manager.search_devices(query="temperature")
        assert len(results) > 0
        assert any("temperature" in d.description.lower() for d in results)

    def test_search_devices_by_tags(self, device_manager):
        """Test searching devices by tags."""
        results = device_manager.search_devices(tags=["i2c"])
        assert len(results) > 0
        assert all(d.tags and any("i2c" in tag.lower() for tag in d.tags) for d in results)

    def test_search_devices_multiple_filters(self, device_manager):
        """Test searching with multiple filters combined."""
        results = device_manager.search_devices(
            category="sensor",
            protocol="I2C",
            query="light",
        )
        assert len(results) > 0
        assert all(d.category == "sensor" for d in results)
        assert all("I2C" in d.protocols for d in results)

    def test_list_categories(self, device_manager):
        """Test getting list of all categories."""
        categories = device_manager.list_categories()
        assert len(categories) > 0
        assert "display" in categories
        assert "sensor" in categories
        assert "hat" in categories
        assert "component" in categories or "actuator" in categories

    def test_list_protocols(self, device_manager):
        """Test getting list of all protocols."""
        protocols = device_manager.list_protocols()
        assert len(protocols) > 0
        assert "I2C" in protocols
        assert "SPI" in protocols
        assert "GPIO" in protocols

    def test_get_devices_by_category(self, device_manager):
        """Test getting all devices in a category."""
        displays = device_manager.get_devices_by_category("display")
        assert len(displays) >= 5
        assert all(d.category == "display" for d in displays)

    def test_get_summary(self, device_manager):
        """Test getting database summary."""
        summary = device_manager.get_summary()
        assert "total_devices" in summary
        assert summary["total_devices"] >= 25
        assert "categories" in summary
        assert "protocols" in summary
        assert isinstance(summary["categories"], dict)
        assert isinstance(summary["protocols"], list)

    def test_device_has_required_fields(self, device_manager):
        """Test that devices have all required fields."""
        device = device_manager.get_device_by_id("bh1750")
        assert device is not None
        assert device.id
        assert device.name
        assert device.category
        assert device.description
        assert len(device.pins) > 0
        assert len(device.protocols) > 0
        assert device.voltage

    def test_device_pins_structure(self, device_manager):
        """Test that device pins have correct structure."""
        device = device_manager.get_device_by_id("bh1750")
        assert device is not None

        for pin in device.pins:
            assert isinstance(pin, DevicePin)
            assert pin.name
            assert pin.role
            assert isinstance(pin.position, int)
            assert pin.position >= 0

    def test_device_to_dict(self, device_manager):
        """Test converting device to dictionary."""
        device = device_manager.get_device_by_id("bh1750")
        assert device is not None

        device_dict = device.to_dict()
        assert isinstance(device_dict, dict)
        assert device_dict["id"] == "bh1750"
        assert "pins" in device_dict
        assert isinstance(device_dict["pins"], list)

    def test_i2c_device_has_address(self, device_manager):
        """Test that I2C devices have I2C address."""
        i2c_devices = device_manager.search_devices(protocol="I2C")
        for device in i2c_devices:
            # Should have either i2c_address or i2c_addresses
            assert device.i2c_address or device.i2c_addresses

    def test_validate_device_valid(self, device_manager):
        """Test validating a valid device entry."""
        valid_device = {
            "id": "test-device",
            "name": "Test Device",
            "category": "sensor",
            "description": "A test device",
            "pins": [
                {"name": "VCC", "role": "3V3", "position": 0},
                {"name": "GND", "role": "GND", "position": 1},
            ],
            "protocols": ["GPIO"],
            "voltage": "3.3V",
        }
        assert device_manager.validate_device(valid_device) is True

    def test_validate_device_invalid(self, device_manager):
        """Test validating an invalid device entry."""
        invalid_device = {
            "id": "test-device",
            "name": "Test Device",
            # Missing required fields
        }
        assert device_manager.validate_device(invalid_device) is False

    def test_database_file_exists(self):
        """Test that the database file exists."""
        database_path = (
            Path(__file__).parent.parent / "src" / "pinviz_mcp" / "devices" / "database.json"
        )
        assert database_path.exists()

    def test_schema_file_exists(self):
        """Test that the schema file exists."""
        schema_path = (
            Path(__file__).parent.parent / "src" / "pinviz_mcp" / "devices" / "schema.json"
        )
        assert schema_path.exists()

    def test_database_is_valid_json(self):
        """Test that the database is valid JSON."""
        database_path = (
            Path(__file__).parent.parent / "src" / "pinviz_mcp" / "devices" / "database.json"
        )
        with open(database_path) as f:
            data = json.load(f)
        assert "devices" in data
        assert isinstance(data["devices"], list)

    def test_all_devices_unique_ids(self, device_manager):
        """Test that all device IDs are unique."""
        ids = [device.id for device in device_manager.devices]
        assert len(ids) == len(set(ids))

    def test_device_categories_are_valid(self, device_manager):
        """Test that all device categories are valid enum values."""
        valid_categories = {"display", "sensor", "hat", "component", "actuator", "breakout"}
        for device in device_manager.devices:
            assert device.category in valid_categories

    def test_device_protocols_are_valid(self, device_manager):
        """Test that all device protocols are valid enum values."""
        valid_protocols = {"I2C", "SPI", "UART", "GPIO", "1-Wire", "PWM"}
        for device in device_manager.devices:
            assert all(protocol in valid_protocols for protocol in device.protocols)

    def test_device_voltages_are_valid(self, device_manager):
        """Test that all device voltages are valid enum values."""
        valid_voltages = {"3.3V", "5V", "3.3V-5V"}
        for device in device_manager.devices:
            assert device.voltage in valid_voltages
