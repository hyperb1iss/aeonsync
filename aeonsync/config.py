"""Configuration module for AeonSync."""

import socket
from typing import List, NamedTuple, Optional, Union, Dict, Any
from pathlib import Path

import toml
from appdirs import user_config_dir


class ConfigManager:
    """Manages AeonSync configuration."""

    APP_NAME = "aeonsync"
    CONFIG_FILE_NAME = "config.toml"

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize ConfigManager with the specified configuration directory.

        Args:
            config_dir (Optional[Path], optional): Path to the configuration directory.
                Defaults to the user config directory.
        """
        self.config_dir = config_dir or Path(user_config_dir(self.APP_NAME))
        self.config_file_path = self.config_dir / self.CONFIG_FILE_NAME
        self.config: Dict[str, Any] = {}  # Initialize config as an empty dict
        self.load_config()  # Load the configuration

    @property
    def default_config(self) -> Dict[str, Any]:
        """Provide default configuration values.

        Returns:
            Dict[str, Any]: Default configuration dictionary.
        """
        return {
            "hostname": socket.gethostname(),
            "remote_address": "user@example.com",
            "remote_path": "/path/to/backups",
            "remote_port": 22,
            "retention_period": 7,
            "source_dirs": [str(Path.home())],
            "exclusions": [
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
            ],
            "ssh_key": str(Path.home() / ".ssh" / "id_rsa"),
            "verbose": False,
            "log_file": str(
                Path.home() / ".local" / "share" / self.APP_NAME / "aeonsync.log"
            ),
            "default_daily_backup": False,
        }

    def load_config(self) -> None:
        """Load the configuration from file or create with default values if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if self.config_file_path.exists():
            with open(self.config_file_path, "r", encoding="utf-8") as config_file:
                self.config = toml.load(config_file)
        else:
            # If the config file doesn't exist, use default values
            self.config = self.default_config.copy()
            self.save_config(self.config)

    def save_config(self, new_config: Dict[str, Any]) -> None:
        """
        Save the configuration to file.

        Args:
            new_config (Dict[str, Any]): The new configuration dictionary to save.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file_path, "w", encoding="utf-8") as config_file:
            toml.dump(new_config, config_file)
        self.config = new_config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key (str): The configuration key.
            default (Any, optional): The default value if key is not found. Defaults to None.

        Returns:
            Any: The configuration value.
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value and save the configuration.

        Args:
            key (str): The configuration key.
            value (Any): The value to set.
        """
        self.config[key] = value
        self.save_config(self.config)

    def add_to_list(self, key: str, value: Any) -> None:
        """
        Add a value to a list configuration item.

        Args:
            key (str): The configuration key associated with a list.
            value (Any): The value to add to the list.
        """
        if key not in self.config or not isinstance(self.config[key], list):
            self.config[key] = []
        if value not in self.config[key]:
            self.config[key].append(value)
            self.save_config(self.config)

    def remove_from_list(self, key: str, value: Any) -> None:
        """
        Remove a value from a list configuration item.

        Args:
            key (str): The configuration key associated with a list.
            value (Any): The value to remove from the list.
        """
        if key in self.config and isinstance(self.config[key], list):
            if value in self.config[key]:
                self.config[key].remove(value)
                self.save_config(self.config)


config_manager = ConfigManager()

# Expose configuration values as module-level variables
HOSTNAME = config_manager.get("hostname")
DEFAULT_REMOTE = (
    f"{config_manager.get('remote_address')}:{config_manager.get('remote_path')}"
)
DEFAULT_RETENTION_PERIOD = config_manager.get("retention_period")
METADATA_FILE_NAME = "backup_metadata.json"
DEFAULT_SOURCE_DIRS: List[str] = config_manager.get("source_dirs")
EXCLUSIONS: List[str] = config_manager.get("exclusions")
DEFAULT_SSH_KEY = config_manager.get("ssh_key")
DEFAULT_REMOTE_PORT = config_manager.get("remote_port")
VERBOSE = config_manager.get("verbose")
LOG_FILE = config_manager.get("log_file")


class BackupConfig(NamedTuple):
    """Configuration for backup operations."""

    remote: str
    sources: List[Union[str, Path]]
    full: bool = False
    dry_run: bool = False
    ssh_key: Optional[str] = DEFAULT_SSH_KEY
    remote_port: Optional[int] = DEFAULT_REMOTE_PORT
    verbose: bool = VERBOSE
    retention_period: int = DEFAULT_RETENTION_PERIOD
    log_file: Optional[str] = LOG_FILE
    daily: bool = False
