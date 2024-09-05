"""Restore functionality for AeonSync."""

import logging

from aeonsync.utils import RemoteExecutor, RemoteInfo, parse_remote
from aeonsync.config import HOSTNAME, BackupConfig

logger = logging.getLogger(__name__)


class AeonRestore:
    """Handles restore operations for AeonSync."""

    def __init__(self, config: BackupConfig):
        """
        Initialize AeonRestore with backup configuration.

        Args:
            config (BackupConfig): Backup configuration
        """
        self.config = config
        self.remote_info: RemoteInfo = parse_remote(
            self.config.remote, self.config.remote_port
        )
        self.executor = RemoteExecutor(
            self.remote_info, self.config.ssh_key, self.config.remote_port
        )

    def restore_file(self, backup_date: str, file_path: str) -> None:
        """
        Restore a specific file from a backup.

        Args:
            backup_date (str): Date of the backup to restore from
            file_path (str): Path of the file to restore
        """
        logger.info("Restoring file: %s from backup date: %s", file_path, backup_date)
        remote_file_path = (
            f"{self.remote_info.path}/{HOSTNAME}/{backup_date}/{file_path.lstrip('/')}"
        )

        logger.debug("Remote file path: %s", remote_file_path)
        logger.debug("Local file path: %s", file_path)

        self.executor.rsync(remote_file_path, file_path, is_download=True)
        logger.info("File restored successfully")
