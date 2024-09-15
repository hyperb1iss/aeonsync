# 🌀 AeonSync

<div align="center">

[![CI/CD](https://github.com/hyperb1iss/signalrgb-python/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/hyperb1iss/aeonsync/actions)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

_A powerful and flexible remote backup tool for developers and system administrators_

[Key Features](#-key-features) • [Getting Started](#-getting-started) • [Usage](#-usage) • [Advanced Topics](#-advanced-topics) • [Contributing](#-contributing)

</div>

## ✨ Key Features

AeonSync redefines remote backups with its powerful feature set:

- 🔄 **Flexible Backup Modes**: Daily snapshots or multiple backups per day
- 🔗 **Efficient Incremental Backups**: Leverages rsync's `--link-dest` for optimal storage use
- 🔐 **Secure Remote Syncing**: Rock-solid SSH encryption for data transfer
- ⏱️ **Smart Retention Policies**: Automatic management of your backup history
- 🕰️ **Version Control**: Restore specific file versions with ease
- 🖥️ **Intuitive CLI**: Seamless command-line experience powered by Typer
- 📊 **Rich Metadata**: Comprehensive insights into each backup operation

## 🚀 Getting Started

### Requirements

- Python 3.12+
- SSH access to remote server/NAS
- rsync on local and remote systems

### Installation

```bash
pip install aeonsync
```

## 📘 Usage

Basic command structure:

```bash
# Perform a backup (multiple per day by default)
aeon sync --remote user@host:/path/to/backups

# Restore a file
aeon restore [OPTIONS] FILE [DATE]

# List available backups
aeon list-backups
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
- `--daily`: Create only one backup per day (overrides default behavior)

### Restore Command

The restore command provides functionality for file recovery:

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

## 🔧 Advanced Topics

### ⚙️ Configuration

AeonSync can be configured using command-line options or by modifying the configuration file:

```python
hostname = "myworkstation"
remote_address = "user@nas.local"
remote_path = "/volume1/backups"
remote_port = 22
retention_period = 30
source_dirs = ["/home/user/projects", "/var/www", "/etc"]
exclusions = [".cache", "*/node_modules", "*.tmp", ".venv"]
ssh_key = "/home/user/.ssh/id_rsa"
verbose = False
log_file = "/home/user/.local/share/aeonsync/aeonsync.log"
default_daily_backup = False  # Set to True to allow only one backup per day
```

### 📁 Remote Structure

AeonSync organizes your backups as follows:

```
/volume1/backups/
└── myworkstation/
    ├── latest -> 2024-03-15
    ├── 2024-03-15/
    ├── 2024-03-14/
    ├── 2024-03-13.1/
    ├── 2024-03-13/
    └── ...
```

- Each backup is stored in a date-stamped directory
- Multiple backups per day append a sequence number (e.g., `2024-03-13.1`)
- The `latest` symlink always points to the most recent backup

### 🌟 Use Cases

AeonSync can be used in various scenarios:

#### Home Office Backup

Protect your projects and documents with daily backups to your Synology NAS:

```bash
aeon sync --remote user@synology:/volume1/backups --source /home/user/projects --source /home/user/documents
```

#### Web Server Backup

Safeguard your web applications and databases:

```bash
aeon sync --remote backupuser@remote-server:/backups --source /var/www --source /var/lib/mysql
```

#### Developer Workstation

Keep your code safe with multiple backups per day:

```bash
aeon sync --remote user@dev-server:/backups --source /home/dev/workspace
```

#### Small Business Server

Comprehensive backup solution for critical business data:

```bash
aeon config --hostname business-server --remote-address nas.local --remote-path /volume1/business-backups
aeon sync --source /home/shared --source /var/financial-data --retention 90
```

### 🛠️ Development

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
