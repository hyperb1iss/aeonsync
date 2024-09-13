"""Shared fixtures for all test modules."""

from unittest.mock import MagicMock, patch

import pytest

from aeonsync.config import BackupConfig


@pytest.fixture
def mock_subprocess_run():
    """Fixture to mock subprocess.run."""
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0, stdout="", stderr="")
        yield mock


@pytest.fixture
def sample_config():
    """Fixture for a sample BackupConfig."""
    return BackupConfig(
        remote="user@host:/path",
        sources=["/home/user/documents", "/home/user/photos"],
        ssh_key="/path/to/key",
        remote_port=22,
        verbose=False,
        dry_run=False,
        retention_period=7,
        log_file="aeon_restore.log",
    )
