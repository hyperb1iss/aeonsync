"""Restore functionality for AeonSync."""

from typing import Optional
from aeonsync.utils import parse_remote, build_ssh_cmd, run_command
from aeonsync.config import HOSTNAME

def restore_file(remote: str, backup_date: str, file_path: str, ssh_key: Optional[str] = None, remote_port: Optional[int] = None) -> None:
    """Restore a specific file from a backup."""
    remote_info = parse_remote(remote, remote_port)
    remote_file_path = f"{remote_info['path']}/{HOSTNAME}/{backup_date}/{file_path.lstrip('/')}"
    local_file_path = file_path

    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    cmd = [
        "rsync",
        "-avz",
        "-e", " ".join(ssh_cmd),
        f"{remote_info['user']}@{remote_info['host']}:{remote_file_path}",
        local_file_path,
    ]
    run_command(cmd)

def list_backups(remote: str, ssh_key: Optional[str] = None, remote_port: Optional[int] = None) -> None:
    """List all available backups with their metadata."""
    from aeonsync.config import METADATA_FILE_NAME
    
    remote_info = parse_remote(remote, remote_port)
    ssh_cmd = build_ssh_cmd(ssh_key, remote_port)
    ssh_cmd.extend([
        f"{remote_info['user']}@{remote_info['host']}",
        f"for d in {remote_info['path']}/{HOSTNAME}/20*-*-*; do "
        f"cat $d/{METADATA_FILE_NAME} 2>/dev/null || "
        f"echo '{{\"date\": \"'$(basename $d)'\", \"error\": \"No metadata found\"}}'; done"
    ])
    result = run_command(ssh_cmd)
    print(result.stdout)