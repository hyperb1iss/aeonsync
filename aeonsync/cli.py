"""Command-line interface for AeonSync."""

import typer
from pathlib import Path
from typing import List, Optional

from aeonsync.config import DEFAULT_REMOTE, DEFAULT_RETENTION_PERIOD, DEFAULT_SOURCE_DIRS
from aeonsync.backup import create_backup, cleanup_old_backups, needs_full_backup
from aeonsync.restore import restore_file, list_backups

app = typer.Typer()

@app.command()
def sync(
    sources: List[Path] = typer.Option(DEFAULT_SOURCE_DIRS, help="Source directories to backup"),
    remote: str = typer.Option(DEFAULT_REMOTE, help="Remote destination in the format [user@]host:path"),
    retention: int = typer.Option(DEFAULT_RETENTION_PERIOD, help="Number of days to retain backups"),
    ssh_key: Optional[Path] = typer.Option(None, help="Path to SSH private key for authentication"),
    port: Optional[int] = typer.Option(None, help="Remote SSH port"),
    dry_run: bool = typer.Option(False, help="Perform a dry run without making changes"),
    verbose: bool = typer.Option(False, help="Enable verbose output for rsync")
):
    """Create a backup of specified sources to the remote destination."""
    try:
        full_backup = needs_full_backup(remote, ssh_key, port)
        create_backup(remote, sources, full_backup, dry_run, ssh_key, port, verbose)
        if not dry_run:
            cleanup_old_backups(remote, retention, ssh_key, port)
        typer.echo("AeonSync completed.")
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)

@app.command()
def list(
    remote: str = typer.Option(DEFAULT_REMOTE, help="Remote destination in the format [user@]host:path"),
    ssh_key: Optional[Path] = typer.Option(None, help="Path to SSH private key for authentication"),
    port: Optional[int] = typer.Option(None, help="Remote SSH port")
):
    """List all available backups with their metadata."""
    try:
        list_backups(remote, ssh_key, port)
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)

@app.command()
def restore(
    file: Path = typer.Argument(..., help="File to restore"),
    date: str = typer.Argument(..., help="Backup date to restore from"),
    remote: str = typer.Option(DEFAULT_REMOTE, help="Remote destination in the format [user@]host:path"),
    ssh_key: Optional[Path] = typer.Option(None, help="Path to SSH private key for authentication"),
    port: Optional[int] = typer.Option(None, help="Remote SSH port")
):
    """Restore a specific file from a backup."""
    try:
        restore_file(remote, date, str(file), ssh_key, port)
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()