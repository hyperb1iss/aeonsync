"""Test suite for AeonSync ListBackups functionality."""

import pytest

from aeonsync.list import ListBackups


def test_list_backups(mock_subprocess_run, sample_config):
    """Test the ListBackups.list method."""
    mock_subprocess_run.return_value.stdout = """
{"date": "2023-09-10", "start_time": "2023-09-10T12:00:00", "end_time": "2023-09-10T12:30:00", "hostname": "myhost", "sources": ["/home/user"], "stats": {"number_of_files": "100", "total_file_size": "500000"}}
{"date": "2023-09-09", "start_time": "2023-09-09T12:00:00", "end_time": "2023-09-09T12:25:00", "hostname": "myhost", "sources": ["/home/user"], "stats": {"number_of_files": "90", "total_file_size": "450000"}}
"""
    list_backups = ListBackups(sample_config)
    list_backups.list()
    # Verify that subprocess.run was called via RemoteExecutor
    mock_subprocess_run.assert_called_once()


if __name__ == "__main__":
    pytest.main()
