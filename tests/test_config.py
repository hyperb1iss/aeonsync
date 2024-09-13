"""Tests for AeonSync configuration management."""

from time import sleep

import pytest

from aeonsync.config import ConfigManager


@pytest.fixture(name="temp_config_dir")
def fixture_temp_config_dir(tmp_path):
    """
    Fixture to provide a temporary directory for config files.

    Args:
        tmp_path (Path): Pytest's temporary path fixture.

    Returns:
        Path: Path to the temporary configuration directory.
    """
    return tmp_path / "config"


@pytest.fixture(name="config_manager")
def fixture_config_manager(temp_config_dir):
    """
    Fixture to provide a ConfigManager instance with a temporary config directory.

    Args:
        temp_config_dir (Path): Temporary configuration directory.

    Returns:
        ConfigManager: Instance of ConfigManager.
    """
    return ConfigManager(config_dir=temp_config_dir)


def test_default_config_creation(config_manager, temp_config_dir):
    """Test that a default configuration file is created if it doesn't exist."""
    config_file_path = temp_config_dir / ConfigManager.CONFIG_FILE_NAME
    assert config_file_path.exists()
    assert config_manager.get("hostname") is not None


def test_config_persistence(config_manager, temp_config_dir):
    """Test that configuration changes are persisted."""
    config_manager.set("test_key", "test_value")
    assert config_manager.get("test_key") == "test_value"

    # Create a new ConfigManager instance to ensure changes were saved
    new_config_manager = ConfigManager(config_dir=temp_config_dir)
    assert new_config_manager.get("test_key") == "test_value"


def test_add_to_list(config_manager):
    """Test adding items to a list configuration."""
    config_manager.add_to_list("source_dirs", "/test/path")
    assert "/test/path" in config_manager.get("source_dirs")


def test_remove_from_list(config_manager):
    """Test removing items from a list configuration."""
    config_manager.add_to_list("exclusions", "*.tmp")
    assert "*.tmp" in config_manager.get("exclusions")
    config_manager.remove_from_list("exclusions", "*.tmp")
    assert "*.tmp" not in config_manager.get("exclusions")


def test_config_types(config_manager):
    """Test that configuration values maintain their types."""
    config_manager.set("int_value", 42)
    config_manager.set("bool_value", True)
    config_manager.set("list_value", [1, 2, 3])

    assert isinstance(config_manager.get("int_value"), int)
    assert isinstance(config_manager.get("bool_value"), bool)
    assert isinstance(config_manager.get("list_value"), list)


def test_nonexistent_key(config_manager):
    """Test behavior when accessing a nonexistent key."""
    assert config_manager.get("nonexistent_key") is None
    assert config_manager.get("nonexistent_key", "default") == "default"


def test_overwrite_protection(config_manager):
    """Test that the configuration is saved when changes are made."""
    original_mtime = config_manager.config_file_path.stat().st_mtime
    # Adding a small delay to ensure timestamp can change
    sleep(0.01)
    config_manager.set("test_key", "test_value")
    sleep(0.01)
    new_mtime = config_manager.config_file_path.stat().st_mtime
    assert (
        new_mtime > original_mtime
    ), f"New mtime {new_mtime} should be greater than original mtime {original_mtime}"
