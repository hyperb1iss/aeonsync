import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
import subprocess
from aeonsync import backup, restore, utils, config


@pytest.fixture
def mock_subprocess_popen():
    with patch("subprocess.Popen") as mock:
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = ["", ""]  # Simulate end of output
        mock_process.wait.return_value = 0
        mock.return_value = mock_process
        yield mock


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0, stdout="", stderr="")
        yield mock


@pytest.fixture
def mock_datetime_now():
    with patch("aeonsync.backup.datetime") as mock:
        mock.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        yield mock


def test_parse_remote():
    assert utils.parse_remote("user@host:/path") == {
        "user": "user",
        "host": "host",
        "path": "/path",
        "port": None,
    }
    assert utils.parse_remote("host:/path") == {
        "user": None,
        "host": "host",
        "path": "/path",
        "port": None,
    }
    assert utils.parse_remote("user@host:/path", 2222) == {
        "user": "user",
        "host": "host",
        "path": "/path",
        "port": "2222",
    }
    with pytest.raises(ValueError):
        utils.parse_remote("invalid_format")


def test_build_ssh_cmd():
    assert utils.build_ssh_cmd() == ["ssh"]
    assert utils.build_ssh_cmd("/path/to/key") == ["ssh", "-i", "/path/to/key"]
    assert utils.build_ssh_cmd(remote_port=2222) == ["ssh", "-p", "2222"]
    assert utils.build_ssh_cmd("/path/to/key", 2222) == [
        "ssh",
        "-i",
        "/path/to/key",
        "-p",
        "2222",
    ]


def test_get_backup_stats():
    sample_output = """
    Number of files: 1,000
    Number of created files: 10
    Number of deleted files: 5
    Number of regular files transferred: 100
    Total file size: 1.5G
    Total transferred file size: 500M
    Literal data: 400M
    Matched data: 100M
    Total bytes sent: 450M
    Total bytes received: 1M
    """
    stats = utils.get_backup_stats(sample_output)
    assert stats["number_of_files"] == "1,000"
    assert stats["number_of_created_files"] == "10"
    assert stats["number_of_deleted_files"] == "5"
    assert stats["number_of_regular_files_transferred"] == "100"
    assert stats["total_file_size"] == "1.5G"
    assert stats["total_transferred_file_size"] == "500M"
    assert stats["literal_data"] == "400M"
    assert stats["matched_data"] == "100M"
    assert stats["total_bytes_sent"] == "450M"
    assert stats["total_bytes_received"] == "1M"


@patch("aeonsync.backup.create_remote_dir")
@patch("aeonsync.backup.update_latest_symlink")
@patch("aeonsync.backup.save_backup_metadata")
@patch("aeonsync.config.HOSTNAME", "test-hostname")
def test_create_backup(
    mock_save_metadata,
    mock_update_symlink,
    mock_create_dir,
    mock_subprocess_popen,
    mock_datetime_now,
):
    mock_subprocess_popen.return_value.stdout.readline.side_effect = [
        "Number of files: 1,000\n",
        "Number of created files: 10\n",
        "",  # End of output
    ]

    backup.create_backup("user@host:/remote/path", ["/local/path"], False, False)

    mock_subprocess_popen.assert_called()
    mock_create_dir.assert_called_once()
    mock_update_symlink.assert_called_once()
    mock_save_metadata.assert_called_once()


@patch("aeonsync.backup.run_command")
def test_needs_full_backup(mock_run_command):
    mock_run_command.return_value = MagicMock(stdout="exists")
    assert not backup.needs_full_backup("user@host:/remote/path")

    mock_run_command.return_value = MagicMock(stdout="")
    assert backup.needs_full_backup("user@host:/remote/path")

    mock_run_command.side_effect = subprocess.CalledProcessError(1, "cmd")
    assert backup.needs_full_backup("user@host:/remote/path")


@patch("aeonsync.restore.run_command")
@patch("aeonsync.restore.get_hostname", return_value="test-hostname")
def test_restore_file(mock_get_hostname, mock_run_command):
    restore.restore_file("user@host:/remote/path", "2023-01-01", "/path/to/file")
    mock_run_command.assert_called_once()
    args = mock_run_command.call_args[0][0]
    assert args[0] == "rsync"
    assert "user@host:/remote/path/test-hostname/2023-01-01/path/to/file" in args
    assert "/path/to/file" in args


@patch("aeonsync.restore.run_command")
@patch("aeonsync.restore.get_hostname", return_value="test-hostname")
def test_list_backups(mock_get_hostname, mock_run_command):
    restore.list_backups("user@host:/remote/path")
    mock_run_command.assert_called_once()
    args = mock_run_command.call_args[0][0]
    assert args[0] == "ssh"
    assert "user@host" in args
    assert "for d in /remote/path/test-hostname/20*-*-*" in args[2]


if __name__ == "__main__":
    pytest.main()
