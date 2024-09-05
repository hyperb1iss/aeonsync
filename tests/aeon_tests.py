# pylint: disable=redefined-outer-name

import subprocess
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from aeonsync import AeonSync
from aeonsync.backup import AeonBackup
from aeonsync.restore import AeonRestore
from aeonsync.list import ListBackups
from aeonsync.utils import RemoteExecutor, RemoteInfo, parse_remote
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


def test_parse_remote():
    assert parse_remote("user@host:/path") == RemoteInfo(
        user="user", host="host", path="/path", port=None
    )
    assert parse_remote("host:/path") == RemoteInfo(
        user=None, host="host", path="/path", port=None
    )
    assert parse_remote("user@host:/path", 2222) == RemoteInfo(
        user="user", host="host", path="/path", port=2222
    )
    with pytest.raises(ValueError):
        parse_remote("invalid_format")


def test_remote_executor_run_command(mock_subprocess_run):
    remote_info = RemoteInfo(user="user", host="host", path="/path", port=22)
    executor = RemoteExecutor(remote_info, ssh_key="/path/to/key")
    executor.run_command("ls -l")
    mock_subprocess_run.assert_called_once()
    args = mock_subprocess_run.call_args[0][0]
    assert args[0] == "ssh"
    assert "-i" in args
    assert "/path/to/key" in args
    assert "user@host" in args
    assert "ls -l" in args


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


def test_aeon_restore_restore_file(mock_subprocess_run, sample_config):
    restore = AeonRestore(sample_config)
    restore.restore_file("2023-01-01", "/path/to/file")
    mock_subprocess_run.assert_called_once()


def test_list_backups(mock_subprocess_run, sample_config):
    list_backups = ListBackups(sample_config)
    mock_subprocess_run.return_value.stdout = '{"date": "2023-01-01", "stats": {}}'
    list_backups.list()
    mock_subprocess_run.assert_called_once()


def test_aeon_sync_sync(mock_subprocess_run, sample_config):
    sync = AeonSync(sample_config)
    sync.sync()
    assert mock_subprocess_run.call_count >= 2  # At least mkdir and rsync calls


def test_aeon_sync_restore(mock_subprocess_run, sample_config):
    sync = AeonSync(sample_config)
    sync.restore("2023-01-01", "/path/to/file")
    mock_subprocess_run.assert_called_once()


def test_aeon_sync_list_backups(mock_subprocess_run, sample_config):
    sync = AeonSync(sample_config)
    mock_subprocess_run.return_value.stdout = '{"date": "2023-01-01", "stats": {}}'
    sync.list_backups()
    mock_subprocess_run.assert_called_once()


if __name__ == "__main__":
    pytest.main()
