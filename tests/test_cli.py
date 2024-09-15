# tests/test_cli.py

# pylint: disable=redefined-outer-name
"""Test cases for the AeonSync CLI functionality."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aeonsync.cli import app
from aeonsync.config import BackupConfig

runner = CliRunner()


@pytest.fixture
def mock_config_manager():
    """Fixture for mocking the config manager."""
    with patch("aeonsync.cli.config_manager") as mock:
        mock.get.return_value = None  # Default to None unless specified
        yield mock


@pytest.fixture
def mock_aeon_backup():
    """Fixture for mocking AeonBackup."""
    with patch("aeonsync.cli.AeonBackup") as mock:
        yield mock


@pytest.fixture
def mock_aeon_restore():
    """Fixture for mocking AeonRestore."""
    with patch("aeonsync.cli.AeonRestore") as mock:
        yield mock


@pytest.fixture
def mock_list_backups():
    """Fixture for mocking ListBackups."""
    with patch("aeonsync.cli.ListBackups") as mock:
        yield mock


def test_sync_command(mock_aeon_backup, mock_config_manager):
    """Test the basic sync command without options."""
    mock_config_manager.get.return_value = False  # default_daily_backup = False
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    mock_aeon_backup.assert_called_once()
    args, _ = mock_aeon_backup.call_args
    config = args[0]
    assert isinstance(config, BackupConfig)
    assert config.daily is False


def test_sync_command_with_daily_flag(mock_aeon_backup):
    """Test the sync command with the --daily flag."""
    result = runner.invoke(app, ["sync", "--daily"])
    assert result.exit_code == 0
    mock_aeon_backup.assert_called_once()
    args, _ = mock_aeon_backup.call_args
    config = args[0]
    assert isinstance(config, BackupConfig)
    assert config.daily is True


@patch("aeonsync.cli.Path.exists")
@patch("aeonsync.cli.Path.is_dir")
def test_sync_command_with_options(
    mock_is_dir, mock_exists, mock_aeon_backup, mock_config_manager
):
    """Test the sync command with various options."""
    mock_exists.return_value = True
    mock_is_dir.return_value = True
    mock_config_manager.get.return_value = False  # default_daily_backup = False
    result = runner.invoke(
        app, ["sync", "--source", "/test/path", "--retention", "30", "--dry-run"]
    )
    assert result.exit_code == 0, f"Command failed with output: {result.output}"
    mock_aeon_backup.assert_called_once()
    args, _ = mock_aeon_backup.call_args

    assert isinstance(args[0], BackupConfig)
    config = args[0]

    assert "/test/path" in config.sources
    assert config.retention_period == 30
    assert config.dry_run is True
    assert config.daily is False  # default value


def test_sync_command_with_default_daily_backup(mock_aeon_backup, mock_config_manager):
    """Test the sync command when default_daily_backup is set in config."""
    mock_config_manager.get.side_effect = (
        lambda key, default: True if key == "default_daily_backup" else default
    )
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    mock_aeon_backup.assert_called_once()
    args, _ = mock_aeon_backup.call_args
    config = args[0]
    assert isinstance(config, BackupConfig)
    assert config.daily is True


def test_restore_command(mock_aeon_restore):
    """Test the restore command with specific file and date."""
    result = runner.invoke(app, ["restore", "/test/file.txt", "2023-01-01"])
    assert result.exit_code == 0
    mock_aeon_restore.assert_called_once()
    mock_aeon_restore.return_value.restore_file_versions.assert_called_once_with(
        "/test/file.txt", "2023-01-01", None, diff=False, preview=False
    )


def test_restore_command_interactive(mock_aeon_restore):
    """Test the interactive restore command."""
    result = runner.invoke(app, ["restore", "--interactive"])
    assert result.exit_code == 0
    mock_aeon_restore.assert_called_once()
    mock_aeon_restore.return_value.restore_interactive.assert_called_once_with(
        diff=False, preview=False
    )


def test_list_backups_command(mock_list_backups, mock_config_manager):
    """Test the list-backups command."""
    mock_config_manager.get.return_value = None
    result = runner.invoke(app, ["list-backups"])
    assert result.exit_code == 0
    mock_list_backups.assert_called_once()
    mock_list_backups.return_value.list.assert_called_once()


def test_config_command_show(mock_config_manager):
    """Test the config command with --show option."""
    mock_config_manager.config = {"test_key": "test_value"}
    result = runner.invoke(app, ["config", "--show"])
    assert result.exit_code == 0
    assert "test_key" in result.output
    assert "test_value" in result.output


def test_config_command_set(mock_config_manager):
    """Test setting a configuration value."""
    result = runner.invoke(app, ["config", "--hostname", "new_host"])
    assert result.exit_code == 0
    mock_config_manager.set.assert_called_once_with("hostname", "new_host")


def test_config_command_set_default_daily_backup(mock_config_manager):
    """Test enabling the default_daily_backup flag."""
    result = runner.invoke(app, ["config", "--default-daily-backup"])
    assert result.exit_code == 0
    mock_config_manager.set.assert_called_with("default_daily_backup", True)


def test_config_command_disable_default_daily_backup(mock_config_manager):
    """Test disabling the default_daily_backup flag."""
    result = runner.invoke(app, ["config", "--no-default-daily-backup"])
    assert result.exit_code == 0
    mock_config_manager.set.assert_called_with("default_daily_backup", False)


def test_config_command_add_source_dir(mock_config_manager):
    """Test adding a source directory to the configuration."""
    result = runner.invoke(app, ["config", "--add-source-dir", "/new/source"])
    assert result.exit_code == 0
    mock_config_manager.add_to_list.assert_called_once_with(
        "source_dirs", "/new/source"
    )


def test_config_command_remove_source_dir(mock_config_manager):
    """Test removing a source directory from the configuration."""
    result = runner.invoke(app, ["config", "--remove-source-dir", "/old/source"])
    assert result.exit_code == 0
    mock_config_manager.remove_from_list.assert_called_once_with(
        "source_dirs", "/old/source"
    )


def test_config_command_multiple_changes(mock_config_manager):
    """Test setting multiple configuration values at once."""
    result = runner.invoke(
        app,
        [
            "config",
            "--hostname",
            "new_host",
            "--remote-address",
            "new_remote",
            "--retention-period",
            "14",
        ],
    )
    assert result.exit_code == 0
    mock_config_manager.set.assert_any_call("hostname", "new_host")
    mock_config_manager.set.assert_any_call("remote_address", "new_remote")
    mock_config_manager.set.assert_any_call("retention_period", 14)


# Add more tests as needed for other CLI functionalities
