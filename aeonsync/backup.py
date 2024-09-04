"""Backup functionality for AeonSync."""

import json
import subprocess

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from aeonsync.config import HOSTNAME, METADATA_FILE_NAME, EXCLUSIONS
from aeonsync.utils import parse_remote, build_ssh_cmd, run_command, get_backup_stats

def create_backup(
    remote: str,
    sources: List[str],
    full: bool = False,
    dry_run: bool = False,
    ssh_key: Optional[str] = None,
    remote_port: Optional[int] = None,
    verbose: bool = False
) -> None:
    """Create a full or incremental backup."""
    remote_info = parse_remote(remote, remote_port)
    date = datetime.now().strftime("%Y-%m-%d")
    backup_path = f"{remote_info['path']}/{HOSTNAME}/{date}"
    latest_link = f"{remote_info['path']}/{HOSTNAME}/latest"
    rsync_url = f"{remote_info['user']}@{remote_info['host']}:{backup_path}"

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

    cmd.extend(sources + [rsync_url])

    result = run_command(cmd, capture_output=not verbose)

    if not dry_run:
        update_latest_symlink(remote, backup_path, latest_link, ssh_key, remote_port)
        stats = get_backup_stats(result.stdout)
        save_backup_metadata(remote, backup_path, stats, sources, ssh_key, remote_port)

def create_remote_dir(remote: str, path: str, ssh_key: Optional[str] = None, remote_port: Optional[int] = None) -> None:
    """Create a directory on the remote host."""
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend([f"{remote_info['user']}@{remote_info['host']}", f"mkdir -p {path}"])
    run_command(ssh_cmd)

def update_latest_symlink(remote: str, backup_path: str, latest_link: str, ssh_key: Optional[str] = None, remote_port: Optional[int] = None) -> None:
    """Update the 'latest' symlink to point to the most recent backup."""
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend([f"{remote_info['user']}@{remote_info['host']}", f"ln -snf {backup_path} {latest_link}"])
    run_command(ssh_cmd)

def save_backup_metadata(remote: str, backup_path: str, stats: dict, sources: List[str], ssh_key: Optional[str] = None, remote_port: Optional[int] = None) -> None:
    """Save the backup metadata to a file in the backup directory."""
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
    ssh_cmd.extend([
        f"{remote_info['user']}@{remote_info['host']}",
        f"echo '{metadata_json}' > {backup_path}/{METADATA_FILE_NAME}"
    ])
    run_command(ssh_cmd)

def cleanup_old_backups(remote: str, retention_period: int, ssh_key: Optional[str] = None, remote_port: Optional[int] = None) -> None:
    """Remove backups older than the specified retention period."""
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend([
        f"{remote_info['user']}@{remote_info['host']}",
        f"find {remote_info['path']}/{HOSTNAME} -maxdepth 1 -type d -name '20*-*-*' -mtime +{retention_period} -exec rm -rf {{}} \\;"
    ])
    run_command(ssh_cmd)

def needs_full_backup(remote: str, ssh_key: Optional[str] = None, remote_port: Optional[int] = None) -> bool:
    """Determine if a full backup is needed."""
    remote_info = parse_remote(remote, remote_port)
    latest_link = f"{remote_info['path']}/{HOSTNAME}/latest"
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend([f"{remote_info['user']}@{remote_info['host']}", f"test -e {latest_link} && echo exists"])
    
    try:
        result = run_command(ssh_cmd)
        return "exists" not in result.stdout
    except subprocess.CalledProcessError:
        return True