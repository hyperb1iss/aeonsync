"""Command-line interface for AeonSync."""

import logging
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from aeonsync.config import (
    config_manager,
    BackupConfig,
    DEFAULT_REMOTE,
    DEFAULT_RETENTION_PERIOD,
    DEFAULT_SOURCE_DIRS,
)
from aeonsync.backup import AeonBackup
from aeonsync.restore import AeonRestore
from aeonsync.list import ListBackups

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
verbose_option = typer.Option(False, "--verbose", "-v", help="Enable verbose output")


def validate_sources(sources: List[Path]):
    """Ensure all source directories exist."""
    for source in sources:
        if not source.exists() or not source.is_dir():
            raise typer.BadParameter(
                f"Source directory does not exist or is not a directory: {source}"
            )


def get_backup_config(
    ctx: typer.Context,
    sources: List[Path],
    retention: int,
    dry_run: bool,
    daily: Optional[bool],
) -> BackupConfig:
    """Create a BackupConfig instance from the context and command options."""
    if not sources:
        sources = [
            Path(s) for s in config_manager.get("source_dirs", DEFAULT_SOURCE_DIRS)
        ]
    # Convert the List[Path] to list[str | Path]
    sources_list: list[str | Path] = [
        str(source) if isinstance(source, Path) else source for source in sources
    ]
    daily = (
        daily
        if daily is not None
        else config_manager.get("default_daily_backup", False)
    )
    return BackupConfig(
        remote=ctx.obj["remote"],
        sources=sources_list,
        ssh_key=ctx.obj["ssh_key"],
        remote_port=ctx.obj["port"],
        verbose=ctx.obj["verbose"],
        dry_run=dry_run,
        retention_period=retention,
        daily=daily,
        log_file=ctx.obj.get("log_file"),
    )


@app.callback()
def callback(
    ctx: typer.Context,
    remote: str = remote_option,
    ssh_key: Optional[Path] = ssh_key_option,
    port: Optional[int] = port_option,
    verbose: bool = verbose_option,
    log_file: Optional[str] = typer.Option(None, help="Set the log file path"),
):
    """Common options for all commands."""
    ctx.ensure_object(dict)
    ctx.obj["remote"] = remote
    ctx.obj["ssh_key"] = ssh_key
    ctx.obj["port"] = port
    ctx.obj["verbose"] = verbose
    ctx.obj["log_file"] = log_file

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    else:
        logging.getLogger().setLevel(logging.INFO)


@app.command()
def sync(
    ctx: typer.Context,
    sources: List[Path] = typer.Option(
        DEFAULT_SOURCE_DIRS,
        "--source",
        "-s",
        help="Source directories to backup. Can be specified multiple times.",
        show_default=True,
    ),
    retention: int = typer.Option(
        DEFAULT_RETENTION_PERIOD, help="Number of days to retain backups"
    ),
    dry_run: bool = typer.Option(
        False, help="Perform a dry run without making changes"
    ),
    daily: Optional[bool] = typer.Option(
        None,
        "--daily",
        help="Only create one backup per day (old behavior)",
    ),
):
    """Create a backup of specified sources to the remote destination."""
    try:
        validate_sources(sources)
        backup_config = get_backup_config(ctx, sources, retention, dry_run, daily)
        backup = AeonBackup(backup_config)
        with console.status("[bold green]Performing backup..."):
            backup.create_backup()
        console.print("[bold green]Backup completed successfully.")
    except typer.BadParameter as e:
        logger.error("Invalid parameter: %s", str(e))
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error("Backup failed: %s", str(e), exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def restore(
    ctx: typer.Context,
    file: Optional[Path] = typer.Argument(
        None, help="File or directory to restore (current directory if not specified)"
    ),
    date: Optional[str] = typer.Argument(None, help="Backup date to restore from"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for restored file or directory"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Use fully interactive mode for restore"
    ),
    diff: bool = typer.Option(
        False, "--diff", help="Show diff between local and backup versions"
    ),
    preview: bool = typer.Option(
        False, "--preview", help="Show a preview of the file before restoring"
    ),
):
    """Restore a specific file or directory from a backup."""
    try:
        sources = config_manager.get("source_dirs", DEFAULT_SOURCE_DIRS)
        backup_config = get_backup_config(
            ctx,
            sources,
            config_manager.get("retention_period", DEFAULT_RETENTION_PERIOD),
            False,
            daily=None,  # daily not relevant for restore
        )
        restore_obj = AeonRestore(backup_config)

        if interactive:
            restore_obj.restore_interactive(diff=diff, preview=preview)
        else:
            if file is None:
                file = Path.cwd()
            restore_obj.restore_file_versions(
                str(file), date, output_dir, diff=diff, preview=preview
            )

    except Exception as e:
        logger.error("File restoration failed: %s", str(e), exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def list_backups(ctx: typer.Context):
    """List all available backups with their metadata."""
    try:
        remote = ctx.obj.get("remote")
        if not remote:
            raise typer.BadParameter("Remote destination is not set.")
        backup_config = BackupConfig(
            remote=remote,
            sources=[],  # Sources are not required for restore
            ssh_key=config_manager.get("ssh_key"),
            remote_port=config_manager.get("remote_port"),
            verbose=config_manager.get("verbose"),
            dry_run=False,
            retention_period=config_manager.get("retention_period"),
            daily=config_manager.get("default_daily_backup", False),
            log_file=config_manager.get("log_file"),
        )
        list_backups_obj = ListBackups(backup_config)
        list_backups_obj.list()
    except typer.BadParameter as e:
        logger.error("Invalid parameter: %s", str(e))
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error("Failed to list backups: %s", str(e), exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

# pylint: disable=too-many-branches
@app.command()
def config(
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
    default_daily_backup: Optional[bool] = typer.Option(
        None,
        "--default-daily-backup/--no-default-daily-backup",
        help="Enable or disable daily backups as the default behavior",
    ),
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
    if default_daily_backup is not None:
        config_manager.set("default_daily_backup", default_daily_backup)
        changed = True

    if changed:
        console.print("Configuration updated successfully!", style="bold green")
    else:
        console.print("No changes were made to the configuration.", style="yellow")

    show_config(config_manager.config)


def show_config(config_dict: dict):
    """Display the current configuration."""
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
