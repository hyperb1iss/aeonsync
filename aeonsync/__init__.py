"""Main module for AeonSync."""

from aeonsync.config import BackupConfig
from aeonsync.utils import RemoteInfo, parse_remote, RemoteExecutor


class BaseCommand:
    """Base class for AeonSync commands."""

    def __init__(self, config: BackupConfig):
        """
        Initialize BaseCommand with backup configuration.

        Args:
            config (BackupConfig): Backup configuration
        """
        self.config = config
        self.remote_info: RemoteInfo = parse_remote(
            self.config.remote, self.config.remote_port
        )
        self.executor = RemoteExecutor(
            self.remote_info, self.config.ssh_key, self.config.remote_port
        )
