#!/usr/bin/env python3
"""
AeonSync: Flexible Remote Backup Tool

This script provides functionality to backup specified directories to a remote server,
list available backups, and restore files from backups.
"""

import sys
import subprocess
import argparse
from datetime import datetime, timedelta
import socket
import json
import re
import logging

# Configuration
HOSTNAME = socket.gethostname()
DEFAULT_REMOTE = "bliss@cloudless:/volume1/rsync_backups/aeonsync"
DEFAULT_RETENTION_PERIOD = 7  # Default number of days to keep backups
METADATA_FILE_NAME = "backup_metadata.json"

# Default source directory
DEFAULT_SOURCE_DIRS = ["/home/bliss"]

# Exclusions
EXCLUSIONS = [
    ".cache",
    "*/caches/*",
    ".local/share/Trash",
    "*/node_modules",
    "*/.venv",
    "*/venv",
    "*/__pycache__",
    "*/.gradle",
    "*/build",
    "*/target",
    "*/.cargo",
    "*/dist",
    "*/.npm",
    "*/.yarn",
    "*/.pub-cache",
]

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_remote(remote, port=None):
    """Parse the remote string into its components."""
    match = re.match(r"^(?:(?P<user>[^@]+)@)?(?P<host>[^:]+):(?P<path>.+)$", remote)
    if not match:
        raise ValueError("Invalid remote format. Use [user@]host:path")
    parts = match.groupdict()
    parts["port"] = port
    return parts


def build_ssh_cmd(ssh_key=None, remote_port=None):
    """Build the SSH command with optional key and port."""
    ssh_cmd = ["ssh"]
    if ssh_key:
        ssh_cmd.extend(["-i", ssh_key])
    if remote_port:
        ssh_cmd.extend(["-p", remote_port])
    return ssh_cmd


def run_rsync(
    sources,
    dest,
    link_dest=None,
    dry_run=False,
    ssh_key=None,
    remote_port=None,
    verbose=False,
):
    """Run rsync command with specified parameters."""
    cmd = ["rsync", "-avz", "--delete", "--stats"]
    for exclusion in EXCLUSIONS:
        cmd.extend(["--exclude", exclusion])
    if link_dest:
        cmd.extend(["--link-dest", link_dest])
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--progress")  # Adding verbose flag for detailed output

    if ssh_key or remote_port:
        ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
        cmd.extend(["-e", " ".join(ssh_cmd)])

    cmd.extend(sources + [dest])

    logger.debug(f"Running command: {' '.join(cmd)}")

    if verbose:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = process.poll()
        if rc != 0:
            logger.error(f"Rsync failed with return code: {rc}")
            sys.exit(rc)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Rsync failed with error: {result.stderr}")
            sys.exit(result.returncode)
        return result.stdout


def create_remote_dir(remote, path, ssh_key=None, remote_port=None):
    """Create a directory on the remote host."""
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.append(f"{remote_info['user']}@{remote_info['host']}")
    ssh_cmd.append(f"mkdir -p {path}")
    logger.debug(f"Running command: {' '.join(ssh_cmd)}")
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Failed to create remote directory: {result.stderr}")
        sys.exit(result.returncode)


def get_backup_stats(output):
    """Extract relevant statistics from rsync output."""
    stats = {}
    for line in output.split("\n"):
        if line.startswith("Total transferred file size:"):
            stats["total_size"] = line.split(":")[1].strip()
        elif line.startswith("Number of files transferred:"):
            stats["files_transferred"] = line.split(":")[1].strip()
        elif line.startswith("Total file size:"):
            stats["total_file_size"] = line.split(":")[1].strip()
        elif line.startswith("Total number of files:"):
            stats["total_files"] = line.split(":")[1].strip()
    return stats


def save_backup_metadata(
    remote, backup_path, stats, sources, ssh_key=None, remote_port=None
):
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
    ssh_cmd.append(f"{remote_info['user']}@{remote_info['host']}")
    ssh_cmd.append(f"echo '{metadata_json}' > {backup_path}/{METADATA_FILE_NAME}")
    logger.debug(f"Running command: {' '.join(ssh_cmd)}")
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Failed to save backup metadata: {result.stderr}")
        sys.exit(result.returncode)


def create_backup(
    remote,
    sources,
    full=False,
    dry_run=False,
    ssh_key=None,
    remote_port=None,
    verbose=False,
):
    """Create a full or incremental backup."""
    remote_info = parse_remote(remote, remote_port)
    date = datetime.now().strftime("%Y-%m-%d")
    backup_path = f"{remote_info['path']}/{HOSTNAME}/{date}"
    latest_link = f"{remote_info['path']}/{HOSTNAME}/latest"
    rsync_url = f"{remote_info['user']}@{remote_info['host']}:{backup_path}"

    create_remote_dir(remote, backup_path, ssh_key, remote_port)

    logger.debug(
        f"Backup path: {backup_path} remote: {rsync_url} remote info: {remote_info}"
    )
    if full:
        logger.info("Creating full backup...")
        output = run_rsync(
            sources,
            f"{rsync_url}",
            dry_run=dry_run,
            ssh_key=ssh_key,
            remote_port=remote_port,
            verbose=verbose,
        )
    else:
        logger.info("Creating incremental backup...")
        output = run_rsync(
            sources,
            f"{rsync_url}",
            f"{remote}:{latest_link}",
            dry_run=dry_run,
            ssh_key=ssh_key,
            remote_port=remote_port,
            verbose=verbose,
        )

    logger.debug(output)

    if not dry_run:
        # Update the "latest" symlink
        ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
        ssh_cmd.append(f"{remote_info['user']}@{remote_info['host']}")
        ssh_cmd.append(f"ln -snf {backup_path} {latest_link}")
        logger.debug(f"Running command: {' '.join(ssh_cmd)}")
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to update latest symlink: {result.stderr}")
            sys.exit(result.returncode)

        # Save backup metadata
        stats = get_backup_stats(output)
        save_backup_metadata(remote, backup_path, stats, sources, ssh_key, remote_port)

    logger.info(f"Backup {'simulation' if dry_run else 'completion'}: {backup_path}")


def needs_full_backup(remote, ssh_key=None, remote_port=None):
    """Determine if a full backup is needed."""
    remote_info = parse_remote(remote, remote_port)
    latest_link = f"{remote_info['path']}/{HOSTNAME}/latest"
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.append(f"{remote_info['user']}@{remote_info['host']}")
    ssh_cmd.append(f"test -e {latest_link} && echo exists")
    logger.debug(f"Running command: {' '.join(ssh_cmd)}")
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, check=False)
    if "exists" not in result.stdout:
        return True

    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.append(f"{remote_info['user']}@{remote_info['host']}")
    ssh_cmd.append(f"stat -c %Y {latest_link}")
    logger.debug(f"Running command: {' '.join(ssh_cmd)}")
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, check=False)
    last_backup_time = datetime.fromtimestamp(int(result.stdout.strip()))
    return datetime.now() - last_backup_time > timedelta(days=DEFAULT_RETENTION_PERIOD)


def cleanup_old_backups(remote, retention_period, ssh_key=None, remote_port=None):
    """Remove backups older than the specified retention period."""
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.append(f"{remote_info['user']}@{remote_info['host']}")
    ssh_cmd.append(
        f"find {remote_info['path']}/{HOSTNAME} -maxdepth 1 -type d -name '20*-*-*' -mtime +{retention_period} -exec rm -rf {{}} \\;"
    )
    logger.debug(f"Running command: {' '.join(ssh_cmd)}")
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Failed to clean up old backups: {result.stderr}")
        sys.exit(result.returncode)
    logger.info(f"Backups older than {retention_period} days cleaned up.")


def list_backups(remote, ssh_key=None, remote_port=None):
    """List all available backups with their metadata."""
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.append(f"{remote_info['user']}@{remote_info['host']}")
    ssh_cmd.append(
        f"for d in {remote_info['path']}/{HOSTNAME}/20*-*-*; do cat $d/{METADATA_FILE_NAME} 2>/dev/null || echo '{{\"date\": \"'$(basename $d)'\", \"error\": \"No metadata found\"}}'; done"
    )
    logger.debug(f"Running command: {' '.join(ssh_cmd)}")
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0 and result.stdout.strip():
        logger.info("Available backups:")
        for line in result.stdout.strip().split("\n"):
            try:
                metadata = json.loads(line)
                date = (
                    metadata.get("date") or metadata.get("end_time", "").split("T")[0]
                )
                size = metadata.get("stats", {}).get("total_size", "Unknown")
                sources = ", ".join(metadata.get("sources", ["Unknown"]))
                logger.info(f"{date}: Size: {size}, Sources: {sources}")
            except json.JSONDecodeError:
                logger.error(f"Error parsing backup metadata: {line}")
    else:
        logger.info("No backups available or unable to retrieve backup information.")


def restore_file(remote, backup_date, file_path, ssh_key=None, remote_port=None):
    """Restore a specific file from a backup."""
    remote_info = parse_remote(remote, remote_port)
    remote_file_path = (
        f"{remote_info['path']}/{HOSTNAME}/{backup_date}/{file_path.lstrip('/')}"
    )
    local_file_path = file_path

    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    cmd = [
        "rsync",
        "-avz",
        "-e",
        " ".join(ssh_cmd),
        f"{remote_info['user']}@{remote_info['host']}:{remote_file_path}",
        local_file_path,
    ]
    logger.debug(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        logger.info(f"File {file_path} restored from {backup_date} backup.")
    else:
        logger.error(f"Failed to restore {file_path} from {backup_date} backup.")
        logger.error(result.stderr)


def main():
    """Main function to handle command-line arguments and execute actions."""
    parser = argparse.ArgumentParser(
        prog="aeon", description="AeonSync: Flexible Remote Backup Tool"
    )
    parser.add_argument(
        "action",
        choices=["sync", "list", "restore"],
        help="Action to perform (sync: create backup, list: show backups, restore: restore file)",
    )
    parser.add_argument("--file", help="File to restore (for restore action)")
    parser.add_argument(
        "--date", help="Backup date to restore from (for restore action)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=DEFAULT_SOURCE_DIRS,
        help="Source directories to backup (default: /home)",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=DEFAULT_RETENTION_PERIOD,
        help=f"Number of days to retain backups (default: {DEFAULT_RETENTION_PERIOD})",
    )
    parser.add_argument("--ssh-key", help="Path to SSH private key for authentication")
    parser.add_argument(
        "--remote",
        default=DEFAULT_REMOTE,
        help="Remote destination in the format [user@]host:path",
    )
    parser.add_argument("--port", type=int, default=None, help="Remote SSH port")
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output for rsync"
    )

    args = parser.parse_args()

    try:
        if args.action == "sync":
            full_backup = needs_full_backup(args.remote, args.ssh_key, args.port)
            create_backup(
                args.remote,
                args.sources,
                full_backup,
                args.dry_run,
                args.ssh_key,
                args.port,
                args.verbose,
            )
            if not args.dry_run:
                cleanup_old_backups(
                    args.remote, args.retention, args.ssh_key, args.port
                )
            logger.info("AeonSync completed.")
        elif args.action == "list":
            list_backups(args.remote, args.ssh_key, args.port)
        elif args.action == "restore":
            if not args.file or not args.date:
                logger.error("Both --file and --date are required for restore action.")
                sys.exit(1)
            restore_file(args.remote, args.date, args.file, args.ssh_key, args.port)
    except ValueError as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
