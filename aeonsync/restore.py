# pylint: disable=useless-parent-delegation,too-few-public-methods

"""Restore functionality for AeonSync."""

import logging
import subprocess

from aeonsync import BaseCommand
from aeonsync.config import HOSTNAME, BackupConfig

logger = logging.getLogger(__name__)


class AeonRestore(BaseCommand):
    """Handles restore operations for AeonSync."""

    def __init__(self, config: BackupConfig):
        """
        Initialize AeonRestore with backup configuration.

        Args:
            config (BackupConfig): Backup configuration
        """
        super().__init__(config)

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

        source = f"{self.remote_info.user}@{self.remote_info.host}:{remote_file_path}"
        destination = file_path

        try:
            self.executor.rsync(source, destination)
            logger.info("File restored successfully")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restore file: %s", e)
            raise
