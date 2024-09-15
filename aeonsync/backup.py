"""Backup functionality for AeonSync."""

import json
import logging
from datetime import datetime
import subprocess
from typing import List, Any, Optional
from pathlib import Path, PosixPath

from aeonsync import BaseCommand
from aeonsync.config import HOSTNAME, METADATA_FILE_NAME, EXCLUSIONS, BackupConfig
from aeonsync.utils import RemoteExecutor, get_backup_stats

logger = logging.getLogger(__name__)


class AeonBackup(BaseCommand):
    """Handles backup operations for AeonSync."""

    def __init__(self, config: BackupConfig, executor: Optional[RemoteExecutor] = None):
        """
        Initialize AeonBackup with the provided configuration.

        Args:
            config (BackupConfig): Backup configuration
        """
        super().__init__(config)
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.executor = executor or RemoteExecutor(
            self.remote_info,
            self.config.ssh_key,
            self.config.remote_port,
        )
        if self.config.daily:
            self.backup_name = self.date
        else:
            self.backup_name = self._get_next_backup_name()
        self.backup_path = f"{self.remote_info.path}/{HOSTNAME}/{self.backup_name}"
        self.latest_link = f"{self.remote_info.path}/{HOSTNAME}/latest"

    def create_backup(self) -> None:
        """Create a full or incremental backup."""
        logger.info("Creating %s backup", "full" if self.config.full else "incremental")

        self._create_remote_dir()
        rsync_output = self._perform_backup()

        if not self.config.dry_run:
            self._update_latest_symlink()
            self._save_backup_metadata(rsync_output)

        logger.info("Backup created successfully")

    def _create_remote_dir(self) -> None:
        """Create the remote directory for the backup."""
        logger.debug("Creating remote directory: %s", self.backup_path)
        self.executor.run_command(f"mkdir -p {self.backup_path}")

    def _perform_backup(self) -> str:
        """Perform the actual backup using rsync."""
        extra_args = self._build_rsync_extra_args()
        source = str(self.config.sources[0])  # Assuming single source for simplicity
        destination = (
            f"{self.remote_info.user}@{self.remote_info.host}:{self.backup_path}"
        )

        try:
            result = self.executor.rsync(source, destination, extra_args)
            logger.debug("Rsync output: %s", result.stdout)

            # Process and log the backup stats
            stats = get_backup_stats(result.stdout)
            for key, value in stats.items():
                logger.info("%s: %s", key.replace("_", " ").title(), value)

            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error("Rsync command failed: %s", e.stderr)
            raise

    def _build_rsync_extra_args(self) -> List[str]:
        """Build extra arguments for the rsync command."""
        extra_args = ["--delete", "--stats"]
        for exclusion in EXCLUSIONS:
            extra_args.extend(["--exclude", exclusion])
        if not self.config.full:
            extra_args.extend(["--link-dest", "../latest"])
        if self.config.dry_run:
            extra_args.append("--dry-run")
        if self.config.verbose:
            extra_args.append("--progress")
        return extra_args

    def _update_latest_symlink(self) -> None:
        """Update the 'latest' symlink to point to the most recent backup."""
        logger.debug("Updating latest symlink to: %s", self.backup_path)
        self.executor.run_command(f"ln -snf {self.backup_path} {self.latest_link}")

    def _save_backup_metadata(self, rsync_output: str) -> None:
        """Save the backup metadata to a file in the backup directory."""
        logger.debug("Saving backup metadata")
        start_time = datetime.now()
        stats = get_backup_stats(rsync_output)
        end_time = datetime.now()
        duration = end_time - start_time
        metadata = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration.total_seconds(),
            "hostname": HOSTNAME,
            "sources": [str(s) for s in self.config.sources],
            "config": self._serialize_config(self.config._asdict()),
            "stats": stats,
        }
        self.executor.run_command(
            f"echo '{json.dumps(metadata, indent=2)}' > {self.backup_path}/{METADATA_FILE_NAME}"
        )

    def _get_next_backup_name(self) -> str:
        """Generate the next backup name with an incrementing sequence number."""
        cmd = f"ls -1 {self.remote_info.path}/{HOSTNAME}"
        try:
            result = self.executor.run_command(cmd)
            backups = []
            for line in result.stdout.strip().split("\n"):
                if line.startswith(self.date):
                    backups.append(line)
            if not backups:
                return self.date
            # Find the highest sequence number
            max_seq = 0
            for backup in backups:
                if backup == self.date:
                    seq = 0
                else:
                    parts = backup.split(".")
                    if len(parts) == 2 and parts[0] == self.date and parts[1].isdigit():
                        seq = int(parts[1])
                        max_seq = max(max_seq, seq)
            next_seq = max_seq + 1
            return f"{self.date}.{next_seq}"
        except subprocess.CalledProcessError:
            # If the directory doesn't exist, start with the date
            return self.date

    @staticmethod
    def _serialize_config(config: Any) -> Any:
        """Recursively serialize config to ensure JSON compatibility."""
        if isinstance(config, (Path, PosixPath)):
            return str(config)
        if isinstance(config, dict):
            return {k: AeonBackup._serialize_config(v) for k, v in config.items()}
        if isinstance(config, list):
            return [AeonBackup._serialize_config(v) for v in config]
        if isinstance(config, tuple):
            return tuple(AeonBackup._serialize_config(v) for v in config)

        return config

    def cleanup_old_backups(self) -> None:
        """Remove backups older than the specified retention period."""
        logger.info(
            "Cleaning up old backups (retention period: %d days)",
            self.config.retention_period,
        )
        cmd = (
            f"find {self.remote_info.path}/{HOSTNAME} -maxdepth 1 -type d "
            f"-name '20*-*-*' -mtime +{self.config.retention_period} -exec rm -rf {{}} \\;"
        )
        self.executor.run_command(cmd)
        logger.info("Old backups cleaned up successfully")

    def needs_full_backup(self) -> bool:
        """Determine if a full backup is needed."""
        logger.debug("Checking if full backup is needed")
        try:
            self.executor.run_command(f"test -e {self.latest_link}")
            logger.info("Incremental backup possible")
            return False
        except subprocess.CalledProcessError:
            logger.info("Full backup needed")
            return True
