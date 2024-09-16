# pylint: disable=protected-access, redefined-outer-name

"""Test cases for AeonBackup functionality."""

import subprocess
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from aeonsync.backup import AeonBackup


@pytest.fixture
def mock_executor():
    """Fixture to mock RemoteExecutor."""
    with patch("aeonsync.backup.RemoteExecutor", autospec=True) as mock:
        executor = mock.return_value
        executor.run_command = MagicMock()
        executor.rsync = MagicMock()
        yield executor


@pytest.fixture
def aeon_backup(sample_config, mock_executor):
    """Fixture to create an AeonBackup instance with mocked datetime."""
    with patch("aeonsync.backup.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 9, 15)
        return AeonBackup(sample_config, executor=mock_executor)


def test_aeon_backup_create_backup(aeon_backup):
    """Test the AeonBackup.create_backup method.

    Ensures that the create_backup method invokes subprocess.run
    at least twice for necessary backup operations like mkdir and rsync.
    """
    aeon_backup.create_backup()
    assert (
        aeon_backup.executor.run_command.call_count >= 2
    ), "create_backup should call run_command at least twice."


def test_aeon_backup_needs_full_backup(aeon_backup):
    """Test the AeonBackup.needs_full_backup method.

    Verifies that needs_full_backup correctly determines whether
    a full backup is required based on subprocess.run outcomes.
    """
    # Simulate subprocess.run raising a CalledProcessError on the first call
    # and succeeding on the second call
    aeon_backup.executor.run_command.side_effect = [
        subprocess.CalledProcessError(returncode=1, cmd="test -e latest"),
        MagicMock(returncode=0),
    ]

    # First call should indicate that a full backup is needed
    assert (
        aeon_backup.needs_full_backup() is True
    ), "needs_full_backup should return True when subprocess.run fails."

    # Second call should indicate that a full backup is not needed
    assert (
        aeon_backup.needs_full_backup() is False
    ), "needs_full_backup should return False when subprocess.run succeeds."


def test_get_next_backup_name_no_existing_backups(aeon_backup):
    """Test _get_next_backup_name when no existing backups are present."""
    aeon_backup.config = aeon_backup.config._replace(daily=False)
    aeon_backup.executor.run_command.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="ls"
    )
    backup_name = aeon_backup._get_next_backup_name()
    assert backup_name == aeon_backup.date


def test_get_next_backup_name_with_existing_backups(aeon_backup):
    """Test _get_next_backup_name with existing backups present."""
    aeon_backup.config = aeon_backup.config._replace(daily=False)
    aeon_backup.date = "2024-09-14"
    mock_ls_output = MagicMock()
    mock_ls_output.stdout = "2024-09-14\n2024-09-14.1\n2024-09-14.2\n"
    aeon_backup.executor.run_command.return_value = mock_ls_output
    backup_name = aeon_backup._get_next_backup_name()
    assert backup_name == "2024-09-14.3"


def test_aeon_backup_with_daily_option(sample_config, mock_executor):
    """Test that the backup name is correctly set when daily is True."""
    config = sample_config._replace(daily=True)
    with patch("aeonsync.backup.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 9, 15)
        backup = AeonBackup(config, executor=mock_executor)
    assert backup.backup_name == "2024-09-15"


def test_aeon_backup_with_sequence_number(sample_config, mock_executor):
    """Test that the backup name includes sequence number when daily is False."""
    config = sample_config._replace(daily=False)
    with patch("aeonsync.backup.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 9, 14)
        backup = AeonBackup(config, executor=mock_executor)
    mock_executor.run_command.return_value.stdout = (
        "2024-09-14\n2024-09-14.1\n2024-09-14.2\n"
    )
    backup_name = backup._get_next_backup_name()
    assert backup_name == "2024-09-14.3"
