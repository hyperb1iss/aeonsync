"""
Restore functionality for AeonSync.

This module provides the AeonRestore class, which handles all restore operations
for the AeonSync backup system. It includes functionality for interactive restores,
file version selection, and non-interactive restores.
"""

import os
import logging
import subprocess
from typing import List, Optional, Dict
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich import print as rprint
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter

from aeonsync import BaseCommand
from aeonsync.config import HOSTNAME, BackupConfig
from aeonsync.utils import get_backup_stats

logger = logging.getLogger(__name__)


class AeonRestore(BaseCommand):
    """Handles enhanced restore operations for AeonSync."""

    def __init__(self, config: BackupConfig):
        """
        Initialize AeonRestore with the provided configuration.

        Args:
            config (BackupConfig): Backup configuration object
        """
        super().__init__(config)
        self.console = Console()
        logger.debug("AeonRestore initialized with config: %s", config)

    def restore_interactive(self) -> None:
        """
        Perform an interactive restore process.

        This method guides the user through selecting a backup date,
        choosing a file to restore, and specifying the restore location.
        """
        logger.debug("Starting interactive restore process")
        backup_date = self._select_backup_date()
        file_path = self._select_file(backup_date)
        remote_relative_path = self._get_remote_relative_path(Path(file_path))
        if not remote_relative_path:
            logger.warning(
                "File '%s' is not within any of the backup source directories",
                file_path,
            )
            self.console.print(
                f"[yellow]'{file_path}' is not within any of the backup source directories.[/yellow]"
            )
            return
        self._preview_and_diff(backup_date, str(remote_relative_path), file_path)
        restore_path = self._get_restore_path(Path(file_path))
        self._confirm_and_restore(backup_date, str(remote_relative_path), restore_path)

    def restore_file_versions(
        self,
        file_path: str,
        specific_date: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Restore a file with version selection.

        Args:
            file_path (str): Path of the file to restore
            specific_date (Optional[str]): Specific backup date to restore from
            output_dir (Optional[Path]): Directory to restore the file to
        """
        logger.debug("Starting restore_file_versions for file: %s", file_path)
        local_file_path = Path(file_path).resolve()
        logger.debug("Resolved local file path: %s", local_file_path)
        remote_relative_path = self._get_remote_relative_path(local_file_path)
        logger.debug("Remote relative path: %s", remote_relative_path)

        if not remote_relative_path:
            logger.warning(
                "File '%s' is not within any of the backup source directories",
                file_path,
            )
            self.console.print(
                f"[yellow]'{file_path}' is not within any of the backup source directories.[/yellow]"
            )
            return

        available_versions = self._get_file_versions(remote_relative_path)
        logger.debug("Available versions: %s", available_versions)
        if not available_versions:
            logger.warning("No backups found for file: %s", file_path)
            self.console.print(f"[yellow]No backups found for '{file_path}'[/yellow]")
            return

        if specific_date:
            if specific_date not in available_versions:
                logger.warning("No backup found for date: %s", specific_date)
                self.console.print(
                    f"[yellow]No backup found for date '{specific_date}'[/yellow]"
                )
                return
            selected_version = specific_date
        else:
            selected_version = self._select_version(available_versions)

        logger.debug("Selected version: %s", selected_version)
        self._preview_and_diff(
            selected_version, str(remote_relative_path), str(local_file_path)
        )
        restore_path = self._get_restore_path(local_file_path, output_dir)
        logger.debug("Restore path: %s", restore_path)
        self._confirm_and_restore(
            selected_version, str(remote_relative_path), restore_path
        )

    def restore_file(
        self, backup_date: str, file_path: str, restore_path: Optional[str] = None
    ) -> None:
        """
        Restore a specific file from a backup (non-interactive mode).

        Args:
            backup_date (str): Date of the backup to restore from
            file_path (str): Path of the file to restore
            restore_path (Optional[str]): Custom path to restore the file to
        """
        logger.debug(
            "Starting restore_file for date: %s, file: %s", backup_date, file_path
        )
        local_file_path = Path(file_path).resolve()
        remote_relative_path = self._get_remote_relative_path(local_file_path)
        if not remote_relative_path:
            logger.warning(
                "File '%s' is not within any of the backup source directories",
                file_path,
            )
            self.console.print(
                f"[yellow]'{file_path}' is not within any of the backup source directories.[/yellow]"
            )
            return

        if not self._file_exists_in_backup(backup_date, str(remote_relative_path)):
            logger.warning("File not found in backup dated %s", backup_date)
            self.console.print(
                f"[red]File not found in the backup dated {backup_date}.[/red]"
            )
            return

        restore_path = restore_path or file_path
        logger.debug("Restore path: %s", restore_path)
        self._perform_restore(backup_date, str(remote_relative_path), restore_path)

    def _get_remote_relative_path(self, local_file_path: Path) -> Optional[Path]:
        """
        Get the relative path of the file in the remote backup.

        Args:
            local_file_path (Path): Local path of the file

        Returns:
            Optional[Path]: Relative path in the remote backup, or None if not in backup sources
        """
        logger.debug("Getting remote relative path for: %s", local_file_path)
        logger.debug("Backup sources: %s", self.config.sources)
        for source in self.config.sources:
            source_path = Path(source).resolve()
            try:
                relative_path = local_file_path.relative_to(source_path)
                logger.debug("Found relative path: %s", relative_path)
                return Path(source_path.name) / relative_path
            except ValueError:
                logger.debug("File not in source: %s", source_path)
                continue
        logger.warning("File not found in any backup source")
        return None

    def _select_backup_date(self) -> str:
        """
        Let the user select a backup date.

        Returns:
            str: Selected backup date
        """
        logger.debug("Selecting backup date")
        backups = self._get_available_backups()
        table = Table(title="Available Backups")
        table.add_column("Date", style="cyan")
        table.add_column("Files", justify="right", style="green")
        table.add_column("Size", justify="right", style="blue")

        for backup in backups:
            stats = get_backup_stats(backup["stats"])
            table.add_row(
                backup["date"],
                stats.get("number_of_files", "N/A"),
                stats.get("total_file_size", "N/A"),
            )

        self.console.print(table)
        while True:
            date = prompt("Enter the backup date to restore from: ")
            if date in [b["date"] for b in backups]:
                logger.debug("Selected backup date: %s", date)
                return date
            logger.warning("Invalid date selected: %s", date)
            self.console.print(
                "[red]Invalid date. Please choose from the list above.[/red]"
            )

    def _get_available_backups(self) -> List[Dict[str, str]]:
        """
        Fetch available backups.

        Returns:
            List[Dict[str, str]]: List of available backups with their stats
        """
        logger.debug("Fetching available backups")
        cmd = f"ls -1 {self.remote_info.path}/{HOSTNAME}"
        result = self.executor.run_command(cmd)
        backups = []
        for line in result.stdout.strip().split("\n"):
            if line.startswith("20") and len(line) == 10:  # Basic date format check
                stats = self._get_backup_stats(line)
                backups.append({"date": line, "stats": stats})
        logger.debug("Found %d backups", len(backups))
        return sorted(
            backups,
            key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"),
            reverse=True,
        )

    def _get_backup_stats(self, date: str) -> str:
        """
        Get stats for a specific backup.

        Args:
            date (str): Backup date

        Returns:
            str: Backup statistics
        """
        logger.debug("Getting backup stats for date: %s", date)
        cmd = f"cat {self.remote_info.path}/{HOSTNAME}/{date}/backup_metadata.json"
        result = self.executor.run_command(cmd)
        return result.stdout

    def _select_file(self, backup_date: str) -> str:
        """
        Let the user select a file to restore.

        Args:
            backup_date (str): Selected backup date

        Returns:
            str: Selected file path
        """
        logger.debug("Selecting file to restore from backup date: %s", backup_date)
        while True:
            file_path = prompt(
                "Enter the path of the file to restore: ", completer=PathCompleter()
            )
            remote_relative_path = self._get_remote_relative_path(Path(file_path))
            if remote_relative_path and self._file_exists_in_backup(
                backup_date, str(remote_relative_path)
            ):
                logger.debug("Selected file: %s", file_path)
                return file_path
            logger.warning("File not found in backup: %s", file_path)
            self.console.print(
                "[red]File not found in the backup. Please try again.[/red]"
            )

    def _file_exists_in_backup(
        self, backup_date: str, remote_relative_path: str
    ) -> bool:
        """
        Check if the file exists in the specified backup.

        Args:
            backup_date (str): Backup date
            remote_relative_path (str): Relative path of the file in the backup

        Returns:
            bool: True if the file exists, False otherwise
        """
        logger.debug(
            "Checking if file exists in backup: date=%s, path=%s",
            backup_date,
            remote_relative_path,
        )
        cmd = f"test -e {self.remote_info.path}/{HOSTNAME}/{backup_date}/{remote_relative_path} && echo 'exists'"
        try:
            result = self.executor.run_command(cmd)
            exists = "exists" in result.stdout
            logger.debug("File exists: %s", exists)
            return exists
        except Exception as e:
            logger.error("Error checking file existence: %s", e)
            return False

    def _preview_and_diff(
        self, backup_date: str, remote_relative_path: str, local_file_path: str
    ) -> None:
        """
        Show a preview of the file and a diff if it exists locally.

        Args:
            backup_date (str): Backup date
            remote_relative_path (str): Relative path of the file in the backup
            local_file_path (str): Local path of the file
        """
        logger.debug(
            "Previewing and diffing file: date=%s, remote_path=%s, local_path=%s",
            backup_date,
            remote_relative_path,
            local_file_path,
        )
        remote_path = (
            f"{self.remote_info.path}/{HOSTNAME}/{backup_date}/{remote_relative_path}"
        )

        # Preview
        cmd = f"cat {remote_path}"
        result = self.executor.run_command(cmd)
        syntax = Syntax(result.stdout, "python", line_numbers=True)
        self.console.print(Panel(syntax, title="File Preview", expand=False))

        # Diff
        if Path(local_file_path).exists():
            cmd = f"diff {local_file_path} {remote_path}"
            try:
                result = self.executor.run_command(cmd)
                if result.stdout:
                    syntax = Syntax(result.stdout, "diff", line_numbers=True)
                    self.console.print(
                        Panel(syntax, title="Diff with current version", expand=False)
                    )
                else:
                    logger.debug("Files are identical")
                    self.console.print(
                        "[green]The file is identical to the current version.[/green]"
                    )
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:  # diff returns 1 if files are different
                    syntax = Syntax(e.stdout, "diff", line_numbers=True)
                    self.console.print(
                        Panel(syntax, title="Diff with current version", expand=False)
                    )
                else:
                    logger.error("Error while diffing: %s", e)
                    self.console.print(f"[red]Error while diffing: {e}[/red]")
        else:
            logger.debug("Local file does not exist, no diff available")
            self.console.print(
                "[yellow]The file doesn't exist locally. No diff available.[/yellow]"
            )

    def _get_restore_path(
        self, original_path: Path, output_dir: Optional[Path] = None
    ) -> str:
        """
        Determine the restore path based on the original path and output directory.

        Args:
            original_path (Path): Original path of the file
            output_dir (Optional[Path]): Output directory for the restored file

        Returns:
            str: Path to restore the file to
        """
        logger.debug(
            "Getting restore path: original_path=%s, output_dir=%s",
            original_path,
            output_dir,
        )
        if output_dir:
            restore_path = str(output_dir / original_path.name)
            logger.debug("Restore path (with output_dir): %s", restore_path)
            return restore_path

        default_path = str(original_path)
        while True:
            restore_path = prompt(
                f"Enter the restore path [{default_path}]: ",
                default=default_path,
                completer=PathCompleter(),
            )
            if (
                not os.path.exists(restore_path)
                or prompt(
                    f"[yellow]'{restore_path}' already exists. Overwrite? (y/n): [/yellow]"
                ).lower()
                == "y"
            ):
                logger.debug("Final restore path: %s", restore_path)
                return restore_path
            logger.debug("User chose not to overwrite existing file")
            self.console.print(
                "[red]Please choose a different path or confirm overwrite.[/red]"
            )

    def _confirm_and_restore(
        self, backup_date: str, remote_relative_path: str, restore_path: str
    ) -> None:
        """
        Confirm the restore operation and perform it.

        Args:
            backup_date (str): Backup date
            remote_relative_path (str): Relative path of the file in the backup
            restore_path (str): Path to restore the file to
        """
        logger.debug(
            "Confirming restore: date=%s, remote_path=%s, restore_path=%s",
            backup_date,
            remote_relative_path,
            restore_path,
        )
        rprint(f"[bold]Restore Summary:[/bold]")
        rprint(f"  Backup Date: [cyan]{backup_date}[/cyan]")
        rprint(f"  Source File: [yellow]{remote_relative_path}[/yellow]")
        rprint(f"  Restore Path: [green]{restore_path}[/green]")

        confirm = prompt("Do you want to proceed with the restore? (y/n): ").lower()
        if confirm != "y":
            logger.debug("User cancelled restore operation")
            self.console.print("[yellow]Restore operation cancelled.[/yellow]")
            return

        self._perform_restore(backup_date, remote_relative_path, restore_path)

    def _perform_restore(
        self, backup_date: str, remote_relative_path: str, restore_path: str
    ) -> None:
        """
        Perform the actual file restore.

        Args:
            backup_date (str): Backup date
            remote_relative_path (str): Relative path of the file in the backup
            restore_path (str): Path to restore the file to
        """
        logger.debug(
            "Performing restore: date=%s, remote_path=%s, restore_path=%s",
            backup_date,
            remote_relative_path,
            restore_path,
        )
        remote_file_path = (
            f"{self.remote_info.path}/{HOSTNAME}/{backup_date}/{remote_relative_path}"
        )
        source = f"{self.remote_info.user}@{self.remote_info.host}:{remote_file_path}"

        try:
            os.makedirs(os.path.dirname(restore_path), exist_ok=True)
            self.executor.rsync(source, restore_path)
            logger.info("File successfully restored to: %s", restore_path)
            self.console.print(
                f"[green]File successfully restored to: {restore_path}[/green]"
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restore file: %s", e)
            self.console.print(f"[red]Failed to restore file: {e}[/red]")

    def _get_file_versions(self, remote_relative_path: Path) -> List[str]:
        """
        Get available versions of a file from backups.

        Args:
            remote_relative_path (Path): Relative path of the file in the backup

        Returns:
            List[str]: List of available backup dates for the file
        """
        logger.debug("Getting file versions for: %s", remote_relative_path)
        cmd = f"ls -1 {self.remote_info.path}/{HOSTNAME}"
        result = self.executor.run_command(cmd)
        versions = []
        for line in result.stdout.strip().split("\n"):
            if line.startswith("20") and len(line) == 10:  # Basic date format check
                if self._file_exists_in_backup(line, str(remote_relative_path)):
                    versions.append(line)
        logger.debug("Found %d versions", len(versions))
        return sorted(versions, reverse=True)

    def _select_version(self, versions: List[str]) -> str:
        """
        Let the user select a version from the list.

        Args:
            versions (List[str]): List of available versions

        Returns:
            str: Selected version date
        """
        logger.debug("Selecting version from %d available versions", len(versions))
        table = Table(title="Available Versions")
        table.add_column("Date", style="cyan")
        for version in versions:
            table.add_row(version)
        self.console.print(table)

        while True:
            selected = prompt("Enter the date of the version to restore: ")
            if selected in versions:
                logger.debug("Selected version: %s", selected)
                return selected
            logger.warning("Invalid version selected: %s", selected)
            self.console.print(
                "[red]Invalid date. Please choose from the list above.[/red]"
            )

    def _get_file_info(
        self, backup_date: str, remote_relative_path: str
    ) -> Dict[str, str]:
        """
        Get file information from a specific backup.

        Args:
            backup_date (str): Backup date
            remote_relative_path (str): Relative path of the file in the backup

        Returns:
            Dict[str, str]: File information including size and modification time
        """
        logger.debug(
            "Getting file info: date=%s, path=%s", backup_date, remote_relative_path
        )
        cmd = f"stat -c '%s %Y' {self.remote_info.path}/{HOSTNAME}/{backup_date}/{remote_relative_path}"
        result = self.executor.run_command(cmd)
        size, mtime = result.stdout.strip().split()
        mtime_utc = datetime.fromtimestamp(int(mtime), tz=timezone.utc)
        info = {
            "size": self._format_size(int(size)),
            "mtime": mtime_utc.strftime("%Y-%m-%d %H:%M:%S %Z"),
        }
        logger.debug("File info: %s", info)
        return info

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        Format file size in a human-readable format.

        Args:
            size_bytes (int): File size in bytes

        Returns:
            str: Formatted file size
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _show_restore_summary(
        self, backup_date: str, remote_relative_path: str, restore_path: str
    ) -> None:
        """
        Show a summary of the restore operation.

        Args:
            backup_date (str): Backup date
            remote_relative_path (str): Relative path of the file in the backup
            restore_path (str): Path to restore the file to
        """
        logger.debug(
            "Showing restore summary: date=%s, remote_path=%s, restore_path=%s",
            backup_date,
            remote_relative_path,
            restore_path,
        )
        file_info = self._get_file_info(backup_date, remote_relative_path)

        table = Table(title="Restore Summary")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Backup Date", backup_date)
        table.add_row("Source File", remote_relative_path)
        table.add_row("Restore Path", restore_path)
        table.add_row("File Size", file_info["size"])
        table.add_row("Last Modified", file_info["mtime"])

        self.console.print(table)

    def _handle_restore_conflict(self, restore_path: str) -> bool:
        """
        Handle conflicts when the restore path already exists.

        Args:
            restore_path (str): Path to restore the file to

        Returns:
            bool: True if the restore should proceed, False otherwise
        """
        logger.debug("Handling restore conflict for path: %s", restore_path)
        if not os.path.exists(restore_path):
            return True

        self.console.print(
            f"[yellow]Warning: '{restore_path}' already exists.[/yellow]"
        )
        choice = prompt("Choose an action (o)verwrite, (r)ename, (s)kip: ").lower()

        if choice == "o":
            logger.debug("User chose to overwrite existing file")
            return True
        elif choice == "r":
            new_path = prompt("Enter a new file name: ")
            logger.debug("User chose to rename, new path: %s", new_path)
            return self._handle_restore_conflict(
                os.path.join(os.path.dirname(restore_path), new_path)
            )
        elif choice == "s":
            logger.debug("User chose to skip restore")
            return False
        else:
            logger.warning("Invalid choice: %s", choice)
            self.console.print("[red]Invalid choice. Please try again.[/red]")
            return self._handle_restore_conflict(restore_path)

    def _log_restore_operation(
        self, backup_date: str, remote_relative_path: str, restore_path: str
    ) -> None:
        """
        Log the restore operation for auditing purposes.

        Args:
            backup_date (str): Backup date
            remote_relative_path (str): Relative path of the file in the backup
            restore_path (str): Path where the file was restored
        """
        logger.debug(
            "Logging restore operation: date=%s, remote_path=%s, restore_path=%s",
            backup_date,
            remote_relative_path,
            restore_path,
        )
        log_entry = f"{datetime.now().isoformat()} - Restored: {remote_relative_path} from {backup_date} to {restore_path}"
        log_file = self.config.log_file or "aeon_restore.log"

        with open(log_file, "a") as f:
            f.write(log_entry + "\n")

        logger.info("Restore operation logged to %s", log_file)
