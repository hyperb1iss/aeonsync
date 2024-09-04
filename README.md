# AeonSync

_AeonSync: Flexible Remote Backup Tool_

**AeonSync** is a powerful, flexible backup tool designed to efficiently sync directories to a remote server using rsync over SSH. Built with developers and sysadmins in mind, AeonSync provides incremental backups, intelligent file linking, and customizable retention policies. With a simple setup and robust error handling, it's your one-stop solution for reliable, automated backups.

---

## Table of Contents

- [Why AeonSync?](#why-aeonsync)
- [Features](#features)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Setup](#setup)
- [Configuration](#configuration)
- [Automating Backups](#automating-backups)
- [Restoring Files](#restoring-files)
- [Contributing](#contributing)

---

## Why AeonSync?

We live in an era where data matters. Whether you're working on the next big project or safeguarding essential personal files, data loss is never an option. AeonSync helps ensure that your important files are always safe—incrementally and efficiently.

- **Simplicity Meets Power**: Run a single command to back up your critical files. AeonSync handles the rest—hard linking, SSH connections, and ensuring that only changed files are synced.
- **Customizable**: Configure the remote server, backup intervals, retention periods, and more to match your needs.
- **Incremental and Intelligent**: Why back up everything when only a few files have changed? AeonSync uses hard links for files that haven’t changed, saving space and time.

---

## Features

- **Incremental Backups**: Only backs up changed files, using rsync’s `--link-dest` to create hard links for unchanged files.
- **Remote Syncing via SSH**: Use any server you can SSH into.
- **Customizable Retention**: Clean up old backups automatically with customizable retention policies.
- **Verbose and Dry-Run Modes**: Test backups before running them with `--dry-run` and view detailed transfer logs with `--verbose`.
- **Metadata Tracking**: Every backup comes with a detailed JSON metadata file, making tracking and restoring files easy.
- **Ease of Use**: Minimal setup, intuitive commands, and automated directory creation.

---

## Quick Start

Here’s how to get AeonSync up and running in a matter of minutes:

1. **Install dependencies**: You need Python 3 and rsync. Install them if you don't already have them.
    ```bash
    sudo apt-get install rsync python3
    ```

2. **Clone the repository**:
    ```bash
    git clone https://github.com/hyperb1iss/aeonsync.git
    cd aeonsync
    ```

3. **First-time setup**:
    Run the setup wizard to configure AeonSync:
    ```bash
    python aeonsync.py setup
    ```

4. **Run your first backup**:
    ```bash
    python aeonsync.py sync --remote bliss@cloudless:aeonsync
    ```

---

## Usage

AeonSync’s usage is simple yet powerful. Here’s an overview of the main commands:

### **Backup Command**
```bash
python aeonsync.py sync [options]
```
**Options**:
- `--sources`: Specify the directories you want to back up (default: `/home`).
- `--remote`: Remote server in `user@host:path` format (default: `bliss@cloudless:aeonsync`).
- `--port`: Specify the SSH port if it’s not the default (22).
- `--ssh-key`: Path to the SSH key for authentication.
- `--dry-run`: Perform a dry run without actually making changes.
- `--verbose`: Output detailed rsync logs.

### **List Available Backups**
```bash
python aeonsync.py list [options]
```
Lists all available backups on the remote server, along with metadata.

### **Restore a File**
```bash
python aeonsync.py restore --file <path> --date <backup-date> [options]
```
Restore a specific file from a specific backup date.

---

## Setup

The **setup wizard** helps you configure AeonSync for your environment. You’ll be prompted to enter the following:

- **Remote Server**: Enter your remote server’s address (`user@host:path`).
- **SSH Port**: The port your SSH server is running on.
- **Backup Directory**: Where you’d like to store your backups on the remote server.

For advanced users, these settings can also be managed directly via the command line.

---

## Configuration

AeonSync offers several options to fit different backup needs:

- **Sources**: Define which directories you’d like to back up.
- **Exclusions**: Common temporary or cache files are excluded by default, but this can be customized in the script.
- **Retention**: Define how many days you’d like to retain backups (default: 7 days).

---

## Automating Backups

Automating your backups is easy using **cron** or any other job scheduler.

1. Open your crontab:
    ```bash
    crontab -e
    ```

2. Add a line like this to back up your files daily at midnight:
    ```bash
    0 0 * * * /usr/bin/python3 /path/to/aeonsync/aeonsync.py sync --remote bliss@cloudless:aeonsync --ssh-key ~/.ssh/id_rsa
    ```

---

## Restoring Files

Need to restore a file? No problem.

1. Find the backup date by listing available backups:
    ```bash
    python aeonsync.py list
    ```

2. Restore a specific file from a specific backup:
    ```bash
    python aeonsync.py restore --file /path/to/file --date 2024-09-04 --remote bliss@cloudless:aeonsync
    ```

---

## Contributing

AeonSync is an open-source project, and contributions are always welcome. If you have a feature request, find a bug, or have improvements to suggest, please feel free to open an issue or a pull request!

**To contribute**:
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/awesome-feature`).
3. Commit your changes (`git commit -m 'Add some awesome feature'`).
4. Push to the branch (`git push origin feature/awesome-feature`).
5. Open a pull request.

---

## License

AeonSync is licensed under the MIT License. See [LICENSE](LICENSE) for more details.