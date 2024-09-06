# pylint: disable=import-outside-toplevel, too-few-public-methods

"""Main orchestrator for AeonSync operations."""

import logging

from aeonsync.config import BackupConfig
from aeonsync.utils import RemoteInfo, parse_remote, RemoteExecutor

logger = logging.getLogger(__name__)


class BaseCommand:
    """Base class for AeonSync commands."""

    def __init__(self, config: BackupConfig):
        """
        Initialize BaseCommand with backup configuration.

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


class AeonSync:
    """Main class for orchestrating AeonSync operations."""

    def __init__(self, config: BackupConfig):
        """
        Initialize AeonSync with backup configuration.

        Args:
            config (BackupConfig): Backup configuration
        """
        self.config = config

    def sync(self) -> None:
        """Perform a backup sync operation."""
        from aeonsync.backup import AeonBackup

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
        from aeonsync.restore import AeonRestore

        restore = AeonRestore(self.config)
        restore.restore_file(backup_date, file_path)

    def list_backups(self) -> None:
        """List all available backups with their metadata."""
        from aeonsync.list import ListBackups

        list_backups = ListBackups(self.config)
        list_backups.list()
