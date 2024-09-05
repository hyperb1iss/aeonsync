"""Command-line interface for AeonSync."""

import typer
import logging
from pathlib import Path
from typing import List, Optional

from aeonsync.config import (
    DEFAULT_REMOTE,
    DEFAULT_RETENTION_PERIOD,
    DEFAULT_SOURCE_DIRS,
)
from aeonsync.backup import create_backup, cleanup_old_backups, needs_full_backup
from aeonsync.restore import restore_file, list_backups

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create a Typer app instance
app = typer.Typer()

# Common options
remote_option = typer.Option(
    DEFAULT_REMOTE, help="Remote destination in the format [user@]host:path"
)
ssh_key_option = typer.Option(None, help="Path to SSH private key for authentication")
port_option = typer.Option(None, help="Remote SSH port")
verbose_option = typer.Option(False, help="Enable verbose output")


def common_callback(ctx: typer.Context, verbose: bool = verbose_option):
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")


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
    common_callback(ctx, verbose)


@app.command()
def sync(
    ctx: typer.Context,
    sources: List[str] = typer.Option(
        DEFAULT_SOURCE_DIRS, help="Source directories to backup"
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
        logger.info("Starting backup process")
        logger.debug(
            "Sync parameters: sources=%s, remote=%s, retention=%d, ssh_key=%s, port=%s, dry_run=%s, verbose=%s",
            sources,
            ctx.obj["remote"],
            retention,
            ctx.obj["ssh_key"],
            ctx.obj["port"],
            dry_run,
            ctx.obj["verbose"],
        )

        full_backup = needs_full_backup(
            ctx.obj["remote"], ctx.obj["ssh_key"], ctx.obj["port"]
        )
        logger.info("Performing %s backup", "full" if full_backup else "incremental")

        create_backup(
            ctx.obj["remote"],
            sources,
            full_backup,
            dry_run,
            ctx.obj["ssh_key"],
            ctx.obj["port"],
            ctx.obj["verbose"],
        )

        if not dry_run:
            logger.info("Cleaning up old backups")
            cleanup_old_backups(
                ctx.obj["remote"], retention, ctx.obj["ssh_key"], ctx.obj["port"]
            )

        logger.info("AeonSync completed successfully")
        typer.echo("AeonSync completed successfully.")
    except Exception as e:
        logger.error("Error during backup process: %s", str(e), exc_info=True)
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)


@app.command()
def list(ctx: typer.Context):
    """List all available backups with their metadata."""
    try:
        logger.info("Listing available backups")
        logger.debug(
            "List parameters: remote=%s, ssh_key=%s, port=%s",
            ctx.obj["remote"],
            ctx.obj["ssh_key"],
            ctx.obj["port"],
        )
        list_backups(ctx.obj["remote"], ctx.obj["ssh_key"], ctx.obj["port"])
    except Exception as e:
        logger.error("Error while listing backups: %s", str(e), exc_info=True)
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)


@app.command()
def restore(
    ctx: typer.Context,
    file: Path = typer.Argument(..., help="File to restore"),
    date: str = typer.Argument(..., help="Backup date to restore from"),
):
    """Restore a specific file from a backup."""
    try:
        logger.info("Starting file restoration")
        logger.debug(
            "Restore parameters: file=%s, date=%s, remote=%s, ssh_key=%s, port=%s",
            file,
            date,
            ctx.obj["remote"],
            ctx.obj["ssh_key"],
            ctx.obj["port"],
        )
        restore_file(
            ctx.obj["remote"], date, str(file), ctx.obj["ssh_key"], ctx.obj["port"]
        )
        logger.info("File restoration completed successfully")
    except Exception as e:
        logger.error("Error during file restoration: %s", str(e), exc_info=True)
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
