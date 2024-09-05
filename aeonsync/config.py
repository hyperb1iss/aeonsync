"""Configuration module for AeonSync."""

import socket
from typing import List

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
