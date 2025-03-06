"""Utility functions and classes for AeonSync."""

import logging
import re
import subprocess
from subprocess import CompletedProcess
from typing import NamedTuple

logger = logging.getLogger(__name__)


class RemoteInfo(NamedTuple):
    """Information about the remote connection."""

    user: str | None
    host: str
    path: str
    port: int | None


def parse_remote(remote: str, port: int | None = None) -> RemoteInfo:
    """
    Parse the remote string into its components.

    Args:
        remote (str): Remote string in the format [user@]host:path
        port (Optional[int]): SSH port number

    Returns:
        RemoteInfo: Parsed remote information

    Raises:
        ValueError: If the remote string format is invalid
    """
    logger.debug("Parsing remote string: %s, port: %s", remote, port)
    match = re.match(r"^(?:(?P<user>[^@]+)@)?(?P<host>[^:]+):(?P<path>.+)$", remote)
    if not match:
        logger.error("Invalid remote format: %s", remote)
        raise ValueError("Invalid remote format. Use [user@]host:path")
    parts = match.groupdict()
    return RemoteInfo(user=parts["user"], host=parts["host"], path=parts["path"], port=port)


class RemoteExecutor:
    """Handles remote command execution for non-rsync operations."""

    def __init__(
        self,
        remote_info: RemoteInfo,
        ssh_key: str | None = None,
        remote_port: int | None = None,
    ):
        """
        Initialize RemoteExecutor with remote connection details.

        Args:
            remote_info (RemoteInfo): Remote server information
            ssh_key (Optional[str]): Path to SSH key file
            remote_port (Optional[int]): SSH port number
        """
        self.remote_info = remote_info
        self.ssh_key = ssh_key
        self.remote_port = remote_port or remote_info.port

    def run_command(self, command: str) -> CompletedProcess[str]:
        """
        Run a command on the remote server.

        Args:
            command (str): Command to run

        Returns:
            CompletedProcess: Process result
        """
        ssh_cmd = self._build_ssh_cmd()
        full_cmd = [*ssh_cmd, f"{self.remote_info.user}@{self.remote_info.host}", command]
        logger.debug("Running command: %s", " ".join(full_cmd))
        return subprocess.run(full_cmd, capture_output=True, text=True, check=True)

    def rsync(self, source: str, destination: str, extra_args: list[str] | None = None) -> CompletedProcess[str]:
        """
        Run rsync to copy files between local and remote.

        Args:
            source (str): Source path (local or remote)
            destination (str): Destination path (local or remote)
            extra_args (Optional[List[str]]): Additional rsync arguments

        Returns:
            CompletedProcess: Result of the rsync execution

        Raises:
            subprocess.CalledProcessError: If the rsync execution fails
        """
        rsync_cmd = ["rsync", "-avz"]
        if extra_args:
            rsync_cmd.extend(extra_args)

        ssh_opts = self._build_ssh_options()
        rsync_cmd.extend(["-e", f"ssh {ssh_opts}"])

        rsync_cmd.extend([source, destination])

        logger.debug("Running rsync command: %s", " ".join(rsync_cmd))
        return subprocess.run(rsync_cmd, capture_output=True, text=True, check=True)

    def _build_ssh_cmd(self) -> list[str]:
        """
        Build the SSH command with optional key and port.

        Returns:
            List[str]: SSH command components
        """
        ssh_cmd = ["ssh"]
        if self.ssh_key:
            ssh_cmd.extend(["-i", self.ssh_key])
        if self.remote_port:
            ssh_cmd.extend(["-p", str(self.remote_port)])
        return ssh_cmd

    def _build_ssh_options(self) -> str:
        """
        Build SSH options string.

        Returns:
            str: SSH options string
        """
        opts = []
        if self.ssh_key:
            opts.append(f"-i {self.ssh_key}")
        if self.remote_port:
            opts.append(f"-p {self.remote_port}")
        return " ".join(opts)


def get_backup_stats(output: str) -> dict[str, str]:
    """
    Extract relevant statistics from rsync output.

    Args:
        output (str): Output from rsync command

    Returns:
        Dict[str, str]: Extracted statistics
    """
    logger.debug("Extracting backup stats from rsync output")
    stats = {}
    summary_started = False
    for line in output.split("\n"):
        if line.startswith("Number of files:"):
            summary_started = True
        if summary_started:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                stats[key] = value.strip()
    logger.debug("Extracted backup stats: %s", stats)
    return stats
