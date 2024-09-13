"""Command-line interface for AeonSync."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import typer
from rich.console import Console
from rich.table import Table

from aeonsync.config import (
    DEFAULT_REMOTE,
    DEFAULT_RETENTION_PERIOD,
    DEFAULT_SOURCE_DIRS,
    BackupConfig,
    config_manager,
)
from aeonsync.core import AeonSync

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
    ctx: typer.Context, sources: Sequence[Path], retention: int, dry_run: bool
) -> BackupConfig:
    """Create a BackupConfig instance from the context and command options.

    Args:
        ctx (typer.Context): Typer context object containing global options.
        sources (Sequence[Path]): Source directories to backup.
        retention (int): Number of days to retain backups.
        dry_run (bool): Whether to perform a dry run.

    Returns:
        BackupConfig: Configured backup configuration.
    """
    if not sources:
        sources = [Path(s) for s in DEFAULT_SOURCE_DIRS]
    return BackupConfig(
        remote=ctx.obj["remote"],
        sources=list(sources),
        ssh_key=ctx.obj["ssh_key"],
        remote_port=ctx.obj["port"],
        verbose=ctx.obj["verbose"],
        dry_run=dry_run,
        retention_period=retention,
    )


@dataclass
class RestoreOptions:
    """Dataclass to encapsulate restore command options."""

    file: Optional[Path] = None
    date: Optional[str] = None
    output_dir: Optional[Path] = None
    interactive: bool = False
    diff: bool = False
    preview: bool = False


@app.callback()
def callback(
    ctx: typer.Context,
    remote: str = remote_option,
    ssh_key: Optional[Path] = ssh_key_option,
    port: Optional[int] = port_option,
    verbose: bool = verbose_option,
):
    """
    Common options for all commands.

    Args:
        ctx (typer.Context): Typer context object.
        remote (str): Remote destination.
        ssh_key (Optional[Path]): Path to SSH key.
        port (Optional[int]): SSH port.
        verbose (bool): Enable verbose logging.
    """
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
        backup_config = get_backup_config(ctx, sources, retention, dry_run)
        aeonsync = AeonSync(backup_config)
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
    options: RestoreOptions = typer.Option(
        RestoreOptions(),
        help="Options for restoring files or directories",
    ),
):
    """Restore a specific file or directory from a backup."""
    try:
        # Use an empty list for sources, it will be populated with defaults in get_backup_config
        backup_config = get_backup_config(ctx, [], DEFAULT_RETENTION_PERIOD, False)
        aeonsync = AeonSync(backup_config)

        if options.interactive:
            aeonsync.restore_obj.restore_interactive(
                diff=options.diff, preview=options.preview
            )
        else:
            if options.file is None:
                options.file = Path.cwd()
            aeonsync.restore_obj.restore_file_versions(
                str(options.file),
                options.date,
                options.output_dir,
                diff=options.diff,
                preview=options.preview,
            )

    except Exception as e:
        logger.error("File restoration failed: %s", str(e), exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def list_backups(ctx: typer.Context):
    """List all available backups with their metadata."""
    try:
        backup_config = get_backup_config(ctx, [], DEFAULT_RETENTION_PERIOD, False)
        aeonsync = AeonSync(backup_config)
        aeonsync.list_backups()
    except Exception as e:
        logger.error("Failed to list backups: %s", str(e), exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def config(  # pylint: disable=too-many-arguments,too-many-branches
    hostname: Optional[str] = typer.Option(None, help="Set the hostname"),
    remote_address: Optional[str] = typer.Option(None, help="Set the remote address"),
    remote_path: Optional[str] = typer.Option(None, help="Set the remote path"),
    remote_port: Optional[int] = typer.Option(None, help="Set the remote port"),
    retention_period: Optional[int] = typer.Option(
        None, help="Set the retention period in days"
    ),
    add_source_dir: Optional[str] = typer.Option(None, help="Add a source directory"),
    remove_source_dir: Optional[str] = typer.Option(
        None, help="Remove a source directory"
    ),
    add_exclusion: Optional[str] = typer.Option(None, help="Add an exclusion pattern"),
    remove_exclusion: Optional[str] = typer.Option(
        None, help="Remove an exclusion pattern"
    ),
    ssh_key: Optional[str] = typer.Option(None, help="Set the SSH key path"),
    verbose: Optional[bool] = typer.Option(None, help="Set verbose mode"),
    log_file: Optional[str] = typer.Option(None, help="Set the log file path"),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
):
    """View or edit the AeonSync configuration."""
    if show:
        show_config(config_manager.config)
        return

    changed = False
    if hostname is not None:
        config_manager.set("hostname", hostname)
        changed = True
    if remote_address is not None:
        config_manager.set("remote_address", remote_address)
        changed = True
    if remote_path is not None:
        config_manager.set("remote_path", remote_path)
        changed = True
    if remote_port is not None:
        config_manager.set("remote_port", remote_port)
        changed = True
    if retention_period is not None:
        config_manager.set("retention_period", retention_period)
        changed = True
    if add_source_dir:
        config_manager.add_to_list("source_dirs", add_source_dir)
        changed = True
    if remove_source_dir:
        config_manager.remove_from_list("source_dirs", remove_source_dir)
        changed = True
    if add_exclusion:
        config_manager.add_to_list("exclusions", add_exclusion)
        changed = True
    if remove_exclusion:
        config_manager.remove_from_list("exclusions", remove_exclusion)
        changed = True
    if ssh_key is not None:
        config_manager.set("ssh_key", ssh_key)
        changed = True
    if verbose is not None:
        config_manager.set("verbose", verbose)
        changed = True
    if log_file is not None:
        config_manager.set("log_file", log_file)
        changed = True

    if changed:
        console.print("Configuration updated successfully!", style="bold green")
    else:
        console.print("No changes were made to the configuration.", style="yellow")

    show_config(config_manager.config)


def show_config(config_dict: Dict[str, Any]):
    """Display the current configuration.

    Args:
        config_dict (Dict[str, Any]): Configuration dictionary to display.
    """
    table = Table(title="AeonSync Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in config_dict.items():
        if isinstance(value, list):
            value = "\n".join(map(str, value))
        table.add_row(key, str(value))

    console.print(table)


if __name__ == "__main__":
    app()
