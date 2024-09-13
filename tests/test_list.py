import pytest
from unittest.mock import patch
from aeonsync.list import ListBackups
from aeonsync.config import BackupConfig
from aeonsync.utils import RemoteExecutor


@pytest.fixture
def sample_config():
    return BackupConfig(
        remote="user@host:/backups",
        sources=["/home/user"],
        ssh_key="/path/to/key",
        remote_port=22,
        verbose=False,
        dry_run=False,
        retention_period=7,
    )


@patch.object(RemoteExecutor, "run_command")
def test_list_backups(mock_run_command, sample_config):
    mock_run_command.return_value.stdout = """
{"date": "2023-09-10", "start_time": "2023-09-10T12:00:00", "end_time": "2023-09-10T12:30:00", "hostname": "myhost", "sources": ["/home/user"], "stats": {"number_of_files": "100", "total_file_size": "500000"}}
{"date": "2023-09-09", "start_time": "2023-09-09T12:00:00", "end_time": "2023-09-09T12:25:00", "hostname": "myhost", "sources": ["/home/user"], "stats": {"number_of_files": "90", "total_file_size": "450000"}}
"""
    list_backups = ListBackups(sample_config)
    list_backups.list()
    # Verify that run_command was called
    mock_run_command.assert_called_once()
