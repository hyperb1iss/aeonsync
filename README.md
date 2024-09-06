# 🌀 AeonSync

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*A powerful and flexible remote backup tool for developers and system administrators*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#%EF%B8%8F-configuration) • [Development](#%EF%B8%8F-development) • [Contributing](#-contributing) • [License](#-license)

</div>

## ✨ Features
<a name="features"></a>

- 🔄 Incremental backups using rsync's `--link-dest` for efficient storage
- 🔐 Secure remote syncing via SSH
- ⏱️ Customizable retention policies for automatic cleanup
- 🧪 Dry-run mode for testing backups without making changes
- 📊 Detailed metadata tracking for each backup
- 🖥️ User-friendly command-line interface powered by Typer
- 🎨 Rich console output for improved readability
- 🔍 Verbose mode for detailed transfer logs
- 🗂️ Multiple source directory support
- 🔁 Automatic latest backup symlink creation
- 🕰️ Version selection for file restores
- 👀 File preview before restoration
- 📊 Diff display to compare file versions
- 🔄 Interactive restore mode for user-friendly file recovery
- 📜 Comprehensive backup listing with detailed information

## 💻 Installation
<a name="installation"></a>

You can install AeonSync using either pip or Poetry:

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

### Prerequisites

- Python 3.12 or higher
- SSH access to a remote server
- rsync installed on both local and remote systems

## 🚀 Usage
<a name="usage"></a>

AeonSync provides an intuitive command-line interface for easy interaction with your backup setup.

```bash
# Perform a backup
aeon sync --remote user@host:/path/to/backups

# Restore a file
aeon restore /path/to/file 2024-09-05

# List available backups
aeon list-backups

# Show help
aeon --help
```

### Main Commands

```bash
# Perform a backup with custom options
aeon sync [OPTIONS]

# Restore a file from a specific backup date
aeon restore [OPTIONS] FILE [DATE]

# List all available backups
aeon list-backups [OPTIONS]
```

### Restore Functionality

AeonSync offers powerful restore capabilities:

- 🕰️ **Version Selection**: Choose from multiple backup versions of a file.
- 👀 **File Preview**: View file contents before restoring.
- 📊 **Diff Display**: Compare changes between versions.
- 🔄 **Interactive Mode**: User-friendly guided restore process.

To use the interactive restore mode:

```bash
aeon restore --interactive
```

This will guide you through selecting a backup date, choosing a file, and specifying the restore location.

For a full list of available commands and options, use:

```bash
aeon --help
```

## ⚙️ Configuration
<a name="configuration"></a>

AeonSync can be configured using command-line options or by modifying the `config.py` file:

- `DEFAULT_REMOTE`: Default remote server for backups
- `DEFAULT_RETENTION_PERIOD`: Default number of days to keep backups
- `DEFAULT_SOURCE_DIRS`: Default directories to back up
- `EXCLUSIONS`: Patterns to exclude from backups

Example configuration in `config.py`:

```python
DEFAULT_REMOTE = "user@example.com:/backups"
DEFAULT_RETENTION_PERIOD = 30
DEFAULT_SOURCE_DIRS = ["/home/user", "/var/www"]
EXCLUSIONS = [".cache", "*/node_modules", "*.tmp"]
```

## 🛠️ Development
<a name="development"></a>

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

## 👥 Contributing
<a name="contributing"></a>

Contributions to AeonSync are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a new branch: `git checkout -b feature-branch-name`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-branch-name`
5. Submit a pull request

Please ensure your code adheres to the project's style guide (we use Black for formatting) and passes all tests.

## 📄 License
<a name="license"></a>

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

📚 [Documentation](#) • 🐛 [Report Bug](https://github.com/hyperb1iss/aeonsync/issues) • 💡 [Request Feature](https://github.com/hyperb1iss/aeonsync/issues)

</div>

---

<div align="center">

Created by [Stefanie Jane 🌠](https://github.com/hyperb1iss)

If you find this project useful, [buy me a Monster Ultra Violet!](https://ko-fi.com/hyperb1iss)! ⚡️

</div>