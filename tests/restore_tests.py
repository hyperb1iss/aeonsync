import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime, timezone
from aeonsync.restore import AeonRestore
from aeonsync.config import BackupConfig


@pytest.fixture
def mock_config():
    return BackupConfig(
        remote="user@host:/backup",
        sources=["/home/user/documents", "/home/user/photos"],
        ssh_key="/path/to/key",
        remote_port=22,
        verbose=False,
        dry_run=False,
        retention_period=7,
        log_file="aeon_restore.log",
    )


@pytest.fixture
def aeon_restore(mock_config):
    with patch("aeonsync.restore.Console"), patch("aeonsync.restore.prompt"):
        return AeonRestore(mock_config)


def test_get_remote_relative_path(aeon_restore):
    # Test file within backup source
    assert aeon_restore._get_remote_relative_path(
        Path("/home/user/documents/file.txt")
    ) == Path("file.txt")
    assert aeon_restore._get_remote_relative_path(
        Path("/home/user/photos/image.jpg")
    ) == Path("image.jpg")

    # Test file in subdirectory
    assert aeon_restore._get_remote_relative_path(
        Path("/home/user/documents/subfolder/file.txt")
    ) == Path("subfolder/file.txt")

    # Test file not in backup source
    assert (
        aeon_restore._get_remote_relative_path(Path("/home/user/music/song.mp3"))
        is None
    )


def test_get_file_versions(aeon_restore):
    with patch.object(aeon_restore.executor, "run_command") as mock_run:
        mock_run.return_value.stdout = "2023-01-01\n2023-01-02\n2023-01-03\n"

        with patch.object(aeon_restore, "_file_exists_in_backup", return_value=True):
            versions = aeon_restore._get_file_versions(Path("file.txt"))
            assert versions == ["2023-01-03", "2023-01-02", "2023-01-01"]


def test_file_exists_in_backup(aeon_restore):
    with patch.object(aeon_restore.executor, "run_command") as mock_run:
        mock_run.return_value.stdout = "exists\n"
        assert aeon_restore._file_exists_in_backup("2023-01-01", "file.txt") == True

        mock_run.side_effect = Exception("SSH Error")
        assert aeon_restore._file_exists_in_backup("2023-01-01", "file.txt") == False


@patch("aeonsync.restore.prompt")
def test_select_version(mock_prompt, aeon_restore):
    versions = ["2023-01-03", "2023-01-02", "2023-01-01"]
    mock_prompt.return_value = "2023-01-02"

    selected = aeon_restore._select_version(versions)
    assert selected == "2023-01-02"


@patch("aeonsync.restore.prompt")
def test_get_restore_path(mock_prompt, aeon_restore):
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
def test_handle_restore_conflict(mock_prompt, mock_exists, aeon_restore):
    mock_exists.return_value = True
    mock_prompt.side_effect = ["o", "r", "new_file.txt", "o", "o"]  # Added an extra "o"

    assert aeon_restore._handle_restore_conflict("/tmp/file.txt") == True
    assert aeon_restore._handle_restore_conflict("/tmp/file.txt") == True
    assert aeon_restore._handle_restore_conflict("/tmp/file.txt") == True


@patch("aeonsync.restore.open")
def test_log_restore_operation(mock_open, aeon_restore):
    aeon_restore._log_restore_operation(
        "2023-01-01", "file.txt", "/tmp/restored_file.txt"
    )
    mock_open.assert_called_once()
    mock_open.return_value.__enter__().write.assert_called_once()


@patch.object(AeonRestore, "_get_remote_relative_path")
@patch.object(AeonRestore, "_get_file_versions")
@patch.object(AeonRestore, "_select_version")
@patch.object(AeonRestore, "_preview_and_diff")
@patch.object(AeonRestore, "_get_restore_path")
@patch.object(AeonRestore, "_confirm_and_restore")
def test_restore_file_versions(
    mock_confirm,
    mock_get_path,
    mock_preview,
    mock_select,
    mock_versions,
    mock_relative_path,
    aeon_restore,
):
    mock_relative_path.return_value = Path("file.txt")
    mock_versions.return_value = ["2023-01-03", "2023-01-02", "2023-01-01"]
    mock_select.return_value = "2023-01-02"
    mock_get_path.return_value = "/tmp/restored_file.txt"

    aeon_restore.restore_file_versions("/home/user/documents/file.txt")

    mock_relative_path.assert_called_once_with(Path("/home/user/documents/file.txt"))
    mock_versions.assert_called_once_with(Path("file.txt"))
    mock_select.assert_called_once_with(["2023-01-03", "2023-01-02", "2023-01-01"])
    mock_preview.assert_called_once_with(
        "2023-01-02", "file.txt", "/home/user/documents/file.txt"
    )
    mock_get_path.assert_called_once_with(Path("/home/user/documents/file.txt"), None)
    mock_confirm.assert_called_once_with(
        "2023-01-02", "file.txt", "/tmp/restored_file.txt"
    )


def test_get_file_info(aeon_restore):
    with patch.object(aeon_restore.executor, "run_command") as mock_run:
        mock_run.return_value.stdout = (
            "1024 1609459200\n"
        )  # 1KB file, Jan 1, 2021 00:00:00 UTC
        file_info = aeon_restore._get_file_info("2023-01-01", "file.txt")
        assert file_info["size"] == "1.00 KB"
        # Parse the returned mtime
        mtime_str = file_info["mtime"]
        assert mtime_str.endswith("UTC")  # Verify that UTC is included in the string
        mtime = datetime.strptime(mtime_str, "%Y-%m-%d %H:%M:%S %Z")
        assert mtime.date().isoformat() == "2021-01-01"
        # Since strptime doesn't set tzinfo, we need to check the string itself
        assert "UTC" in mtime_str


def test_format_size(aeon_restore):
    assert aeon_restore._format_size(500) == "500.00 B"
    assert aeon_restore._format_size(1024) == "1.00 KB"
    assert aeon_restore._format_size(1048576) == "1.00 MB"
    assert aeon_restore._format_size(1073741824) == "1.00 GB"


@patch("aeonsync.restore.Table")
@patch("aeonsync.restore.Console")
def test_show_restore_summary(mock_console_class, mock_table, aeon_restore):
    mock_console = Mock()
    mock_console_class.return_value = mock_console
    aeon_restore.console = mock_console
    with patch.object(aeon_restore, "_get_file_info") as mock_get_info:
        mock_get_info.return_value = {"size": "1.00 KB", "mtime": "2021-01-01 00:00:00"}
        aeon_restore._show_restore_summary(
            "2023-01-01", "file.txt", "/tmp/restored_file.txt"
        )
        mock_table.assert_called_once()
        mock_console.print.assert_called_once()


# Add more tests as needed for other methods and edge cases
