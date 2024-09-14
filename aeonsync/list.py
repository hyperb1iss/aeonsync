"""List backups functionality for AeonSync."""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict

from rich.console import Console
from rich.table import Table

from aeonsync import BaseCommand
from aeonsync.config import HOSTNAME, METADATA_FILE_NAME, BackupConfig

logger = logging.getLogger(__name__)


class ListBackups(BaseCommand):
    """Handles listing of backups for AeonSync."""

    def __init__(self, config: BackupConfig):
        """
        Initialize ListBackups with backup configuration.

        Args:
            config (BackupConfig): Backup configuration
        """
        super().__init__(config)

    def list(self) -> None:
        """List all available backups with their metadata."""
        backups = self._fetch_backup_list()
        self._display_backup_list(backups)

    def _fetch_backup_list(self) -> List[Dict]:
        """Fetch the list of backups from the remote server."""
        cmd = (
            f"for d in {self.remote_info.path}/{HOSTNAME}/20*-*-*; do "
            f"cat $d/{METADATA_FILE_NAME} 2>/dev/null || "
            f'echo \'{{"date": "\'$(basename $d)\'", "error": "No metadata found"}}\'; done'
        )
        result = self.executor.run_command(cmd)
        return self._parse_backup_list(result.stdout)

    @staticmethod
    def _parse_backup_list(output: str) -> List[Dict]:
        """Parse the JSON output from the backup list command."""
        backups = []
        current_json = ""
        for line in output.strip().split("\n"):
            current_json += line
            try:
                backup = json.loads(current_json)
                backups.append(backup)
                current_json = ""
            except json.JSONDecodeError:
                current_json += "\n"  # Handle multi-line JSON objects

        if current_json.strip():
            logger.warning("Incomplete JSON data: %s", current_json)

        return backups

    def _display_backup_list(self, backups: List[Dict]) -> None:
        """Display the backup list with metadata in an informative format."""
        console = Console()

        if not backups:
            console.print("[yellow]No backups found.[/yellow]")
            return

        table = Table(
            title="AeonSync Backups", show_header=True, header_style="bold magenta"
        )
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("Hostname", style="magenta")
        table.add_column("Sources", style="green")
        table.add_column("Files", justify="right", style="green")
        table.add_column("Size", justify="right", style="blue")
        table.add_column("Duration", justify="right", style="yellow")

        for backup in backups:
            self._add_backup_to_table(backup, table)

        console.print(table)
        self._print_backup_summary(backups, console)

    def _add_backup_to_table(self, backup: Dict, table: Table) -> None:
        """Add a single backup entry to the display table."""
        if "error" in backup:
            table.add_row(
                backup.get("date", "Unknown"),
                "Error",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
            )
        else:
            try:
                start_time = datetime.fromisoformat(backup.get("start_time", ""))
                duration = timedelta(seconds=float(backup.get("duration", 0)))

                stats = backup.get("stats", {})
                hostname = backup.get("hostname", "Unknown")
                sources = ", ".join(backup.get("sources", []))
                table.add_row(
                    backup.get("date", start_time.date().isoformat()),
                    hostname,
                    sources,
                    stats.get("number_of_files", "N/A"),
                    self._format_size(stats.get("total_file_size", "N/A")),
                    self._format_duration(duration),
                )
            except (ValueError, AttributeError, TypeError) as e:
                logger.warning("Error processing backup data: %s", e)
                table.add_row(
                    backup.get("date", "Unknown"),
                    "Error",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                )

    def _print_backup_summary(self, backups: List[Dict], console: Console) -> None:
        """Print a summary of the backup list."""
        total_backups = len(backups)
        valid_backups = [b for b in backups if "error" not in b]
        latest_backup = max(
            valid_backups,
            key=lambda x: x.get("date", "") or x.get("start_time", ""),
            default=None,
        )
        latest_date = (
            latest_backup.get("date")
            or latest_backup.get("start_time", "").split("T")[0]
            if latest_backup
            else "N/A"
        )

        console.print(f"[bold]Total backups:[/bold] {total_backups}")
        console.print(f"[bold]Latest backup:[/bold] {latest_date}")

    @staticmethod
    def _format_size(size: str) -> str:
        """Format size in bytes to a human-readable format."""
        try:
            size_bytes = float(size.replace(",", "").split()[0])
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
        except (ValueError, IndexError, AttributeError):
            return size
        return f"{size_bytes:.2f} PB"

    @staticmethod
    def _format_duration(duration: timedelta) -> str:
        """Format timedelta to a human-readable format."""
        total_seconds = duration.total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        if minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        return f"{seconds:.2f}s"
