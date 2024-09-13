# pylint: disable=protected-access, redefined-outer-name, too-many-arguments, unused-argument
"""Test cases for AeonRestore functionality."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

from aeonsync.restore import AeonRestore
from aeonsync.config import BackupConfig


@pytest.fixture
def aeon_restore(sample_config):
    """Fixture for AeonRestore instance."""
    with patch("aeonsync.restore.Console"), patch("aeonsync.restore.prompt"):
        return AeonRestore(sample_config)


def test_get_remote_relative_path(aeon_restore, sample_config):
    """Test the _get_remote_relative_path method."""
    # Create a new BackupConfig instance for testing
    test_config = BackupConfig(
        remote=aeon_restore.config.remote,
        sources=["/home/user"],
        full=False,
        dry_run=False,
        ssh_key=None,
        remote_port=None,
        verbose=False,
        retention_period=7,
        log_file=None,
    )
    aeon_restore.config = test_config

    # Test file within backup source
    assert aeon_restore._get_remote_relative_path(
        Path("/home/user/documents/file.txt")
    ) == Path("user/documents/file.txt")
    assert aeon_restore._get_remote_relative_path(
        Path("/home/user/photos/image.jpg")
    ) == Path("user/photos/image.jpg")

    # Test file in subdirectory
    assert aeon_restore._get_remote_relative_path(
        Path("/home/user/documents/subfolder/file.txt")
    ) == Path("user/documents/subfolder/file.txt")

    # Test file not in backup source
    assert (
        aeon_restore._get_remote_relative_path(Path("/home/other_user/music/song.mp3"))
        is None
    )

    # Test with multiple sources
    test_config = BackupConfig(
        remote=aeon_restore.config.remote,
        sources=["/home/user", "/var/www"],
        full=False,
        dry_run=False,
        ssh_key=None,
        remote_port=None,
        verbose=False,
        retention_period=7,
        log_file=None,
    )
    aeon_restore.config = test_config

    assert aeon_restore._get_remote_relative_path(
        Path("/var/www/html/index.html")
    ) == Path("www/html/index.html")


def test_get_path_versions(aeon_restore):
    """Test the _get_path_versions method."""
    with patch.object(aeon_restore.executor, "run_command") as mock_run:
        mock_run.return_value.stdout = "2023-01-01\n2023-01-02\n2023-01-03\n"

        with patch.object(aeon_restore, "_path_exists_in_backup", return_value=True):
            versions = aeon_restore._get_path_versions(Path("file.txt"))
            assert versions == ["2023-01-03", "2023-01-02", "2023-01-01"]


def test_path_exists_in_backup(aeon_restore):
    """Test the _path_exists_in_backup method."""
    with patch.object(aeon_restore.executor, "run_command") as mock_run:
        # Test when path exists
        mock_run.return_value.stdout = "exists\n"
        assert aeon_restore._path_exists_in_backup("2023-01-01", "file.txt") is True

        # Test when path doesn't exist
        mock_run.return_value.stdout = ""
        assert aeon_restore._path_exists_in_backup("2023-01-01", "file.txt") is False

        # Test when an exception occurs
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        assert aeon_restore._path_exists_in_backup("2023-01-01", "file.txt") is False


@patch("aeonsync.restore.prompt")
def test_select_version(mock_prompt, aeon_restore):
    """Test the _select_version method."""
    versions = ["2023-01-03", "2023-01-02", "2023-01-01"]
    mock_prompt.return_value = "2023-01-02"

    selected = aeon_restore._select_version(versions)
    assert selected == "2023-01-02"


@patch("aeonsync.restore.prompt")
def test_get_restore_path(mock_prompt, aeon_restore):
    """Test the _get_restore_path method."""
    mock_prompt.return_value = "/tmp/restored_file.txt"

    restore_path = aeon_restore._get_restore_path(Path("/home/user/documents/file.txt"))
    assert restore_path == "/tmp/restored_file.txt"

    # Test with output_dir
    restore_path = aeon_restore._get_restore_path(
        Path("/home/user/documents/file.txt"), Path("/tmp")
    )
    assert restore_path == "/tmp/file.txt"


@patch("aeonsync.restore.os.path.exists")
@patch("aeonsync.restore.prompt")
def test_get_restore_path_existing_file(mock_prompt, mock_exists, aeon_restore):
    """Test handling existing restore path."""
    # Test when the file already exists and user chooses to overwrite
    mock_exists.return_value = True
    mock_prompt.side_effect = [
        "/tmp/restored_file.txt",
        "y",  # User confirms overwrite
    ]

    restore_path = aeon_restore._get_restore_path(Path("/home/user/documents/file.txt"))
    assert restore_path == "/tmp/restored_file.txt"


@patch("aeonsync.restore.open")
def test_log_restore_operation(mock_open, aeon_restore):
    """Test the logging of restore operations."""
    with mock_open() as mock_file:
        aeon_restore._log_restore_operation(
            "2023-01-01", "file.txt", "/tmp/restored_file.txt"
        )
        mock_file.write.assert_called_once()



@patch.object(Path, "is_file", return_value=True)
@patch.object(AeonRestore, "_confirm_and_restore")
@patch.object(AeonRestore, "_get_restore_path")
@patch.object(AeonRestore, "_preview_and_diff")
@patch.object(AeonRestore, "_select_version")
@patch.object(AeonRestore, "_get_path_versions")
@patch.object(AeonRestore, "_get_remote_relative_path")
def test_restore_file_versions(
    mock_get_remote_relative_path,
    mock_get_versions,
    mock_select_version,
    mock_preview_and_diff,
    mock_get_path,
    mock_confirm,
    _mock_is_file,
    aeon_restore,
):
    """Test the restore_file_versions method for files."""
    mock_get_remote_relative_path.return_value = Path("file.txt")
    mock_get_versions.return_value = ["2023-01-03", "2023-01-02", "2023-01-01"]
    mock_select_version.return_value = "2023-01-02"
    mock_get_path.return_value = "/tmp/restored_file.txt"

    aeon_restore.restore_file_versions(
        "/home/user/documents/file.txt", diff=True, preview=True
    )

    mock_get_remote_relative_path.assert_called_once_with(
        Path("/home/user/documents/file.txt")
    )
    mock_get_versions.assert_called_once_with(Path("file.txt"))
    mock_select_version.assert_called_once_with(
        ["2023-01-03", "2023-01-02", "2023-01-01"]
    )
    mock_preview_and_diff.assert_called_once_with(
        "2023-01-02",
        "file.txt",
        "/home/user/documents/file.txt",
        diff=True,
        preview=True,
    )
    mock_get_path.assert_called_once_with(Path("/home/user/documents/file.txt"), None)
    mock_confirm.assert_called_once_with(
        "2023-01-02", "file.txt", "/tmp/restored_file.txt", is_directory=False
    )


def test_get_file_info(aeon_restore):
    """Test the _get_file_info method."""
    with patch.object(aeon_restore.executor, "run_command") as mock_run:
        mock_run.return_value.stdout = (
            "1024 1609459200\n"
        )  # 1KB file, Jan 1, 2021 00:00:00 UTC
        file_info = aeon_restore._get_file_info("2023-01-01", "file.txt")
        assert file_info["size"] == "1.00 KB"
        assert file_info["mtime"] == "2021-01-01 00:00:00 UTC"


def test_format_size(aeon_restore):
    """Test the _format_size method."""
    assert aeon_restore._format_size(500) == "500.00 B"
    assert aeon_restore._format_size(1024) == "1.00 KB"
    assert aeon_restore._format_size(1048576) == "1.00 MB"
    assert aeon_restore._format_size(1073741824) == "1.00 GB"


def test_show_restore_summary(aeon_restore):
    """Test the _show_restore_summary method."""
    with patch("aeonsync.restore.Table") as mock_table_class:
        mock_table = Mock()
        mock_table_class.return_value = mock_table
        with patch.object(aeon_restore, "_get_file_info") as mock_get_info:
            mock_get_info.return_value = {
                "size": "1.00 KB",
                "mtime": "2021-01-01 00:00:00 UTC",
            }
            aeon_restore._show_restore_summary(
                "2023-01-01", "file.txt", "/tmp/restored_file.txt"
            )
            mock_table_class.assert_called_once()

            expected_calls = [
                call("Backup Date", "2023-01-01"),
                call("Source File", "file.txt"),
                call("Restore Path", "/tmp/restored_file.txt"),
                call("File Size", "1.00 KB"),
                call("Last Modified", "2021-01-01 00:00:00 UTC"),
            ]
            mock_table.add_row.assert_has_calls(expected_calls)


@patch.object(Path, "is_file", return_value=False)
@patch.object(Path, "is_dir", return_value=True)
@patch.object(AeonRestore, "_confirm_and_restore")
@patch.object(AeonRestore, "_get_restore_path")
@patch.object(AeonRestore, "_select_version")
@patch.object(AeonRestore, "_get_path_versions")
@patch.object(AeonRestore, "_get_remote_relative_path")
def test_restore_directory_versions(
    mock_get_remote_relative_path,
    mock_get_versions,
    mock_select_version,
    mock_get_path,
    mock_confirm,
    _mock_is_dir,
    _mock_is_file,
    aeon_restore,
):
    """Test the restore_file_versions method for directories."""
    mock_get_remote_relative_path.return_value = Path("documents")
    mock_get_versions.return_value = ["2023-01-03", "2023-01-02", "2023-01-01"]
    mock_select_version.return_value = "2023-01-02"
    mock_get_path.return_value = "/tmp/documents"

    aeon_restore.restore_file_versions(
        "/home/user/documents", diff=False, preview=False
    )

    mock_get_remote_relative_path.assert_called_once_with(Path("/home/user/documents"))
    mock_get_versions.assert_called_once_with(Path("documents"))
    mock_select_version.assert_called_once_with(
        ["2023-01-03", "2023-01-02", "2023-01-01"]
    )
    mock_get_path.assert_called_once_with(Path("/home/user/documents"), None)
    mock_confirm.assert_called_once_with(
        "2023-01-02", "documents", "/tmp/documents", is_directory=True
    )
