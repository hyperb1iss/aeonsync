"""Backup functionality for AeonSync."""

import json
import logging
import subprocess
from datetime import datetime
from typing import List, Any, Dict
from pathlib import Path, PosixPath

from aeonsync.config import HOSTNAME, METADATA_FILE_NAME, EXCLUSIONS, BackupConfig
from aeonsync.utils import RemoteExecutor, RemoteInfo, parse_remote, get_backup_stats

logger = logging.getLogger(__name__)


class AeonBackup:
    """Handles backup operations for AeonSync."""

    def __init__(self, config: BackupConfig):
        """
        Initialize AeonBackup with the provided configuration.

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
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.backup_path = f"{self.remote_info.path}/{HOSTNAME}/{self.date}"
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
        cmd = self._build_rsync_command()
        logger.debug("Rsync command: %s", " ".join(cmd))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug("Rsync output: %s", result.stdout)

            # Process and log the backup stats
            stats = get_backup_stats(result.stdout)
            for key, value in stats.items():
                logger.info("%s: %s", key.replace("_", " ").title(), value)

            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error("Rsync command failed: %s", e.stderr)
            raise

    def _build_rsync_command(self) -> List[str]:
        """Build the rsync command for the backup operation."""
        cmd = ["rsync", "-avz", "--delete", "--stats"]
        for exclusion in EXCLUSIONS:
            cmd.extend(["--exclude", exclusion])
        if not self.config.full:
            cmd.extend(["--link-dest", f"../{HOSTNAME}/latest"])
        if self.config.dry_run:
            cmd.append("--dry-run")
        if self.config.verbose:
            cmd.append("--progress")

        # Add SSH options
        ssh_opts = self._build_ssh_options()
        cmd.extend(["-e", f"ssh {ssh_opts}"])

        # Convert all sources to strings
        str_sources = [str(s) for s in self.config.sources]

        # Construct the remote path correctly
        remote_path = f"{self.remote_info.user}@{self.remote_info.host}:{self.remote_info.path}/{HOSTNAME}/{self.date}"

        cmd.extend(str_sources + [remote_path])

        return cmd

    def _build_ssh_options(self) -> str:
        """Build SSH options string."""
        opts = []
        if self.config.ssh_key:
            opts.append(f"-i {self.config.ssh_key}")
        if self.config.remote_port:
            opts.append(f"-p {self.config.remote_port}")
        return " ".join(opts)

    def _update_latest_symlink(self) -> None:
        """Update the 'latest' symlink to point to the most recent backup."""
        logger.debug("Updating latest symlink to: %s", self.backup_path)
        self.executor.run_command(f"ln -snf {self.backup_path} {self.latest_link}")

    def _save_backup_metadata(self, rsync_output: str) -> None:
        """Save the backup metadata to a file in the backup directory."""
        logger.debug("Saving backup metadata")
        stats = get_backup_stats(rsync_output)
        metadata = {
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "hostname": HOSTNAME,
            "sources": [str(s) for s in self.config.sources],
            "config": self._serialize_config(self.config._asdict()),
            "stats": stats,
        }
        self.executor.run_command(
            f"echo '{json.dumps(metadata, indent=2)}' > {self.backup_path}/{METADATA_FILE_NAME}"
        )

    @staticmethod
    def _serialize_config(config: Any) -> Any:
        """Recursively serialize config to ensure JSON compatibility."""
        if isinstance(config, (Path, PosixPath)):
            return str(config)
        elif isinstance(config, dict):
            return {k: AeonBackup._serialize_config(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [AeonBackup._serialize_config(v) for v in config]
        elif isinstance(config, tuple):
            return tuple(AeonBackup._serialize_config(v) for v in config)
        else:
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
        except Exception:
            logger.info("Full backup needed")
            return True
