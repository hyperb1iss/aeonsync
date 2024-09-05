"""Restore functionality for AeonSync."""

import logging
import json
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from aeonsync.utils import parse_remote, build_ssh_cmd, run_command
from aeonsync.config import HOSTNAME as CONFIG_HOSTNAME, METADATA_FILE_NAME

logger = logging.getLogger(__name__)


def get_hostname():
    return CONFIG_HOSTNAME


def restore_file(
    remote: str,
    backup_date: str,
    file_path: str,
    ssh_key: Optional[str] = None,
    remote_port: Optional[int] = None,
) -> None:
    """Restore a specific file from a backup."""
    logger.info("Restoring file: %s from backup date: %s", file_path, backup_date)
    remote_info = parse_remote(remote, remote_port)
    remote_file_path = (
        f"{remote_info['path']}/{get_hostname()}/{backup_date}/{file_path.lstrip('/')}"
    )
    local_file_path = file_path

    logger.debug("Remote file path: %s", remote_file_path)
    logger.debug("Local file path: %s", local_file_path)

    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    cmd = [
        "rsync",
        "-avz",
        "-e",
        " ".join(ssh_cmd),
        f"{remote_info['user']}@{remote_info['host']}:{remote_file_path}",
        local_file_path,
    ]
    logger.debug("Rsync command: %s", " ".join(cmd))
    run_command(cmd)
    logger.info("File restored successfully")


def list_backups(
    remote: str, ssh_key: Optional[str] = None, remote_port: Optional[int] = None
) -> None:
    """List all available backups with their metadata."""
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend(
        [
            f"{remote_info['user']}@{remote_info['host']}",
            f"for d in {remote_info['path']}/{get_hostname()}/20*-*-*; do "
            f"cat $d/{METADATA_FILE_NAME} 2>/dev/null || "
            f"echo '{{\"date\": \"'$(basename $d)'\", \"error\": \"No metadata found\"}}'; done",
        ]
    )
    result = run_command(ssh_cmd)

    backups = parse_backup_list(result.stdout)
    display_backup_list(backups)


def parse_backup_list(output: str) -> List[Dict]:
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
            pass

    if current_json:
        logger.warning(f"Incomplete JSON data: {current_json}")

    return backups


def format_size(size: str) -> str:
    """Format size in bytes to a human-readable format."""
    try:
        size_bytes = int(size.split()[0].replace(",", ""))
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
    except (ValueError, IndexError, AttributeError):
        return size
    return f"{size_bytes:.2f} PB"


def format_duration(duration: timedelta) -> str:
    """Format timedelta to a human-readable format."""
    seconds = duration.total_seconds()
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.2f}m"
    else:
        return f"{seconds / 3600:.2f}h"


def display_backup_list(backups: List[Dict]) -> None:
    """Display the backup list in an informative format."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if not backups:
        console.print("[yellow]No backups found.[/yellow]")
        return

    table = Table(
        title="AeonSync Backups", show_header=True, header_style="bold magenta"
    )
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Files", justify="right", style="green")
    table.add_column("Size", justify="right", style="blue")
    table.add_column("Duration", justify="right", style="yellow")

    for backup in backups:
        if isinstance(backup, str) or "error" in backup:
            table.add_row(backup.get("date", "Unknown"), "Error", "N/A", "N/A")
        else:
            try:
                start_time = datetime.fromisoformat(backup.get("start_time", ""))
                end_time = datetime.fromisoformat(backup.get("end_time", ""))
                duration = (
                    end_time - start_time if start_time and end_time else timedelta()
                )

                stats = backup.get("stats", {})
                table.add_row(
                    backup.get(
                        "date",
                        start_time.date().isoformat() if start_time else "Unknown",
                    ),
                    stats.get("total_files", "N/A").split()[0],
                    format_size(stats.get("total_file_size", "N/A")),
                    format_duration(duration),
                )
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error processing backup data: {e}")
                table.add_row(backup.get("date", "Unknown"), "Error", "N/A", "N/A")

    console.print(table)

    total_backups = len(backups)
    valid_backups = [b for b in backups if isinstance(b, dict) and "error" not in b]
    latest_backup = max(
        valid_backups,
        key=lambda x: x.get("date", "") or x.get("start_time", ""),
        default=None,
    )
    latest_date = (
        latest_backup.get("date") or latest_backup.get("start_time", "").split("T")[0]
        if latest_backup
        else "N/A"
    )

    console.print(f"[bold]Total backups:[/bold] {total_backups}")
    console.print(f"[bold]Latest backup:[/bold] {latest_date}")
