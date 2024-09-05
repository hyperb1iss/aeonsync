"""Main orchestrator for AeonSync operations."""

import logging

from aeonsync.backup import AeonBackup
from aeonsync.restore import AeonRestore
from aeonsync.list import ListBackups
from aeonsync.config import BackupConfig
from aeonsync.utils import RemoteInfo, parse_remote

logger = logging.getLogger(__name__)


class AeonSync:
    """Main class for orchestrating AeonSync operations."""

    def __init__(self, config: BackupConfig):
        """
        Initialize AeonSync with backup configuration.

        Args:
            config (BackupConfig): Backup configuration
        """
        self.config = config
        self.remote_info: RemoteInfo = parse_remote(
            self.config.remote, self.config.remote_port
        )

    def sync(self) -> None:
        """Perform a backup sync operation."""
        backup = AeonBackup(self.config)
        full_backup = backup.needs_full_backup()
        self.config = self.config._replace(full=full_backup)
        backup.config = self.config  # Update the backup's config

        logger.info("Starting %s backup", "full" if full_backup else "incremental")
        backup.create_backup()

        if not self.config.dry_run:
            backup.cleanup_old_backups()

        logger.info("Backup completed successfully")

    def restore(self, backup_date: str, file_path: str) -> None:
        """
        Restore a file from a specific backup.

        Args:
            backup_date (str): Date of the backup to restore from
            file_path (str): Path of the file to restore
        """
        restore = AeonRestore(self.config)
        restore.restore_file(backup_date, file_path)

    def list_backups(self) -> None:
        """List all available backups with their metadata."""
        list_backups = ListBackups(self.config)
        list_backups.list()
