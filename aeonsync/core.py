"""Core functionality for AeonSync."""

import logging
from aeonsync.config import BackupConfig
from aeonsync.backup import AeonBackup
from aeonsync.restore import AeonRestore
from aeonsync.list import ListBackups

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
        self.backup = AeonBackup(config)
        self.restore_obj = AeonRestore(config)
        self.list_backups_obj = ListBackups(config)

    def sync(self) -> None:
        """Perform a backup sync operation."""
        full_backup = self.backup.needs_full_backup()
        self.config = self.config._replace(full=full_backup)
        self.backup.config = self.config  # Update the backup's config

        logger.info("Starting %s backup", "full" if full_backup else "incremental")
        self.backup.create_backup()

        if not self.config.dry_run:
            self.backup.cleanup_old_backups()

        logger.info("Backup completed successfully")

    def restore(self, backup_date: str, file_path: str) -> None:
        """
        Restore a file from a specific backup.

        Args:
            backup_date (str): Date of the backup to restore from
            file_path (str): Path of the file to restore
        """
        self.restore_obj.restore_file(backup_date, file_path)

    def list_backups(self) -> None:
        """List all available backups with their metadata."""
        self.list_backups_obj.list()
