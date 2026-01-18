"""Tests for instantiable device registry pattern (issue #126)."""

from pinviz.devices import create_registry, get_registry, reset_default_registry


def test_create_registry_returns_new_instance():
    """Test that create_registry() returns a new independent instance."""
    registry1 = create_registry()
    registry2 = create_registry()
    assert registry1 is not registry2


def test_get_registry_returns_same_instance():
    """Test that get_registry() returns the same cached instance."""
    registry1 = get_registry()
    registry2 = get_registry()
    assert registry1 is registry2


def test_get_registry_and_create_registry_are_independent():
    """Test that default registry and created registries are independent."""
    default_registry = get_registry()
    created_registry = create_registry()
    assert default_registry is not created_registry


def test_reset_default_registry():
    """Test that reset_default_registry() causes new instance on next call."""
    registry1 = get_registry()
    reset_default_registry()
    registry2 = get_registry()
    # After reset, should get a new instance
    assert registry1 is not registry2


def test_created_registry_has_same_devices():
    """Test that created registries have access to same device configs."""
    default_registry = get_registry()
    created_registry = create_registry()

    # Both should have same devices available
    default_devices = {t.type_id for t in default_registry.list_all()}
    created_devices = {t.type_id for t in created_registry.list_all()}

    assert default_devices == created_devices
    assert "bh1750" in created_devices


def test_created_registry_can_create_devices():
    """Test that created registries can create device instances."""
    registry = create_registry()
    device = registry.create("bh1750")
    assert device is not None
    assert "BH1750" in device.name
