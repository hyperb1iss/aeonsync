# pylint: disable=protected-access
"""Tests for utility functions and classes in utils.py."""

from unittest.mock import MagicMock, patch

import pytest

from aeonsync.utils import RemoteExecutor, RemoteInfo, get_backup_stats, parse_remote


def test_parse_remote():
    """Test the parse_remote function."""
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


def test_remote_executor_run_command():
    """Test the RemoteExecutor's run_command method."""
    remote_info = RemoteInfo(user="user", host="host", path="/path", port=22)
    executor = RemoteExecutor(remote_info, ssh_key="/path/to/key")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        executor.run_command("ls -l")

        mock_run.assert_called_once()
        args, _ = mock_run.call_args

        # Define the expected command
        expected_cmd = ["ssh", "-i", "/path/to/key", "-p", "22", "user@host", "ls -l"]

        # Assert that the constructed command matches the expected command
        assert (
            args[0] == expected_cmd
        ), f"Expected command {expected_cmd}, but got {args[0]}"


def test_remote_executor_rsync():
    """Test the RemoteExecutor's rsync method."""
    remote_info = RemoteInfo(user="user", host="host", path="/path", port=22)
    executor = RemoteExecutor(remote_info, ssh_key="/path/to/key")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="rsync output", stderr=""
        )
        result = executor.rsync("source", "destination", ["--delete"])

        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        assert "rsync" in args[0]
        assert "--delete" in args[0]
        assert "source" in args[0]
        assert "destination" in args[0]
        assert result.stdout == "rsync output"


def test_get_backup_stats():
    """Test the get_backup_stats utility function."""
    rsync_output = """
Number of files: 100
Number of files transferred: 10
Total file size: 1,024,000 bytes
Total transferred file size: 10,240,000 bytes
Literal data: 500,000 bytes
Matched data: 524,288 bytes
File list size: 1,500
File list generation time: 0.002 seconds
File list transfer time: 0.001 seconds
Total bytes sent: 10,240,000
Total bytes received: 1,500
"""
    expected_stats = {
        "number_of_files": "100",
        "number_of_files_transferred": "10",
        "total_file_size": "1,024,000 bytes",
        "total_transferred_file_size": "10,240,000 bytes",
        "literal_data": "500,000 bytes",
        "matched_data": "524,288 bytes",
        "file_list_size": "1,500",
        "file_list_generation_time": "0.002 seconds",
        "file_list_transfer_time": "0.001 seconds",
        "total_bytes_sent": "10,240,000",
        "total_bytes_received": "1,500",
    }
    stats = get_backup_stats(rsync_output)
    assert stats == expected_stats


def test_remote_executor_build_ssh_options():
    """Test the RemoteExecutor's SSH options building."""
    remote_info = RemoteInfo(user="user", host="host", path="/path", port=2222)
    executor = RemoteExecutor(remote_info, ssh_key="/path/to/key")

    assert executor._build_ssh_options() == "-i /path/to/key -p 2222"

    # Without SSH key and default port
    remote_info = RemoteInfo(user="user", host="host", path="/path", port=22)
    executor = RemoteExecutor(remote_info)

    assert executor._build_ssh_options() == "-p 22"

    # Without SSH key and port
    remote_info = RemoteInfo(user="user", host="host", path="/path", port=None)
    executor = RemoteExecutor(remote_info)

    assert executor._build_ssh_options() == ""
