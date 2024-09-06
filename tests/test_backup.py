# pylint: disable=redefined-outer-name

import subprocess
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from aeonsync.backup import AeonBackup
from aeonsync.config import BackupConfig


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0, stdout="", stderr="")
        yield mock


@pytest.fixture
def mock_datetime_now():
    with patch("aeonsync.backup.datetime") as mock:
        mock.now.return_value = datetime(2024, 9, 5, 12, 0, 0)
        yield mock


@pytest.fixture
def sample_config():
    return BackupConfig(
        remote="user@host:/path",
        sources=["/local/path"],
        ssh_key="/path/to/key",
        remote_port=22,
        verbose=False,
        dry_run=False,
        retention_period=7,
    )


def test_aeon_backup_create_backup(mock_subprocess_run, sample_config):
    backup = AeonBackup(sample_config)
    backup.create_backup()
    assert mock_subprocess_run.call_count >= 2  # At least mkdir and rsync calls


def test_aeon_backup_needs_full_backup(mock_subprocess_run, sample_config):
    backup = AeonBackup(sample_config)
    mock_subprocess_run.side_effect = [
        subprocess.CalledProcessError(1, "cmd"),
        MagicMock(returncode=0),
    ]
    assert backup.needs_full_backup() is True
    assert backup.needs_full_backup() is False


if __name__ == "__main__":
    pytest.main()
