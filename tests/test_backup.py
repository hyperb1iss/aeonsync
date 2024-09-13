"""Test cases for AeonBackup functionality."""

import subprocess
from unittest.mock import MagicMock

import pytest

from aeonsync.backup import AeonBackup


def test_aeon_backup_create_backup(mock_subprocess_run, sample_config):
    """Test the AeonBackup.create_backup method.

    Ensures that the create_backup method invokes subprocess.run
    at least twice for necessary backup operations like mkdir and rsync.
    """
    backup = AeonBackup(sample_config)
    backup.create_backup()
    assert (
        mock_subprocess_run.call_count >= 2
    ), "create_backup should call subprocess.run at least twice."


def test_aeon_backup_needs_full_backup(mock_subprocess_run, sample_config):
    """Test the AeonBackup.needs_full_backup method.

    Verifies that needs_full_backup correctly determines whether
    a full backup is required based on subprocess.run outcomes.
    """
    backup = AeonBackup(sample_config)
    # Simulate subprocess.run raising a CalledProcessError on the first call
    # and succeeding on the second call
    mock_subprocess_run.side_effect = [
        subprocess.CalledProcessError(returncode=1, cmd="check_backup"),
        MagicMock(returncode=0),
    ]

    # First call should indicate that a full backup is needed
    assert (
        backup.needs_full_backup() is True
    ), "needs_full_backup should return True when subprocess.run fails."

    # Second call should indicate that a full backup is not needed
    assert (
        backup.needs_full_backup() is False
    ), "needs_full_backup should return False when subprocess.run succeeds."


if __name__ == "__main__":
    pytest.main()
