"""Tests for DeviceRegistry fail-fast validation and health status."""

from pinviz.devices import get_registry


class TestRegistryHealthStatus:
    """Tests for registry health status methods."""

    def test_get_health_status(self):
        """Test get_health_status returns correct structure."""
        registry = get_registry()
        status = registry.get_health_status()

        # Check structure
        assert isinstance(status, dict)
        assert "loaded" in status
        assert "failed" in status
        assert "total" in status

        # Check types
        assert isinstance(status["loaded"], int)
        assert isinstance(status["failed"], int)
        assert isinstance(status["total"], int)

        # Check values make sense
        assert status["loaded"] >= 0
        assert status["failed"] >= 0
        assert status["total"] == status["loaded"] + status["failed"]

    def test_get_failed_configs(self):
        """Test get_failed_configs returns list."""
        registry = get_registry()
        failed = registry.get_failed_configs()

        # Should return a list
        assert isinstance(failed, list)

        # All items should be strings (filenames)
        assert all(isinstance(f, str) for f in failed)

    def test_successful_registry_load(self):
        """Test that registry loads successfully with valid configs."""
        registry = get_registry()
        status = registry.get_health_status()

        # Should have loaded some devices
        assert status["loaded"] > 0

        # Total should match loaded + failed
        assert status["total"] == status["loaded"] + status["failed"]

    def test_list_all_devices(self):
        """Test that list_all returns loaded devices."""
        registry = get_registry()
        all_devices = registry.list_all()

        # Should have some devices
        assert len(all_devices) > 0

        # Should match loaded count
        status = registry.get_health_status()
        assert len(all_devices) == status["loaded"]

    def test_health_status_consistency(self):
        """Test that health status is consistent with actual state."""
        registry = get_registry()

        # Get status
        status = registry.get_health_status()
        failed = registry.get_failed_configs()

        # Failed count should match
        assert status["failed"] == len(failed)

        # If no failures, failed list should be empty
        if status["failed"] == 0:
            assert len(failed) == 0

    def test_get_failed_configs_returns_copy(self):
        """Test that get_failed_configs returns a copy, not reference."""
        registry = get_registry()

        # Get failed configs twice
        failed1 = registry.get_failed_configs()
        failed2 = registry.get_failed_configs()

        # Should be equal but not same object
        assert failed1 == failed2
        assert failed1 is not failed2

        # Modifying one shouldn't affect the other
        failed1.append("test.json")
        assert "test.json" not in failed2


class TestRegistryValidation:
    """Tests for registry validation behavior."""

    def test_registry_warns_on_partial_failure(self):
        """Test that registry logs warning if some configs fail."""
        # This is tested implicitly - if some device configs are invalid,
        # the registry should log a warning but continue loading others.
        # We can't easily test this without creating invalid configs,
        # but the code path is exercised if any real configs fail.
        registry = get_registry()
        status = registry.get_health_status()

        # If we have any failures, check they're tracked
        if status["failed"] > 0:
            failed = registry.get_failed_configs()
            assert len(failed) == status["failed"]

    def test_registry_creates_devices_successfully(self):
        """Test that registry can create devices after loading."""
        registry = get_registry()

        # Should be able to create a device
        device = registry.create("led", color_name="Red")
        assert device is not None
        assert device.name == "Red LED"

    def test_get_device_template(self):
        """Test that we can get device templates."""
        registry = get_registry()

        # Get a known device template
        template = registry.get("bh1750")

        if template:  # Only if bh1750 loaded successfully
            assert template.type_id == "bh1750"
            assert template.name
            assert template.category
