# 🌀 AeonSync

<div align="center">

[![CI/CD](https://github.com/hyperb1iss/signalrgb-python/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/hyperb1iss/aeonsync/actions)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

_A powerful and flexible remote backup tool for developers and system administrators_

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#%EF%B8%8F-configuration) • [Development](#%EF%B8%8F-development) • [Contributing](#-contributing) • [License](#-license)

</div>

## ✨ Features

AeonSync offers a comprehensive set of features for efficient and secure remote backups:

- 🔄 **Incremental Backups**: Utilizes rsync's `--link-dest` for efficient storage management
- 🔐 **Secure Remote Syncing**: Implements SSH for secure data transfer
- ⏱️ **Customizable Retention Policies**: Automatically cleans up old backups based on user-defined policies
- 🧪 **Dry-run Mode**: Test backups without making changes to ensure configuration accuracy
- 📊 **Detailed Metadata Tracking**: Maintains comprehensive metadata for each backup operation
- 🖥️ **User-friendly CLI**: Powered by Typer for an intuitive command-line interface
- 🎨 **Rich Console Output**: Enhances readability with colorized and formatted output
- 🔍 **Verbose Mode**: Provides detailed transfer logs for in-depth analysis
- 🗂️ **Multiple Source Support**: Backup multiple directories in a single operation
- 🔁 **Latest Backup Symlink**: Automatically creates a symlink to the most recent backup
- 🕰️ **Version Selection**: Choose specific versions of files for restoration
- 👀 **File Preview**: View file contents before restoration
- 📊 **Diff Display**: Compare different versions of files
- 🔄 **Interactive Restore**: User-friendly guided process for file recovery
- 📜 **Comprehensive Backup Listing**: Detailed information about all available backups
- ⚙️ **Flexible Configuration**: Easily customizable through command-line options or configuration file

## 💻 Installation

### Prerequisites

- Python 3.12 or higher
- SSH access to a remote server
- rsync installed on both local and remote systems

### Using pip

```bash
pip install aeonsync
```

### Using Poetry

```bash
git clone https://github.com/hyperb1iss/aeonsync.git
cd aeonsync
poetry install
```

After installation, the `aeon` command will be available in your system path.

## 🚀 Usage

AeonSync provides an intuitive command-line interface for easy interaction with your backup setup.

### Basic Commands

```bash
# Perform a backup
aeon sync --remote user@host:/path/to/backups

# Restore a file
aeon restore [OPTIONS] FILE [DATE]

# List available backups
aeon list-backups [OPTIONS]

# Show help
aeon --help
```

### Sync Command

The sync command is used to create backups:

```bash
aeon sync [OPTIONS]
```

Options:

- `--remote TEXT`: Remote destination in the format [user@]host:path
- `--source PATH`: Source directories to backup (can be specified multiple times)
- `--retention INTEGER`: Number of days to retain backups
- `--dry-run`: Perform a dry run without making changes
- `--verbose`: Enable verbose output

### Restore Command

The restore command provides powerful functionality for file recovery:

```bash
aeon restore [OPTIONS] [FILE] [DATE]
```

Options:

- `--output PATH`: Output directory for restored file or directory
- `--interactive`: Use fully interactive mode for restore
- `--diff`: Show diff between local and backup versions
- `--preview`: Show a preview of the file before restoring

### List Backups Command

To view available backups:

```bash
aeon list-backups [OPTIONS]
```

This command displays a detailed list of all backups, including dates, file counts, and total sizes.

### Configuration Command

Manage AeonSync configuration:

```bash
aeon config [OPTIONS]
```

Options:

- `--hostname TEXT`: Set the hostname
- `--remote-address TEXT`: Set the remote address
- `--remote-path TEXT`: Set the remote path
- `--remote-port INTEGER`: Set the remote port
- `--retention-period INTEGER`: Set the retention period in days
- `--add-source-dir TEXT`: Add a source directory
- `--remove-source-dir TEXT`: Remove a source directory
- `--add-exclusion TEXT`: Add an exclusion pattern
- `--remove-exclusion TEXT`: Remove an exclusion pattern
- `--ssh-key TEXT`: Set the SSH key path
- `--verbose`: Set verbose mode
- `--log-file TEXT`: Set the log file path
- `--show`: Show current configuration

## ⚙️ Configuration

AeonSync can be configured using command-line options or by modifying the configuration file:

- `hostname`: Hostname for the backup
- `remote_address`: Remote server address
- `remote_path`: Path on the remote server for backups
- `remote_port`: SSH port for the remote server
- `retention_period`: Number of days to keep backups
- `source_dirs`: List of directories to back up
- `exclusions`: Patterns to exclude from backups
- `ssh_key`: Path to SSH key file
- `verbose`: Enable verbose logging
- `log_file`: Path to log file

Example configuration:

```python
hostname = "myhost"
remote_address = "user@example.com"
remote_path = "/backups"
remote_port = 22
retention_period = 30
source_dirs = ["/home/user", "/var/www"]
exclusions = [".cache", "*/node_modules", "*.tmp"]
ssh_key = "/home/user/.ssh/id_rsa"
verbose = False
log_file = "/home/user/.local/share/aeonsync/aeonsync.log"
```

## 🛠️ Development

To set up the development environment:

1. Clone the repository:
   ```bash
   git clone https://github.com/hyperb1iss/aeonsync.git
   cd aeonsync
   ```
2. Install Poetry if you haven't already: `pip install poetry`
3. Install dependencies: `poetry install`
4. Activate the virtual environment: `poetry shell`

To run tests:

```bash
pytest
```

To run linting checks:

```bash
poetry run lint
```

## 👥 Contributing

Contributions to AeonSync are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a new branch: `git checkout -b feature-branch-name`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-branch-name`
5. Submit a pull request

Please ensure your code adheres to the project's style guide (we use Ruff for formatting) and passes all tests.

## 📄 License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

📚 [Documentation](#) • 🐛 [Report Bug](https://github.com/hyperb1iss/aeonsync/issues) • 💡 [Request Feature](https://github.com/hyperb1iss/aeonsync/issues)

Created by [Stefanie Jane 🌠](https://github.com/hyperb1iss)

If you find this project useful, [buy me a Monster Ultra Violet!](https://ko-fi.com/hyperb1iss) ⚡️

</div>
