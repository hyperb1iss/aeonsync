"""Backup functionality for AeonSync."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, Dict
import subprocess

from aeonsync.config import HOSTNAME, METADATA_FILE_NAME, EXCLUSIONS
from aeonsync.utils import parse_remote, build_ssh_cmd, run_command, get_backup_stats

logger = logging.getLogger(__name__)


def create_backup(
    remote: str,
    sources: List[Union[str, Path]],
    full: bool = False,
    dry_run: bool = False,
    ssh_key: Optional[str] = None,
    remote_port: Optional[int] = None,
    verbose: bool = False,
) -> None:
    """Create a full or incremental backup."""
    logger.info("Creating %s backup", "full" if full else "incremental")
    remote_info = parse_remote(remote, remote_port)
    date = datetime.now().strftime("%Y-%m-%d")
    backup_path = f"{remote_info['path']}/{HOSTNAME}/{date}"
    latest_link = f"{remote_info['path']}/{HOSTNAME}/latest"
    rsync_url = f"{remote_info['user']}@{remote_info['host']}:{backup_path}"

    logger.debug("Backup path: %s", backup_path)
    logger.debug("Latest link: %s", latest_link)
    logger.debug("Rsync URL: %s", rsync_url)

    create_remote_dir(remote, backup_path, ssh_key, remote_port)

    cmd = ["rsync", "-avz", "--delete", "--stats"]
    for exclusion in EXCLUSIONS:
        cmd.extend(["--exclude", exclusion])
    if not full:
        cmd.extend(["--link-dest", f"{remote}:{latest_link}"])
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--progress")

    if ssh_key or remote_port:
        ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
        cmd.extend(["-e", " ".join(ssh_cmd)])

    # Convert all sources to strings
    str_sources = [str(s) for s in sources]
    cmd.extend(str_sources + [rsync_url])

    logger.debug("Rsync command: %s", " ".join(map(str, cmd)))

    # Use Popen to capture output while still displaying it
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    output = []
    for line in iter(process.stdout.readline, ""):
        print(line, end="")  # Print the line in real-time
        output.append(line)  # Store the line for later processing

    process.stdout.close()
    return_code = process.wait()

    if return_code != 0:
        logger.error(f"Rsync command failed with return code {return_code}")
        raise subprocess.CalledProcessError(return_code, cmd)

    # Join the output lines and process stats
    full_output = "".join(output)
    stats = get_backup_stats(full_output)

    if not dry_run:
        update_latest_symlink(remote, backup_path, latest_link, ssh_key, remote_port)
        save_backup_metadata(
            remote, backup_path, stats, str_sources, ssh_key, remote_port
        )

    logger.info("Backup created successfully")


def create_remote_dir(
    remote: str,
    path: str,
    ssh_key: Optional[str] = None,
    remote_port: Optional[int] = None,
) -> None:
    """Create a directory on the remote host."""
    logger.debug("Creating remote directory: %s", path)
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend([f"{remote_info['user']}@{remote_info['host']}", f"mkdir -p {path}"])
    run_command(ssh_cmd)
    logger.debug("Remote directory created successfully")


def update_latest_symlink(
    remote: str,
    backup_path: str,
    latest_link: str,
    ssh_key: Optional[str] = None,
    remote_port: Optional[int] = None,
) -> None:
    """Update the 'latest' symlink to point to the most recent backup."""
    logger.debug("Updating latest symlink to: %s", backup_path)
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend(
        [
            f"{remote_info['user']}@{remote_info['host']}",
            f"ln -snf {backup_path} {latest_link}",
        ]
    )
    run_command(ssh_cmd)
    logger.debug("Latest symlink updated successfully")


def save_backup_metadata(
    remote: str,
    backup_path: str,
    stats: Dict[str, str],
    sources: List[str],
    ssh_key: Optional[str] = None,
    remote_port: Optional[int] = None,
) -> None:
    """Save the backup metadata to a file in the backup directory."""
    logger.debug("Saving backup metadata")
    metadata = {
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "hostname": HOSTNAME,
        "sources": sources,
        "stats": stats,
    }
    metadata_json = json.dumps(metadata, indent=2)
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)

    # Escape single quotes in the JSON string
    escaped_json = metadata_json.replace("'", "'\\''")

    cmd = ssh_cmd + [
        f"{remote_info['user']}@{remote_info['host']}",
        f"echo '{escaped_json}' > {backup_path}/{METADATA_FILE_NAME}",
    ]

    logger.debug(f"Metadata command: {' '.join(cmd)}")
    try:
        run_command(cmd)
        logger.debug("Backup metadata saved successfully")
    except Exception as e:
        logger.error(f"Failed to save backup metadata: {str(e)}")


def cleanup_old_backups(
    remote: str,
    retention_period: int,
    ssh_key: Optional[str] = None,
    remote_port: Optional[int] = None,
) -> None:
    """Remove backups older than the specified retention period."""
    logger.info("Cleaning up old backups (retention period: %d days)", retention_period)
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend(
        [
            f"{remote_info['user']}@{remote_info['host']}",
            f"find {remote_info['path']}/{HOSTNAME} -maxdepth 1 -type d -name '20*-*-*' -mtime +{retention_period} -exec rm -rf {{}} \\;",
        ]
    )
    run_command(ssh_cmd)
    logger.info("Old backups cleaned up successfully")


def needs_full_backup(
    remote: str, ssh_key: Optional[str] = None, remote_port: Optional[int] = None
) -> bool:
    """Determine if a full backup is needed."""
    logger.debug("Checking if full backup is needed")
    remote_info = parse_remote(remote, remote_port)
    latest_link = f"{remote_info['path']}/{HOSTNAME}/latest"
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend(
        [
            f"{remote_info['user']}@{remote_info['host']}",
            f"test -e {latest_link} && echo exists",
        ]
    )

    try:
        result = run_command(ssh_cmd)
        needs_full = "exists" not in result.stdout
        logger.info("Full backup needed: %s", needs_full)
        return needs_full
    except subprocess.CalledProcessError:
        logger.info("Full backup needed: True (error checking latest link)")
        return True
