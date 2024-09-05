"""Command-line interface for AeonSync."""

import logging
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from aeonsync.config import (
    DEFAULT_REMOTE,
    DEFAULT_RETENTION_PERIOD,
    DEFAULT_SOURCE_DIRS,
    BackupConfig,
)
from aeonsync import AeonSync

# Set up logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Create a Typer app instance
app = typer.Typer()

# Create a Rich console instance
console = Console()

# Common options
remote_option = typer.Option(
    DEFAULT_REMOTE, help="Remote destination in the format [user@]host:path"
)
ssh_key_option = typer.Option(None, help="Path to SSH private key for authentication")
port_option = typer.Option(None, help="Remote SSH port")
verbose_option = typer.Option(False, help="Enable verbose output")


def get_backup_config(
    ctx: typer.Context, sources: List[Path], retention: int, dry_run: bool
) -> BackupConfig:
    """Create a BackupConfig instance from the context and command options."""
    return BackupConfig(
        remote=ctx.obj["remote"],
        sources=sources,
        ssh_key=ctx.obj["ssh_key"],
        remote_port=ctx.obj["port"],
        verbose=ctx.obj["verbose"],
        dry_run=dry_run,
        retention_period=retention,
    )


@app.callback()
def callback(
    ctx: typer.Context,
    remote: str = remote_option,
    ssh_key: Optional[Path] = ssh_key_option,
    port: Optional[int] = port_option,
    verbose: bool = verbose_option,
):
    """Common options for all commands."""
    ctx.ensure_object(dict)
    ctx.obj["remote"] = remote
    ctx.obj["ssh_key"] = ssh_key
    ctx.obj["port"] = port
    ctx.obj["verbose"] = verbose

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")


@app.command()
def sync(
    ctx: typer.Context,
    sources: List[Path] = typer.Option(
        [Path(s) for s in DEFAULT_SOURCE_DIRS], help="Source directories to backup"
    ),
    retention: int = typer.Option(
        DEFAULT_RETENTION_PERIOD, help="Number of days to retain backups"
    ),
    dry_run: bool = typer.Option(
        False, help="Perform a dry run without making changes"
    ),
):
    """Create a backup of specified sources to the remote destination."""
    try:
        config = get_backup_config(ctx, sources, retention, dry_run)
        aeonsync = AeonSync(config)
        with console.status("[bold green]Performing backup..."):
            aeonsync.sync()
        console.print("[bold green]Backup completed successfully.")
    except Exception as e:
        logger.error("Backup failed: %s", str(e), exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def restore(
    ctx: typer.Context,
    file: Path = typer.Argument(..., help="File to restore"),
    date: str = typer.Argument(..., help="Backup date to restore from"),
):
    """Restore a specific file from a backup."""
    try:
        config = get_backup_config(ctx, [], DEFAULT_RETENTION_PERIOD, False)
        aeonsync = AeonSync(config)
        with console.status(f"[bold green]Restoring file {file} from {date}..."):
            aeonsync.restore(date, str(file))
        console.print(f"[bold green]File {file} restored successfully from {date}.")
    except Exception as e:
        logger.error("File restoration failed: %s", str(e), exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def list_backups(ctx: typer.Context):
    """List all available backups with their metadata."""
    try:
        config = get_backup_config(ctx, [], DEFAULT_RETENTION_PERIOD, False)
        aeonsync = AeonSync(config)
        aeonsync.list_backups()
    except Exception as e:
        logger.error("Failed to list backups: %s", str(e), exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
