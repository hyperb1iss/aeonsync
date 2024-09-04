"""Utility functions for AeonSync."""

import re
import subprocess
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def parse_remote(remote: str, port: Optional[int] = None) -> Dict[str, str]:
    """Parse the remote string into its components."""
    match = re.match(r"^(?:(?P<user>[^@]+)@)?(?P<host>[^:]+):(?P<path>.+)$", remote)
    if not match:
        raise ValueError("Invalid remote format. Use [user@]host:path")
    parts = match.groupdict()
    parts["port"] = str(port) if port else None
    return parts

def build_ssh_cmd(ssh_key: Optional[str] = None, remote_port: Optional[int] = None) -> List[str]:
    """Build the SSH command with optional key and port."""
    ssh_cmd = ["ssh"]
    if ssh_key:
        ssh_cmd.extend(["-i", ssh_key])
    if remote_port:
        ssh_cmd.extend(["-p", str(remote_port)])
    return ssh_cmd

def run_command(cmd: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and handle its output."""
    logger.debug("Running command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=capture_output, text=True, check=False)
    if result.returncode != 0:
        logger.error("Command failed with error: %s", result.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result

def get_backup_stats(output: str) -> Dict[str, str]:
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