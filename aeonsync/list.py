"""List backups functionality for AeonSync."""
import json
import logging
from typing import List, Dict, Optional
import re

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
            f"for d in {self.remote_info.path}/{HOSTNAME}/20*-*-*{{'',.*}}; do "
            f'echo "BACKUP_START $(basename $d)"; '
            f"cat $d/{METADATA_FILE_NAME} 2>/dev/null || "
            f'echo \'{{"error": "No metadata found"}}\'; '
            f'echo "BACKUP_END"; done'
        )
        result = self.executor.run_command(cmd)
        return self._parse_backup_list(result.stdout)

    @staticmethod
    def _parse_backup_list(output: str) -> List[Dict]:
        """Parse the JSON output from the backup list command."""
        backups = []
        current_backup = None
        current_json = ""

        for line in output.strip().split("\n"):
            if line.startswith("BACKUP_START"):
                current_backup = line.split()[1]
                current_json = ""
            elif line == "BACKUP_END":
                if current_backup and current_json:
                    try:
                        backup_data = json.loads(current_json)
                        backup_data["date"] = current_backup
                        backups.append(backup_data)
                    except json.JSONDecodeError:
                        logger.warning(
                            "Failed to parse JSON data for backup %s", current_backup
                        )
                current_backup = None
                current_json = ""
            else:
                current_json += line

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
        table.add_column("Backup", style="cyan", no_wrap=True)
        table.add_column("Hostname", style="magenta")
        table.add_column("Sources", style="green")
        table.add_column("Files", justify="right", style="green")
        table.add_column("Total Size", justify="right", style="blue")
        table.add_column("Changed", justify="right", style="yellow")

        sorted_backups = sorted(backups, key=lambda x: x.get("date", ""), reverse=True)

        for backup in sorted_backups:
            self._add_backup_to_table(backup, table)

        console.print(table)
        self._print_backup_summary(sorted_backups, console)

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
                stats = backup.get("stats", {})
                hostname = backup.get("hostname", "Unknown")
                sources = ", ".join(backup.get("sources", []))
                total_size = self._get_total_size(backup)
                changed_size = self._get_changed_size(stats)

                table.add_row(
                    backup.get("date", "Unknown"),
                    hostname,
                    sources,
                    self._format_file_count(stats.get("number_of_files", "N/A")),
                    self._format_size(total_size),
                    self._format_size(changed_size)
                    if changed_size is not None
                    else "N/A",
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
        latest_backup = valid_backups[0] if valid_backups else None
        latest_date = latest_backup.get("date", "N/A") if latest_backup else "N/A"

        console.print(f"[bold]Total backups:[/bold] {total_backups}")
        console.print(f"[bold]Latest backup:[/bold] {latest_date}")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size in bytes to a human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes = int(size_bytes / 1024.0)
        return f"{size_bytes:.2f} PB"

    @staticmethod
    def _format_file_count(file_count: str) -> str:
        """Format the file count, extracting only the total number."""
        match = re.search(r"\d+(?:,\d+)*", file_count)
        if match:
            return match.group(0)
        return file_count

    @staticmethod
    def _get_total_size(backup: Dict) -> int:
        """Get the total file size from the backup stats."""
        stats = backup.get("stats", {})
        size_str = stats.get("total_file_size", "0 bytes")
        match = re.search(r"(\d+(?:,\d+)*)", size_str)
        if match:
            return int(match.group(1).replace(",", ""))
        return 0

    @staticmethod
    def _get_changed_size(stats: Dict) -> Optional[int]:
        """Get the changed size from the backup stats using literal_data."""
        literal_data = stats.get("literal_data", "0 bytes")
        match = re.search(r"(\d+(?:,\d+)*)", literal_data)
        if match:
            return int(match.group(1).replace(",", ""))
        return None
