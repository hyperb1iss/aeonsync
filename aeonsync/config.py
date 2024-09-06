"""Configuration module for AeonSync."""

import socket
from typing import List, Optional, Union, NamedTuple
from pathlib import Path

# Configuration
HOSTNAME = socket.gethostname()
DEFAULT_REMOTE = "bliss@cloudless:/volume1/rsync_backups/aeonsync"
DEFAULT_RETENTION_PERIOD = 7  # Default number of days to keep backups
METADATA_FILE_NAME = "backup_metadata.json"

# Default source directory
DEFAULT_SOURCE_DIRS: List[str] = ["/home/bliss"]

# Exclusions
EXCLUSIONS: List[str] = [
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


class BackupConfig(NamedTuple):
    """Configuration for backup operations."""

    remote: str
    sources: List[Union[str, Path]]
    full: bool = False
    dry_run: bool = False
    ssh_key: Optional[str] = None
    remote_port: Optional[int] = None
    verbose: bool = False
    retention_period: int = DEFAULT_RETENTION_PERIOD
    log_file: Optional[str] = None
