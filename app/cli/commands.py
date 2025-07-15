"""Command-line interface for MCP ClickHouse Server.

This module provides a simplified CLI layer that follows the single responsibility
principle. It only handles essential command-line arguments and delegates business
logic to the main module.

Architecture:
    CLI Layer (this file) → Business Logic Layer (app/main.py) → Service Layer (app/core/server.py)

The CLI has been simplified to remove complex argument overriding logic and only
supports essential parameters:
- transport: MCP transport protocol (streamable-http, sse, stdio)
- env_file: Path to environment file

All other configuration is handled through environment variables and FastMCP's
native configuration system (FASTMCP_* variables).

Examples:
    Basic usage:

    $ mcp-clickhouse run

    With specific transport:

    $ mcp-clickhouse run --transport sse

    With custom environment file:

    $ mcp-clickhouse run --env-file .env.production

    Environment variables are automatically loaded from .env file:
    - FASTMCP_*: FastMCP server configuration
    - CH_*: ClickHouse connection settings
    - APP_NAME: Application name
"""

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from app.utils.logging import configure_logging, get_logger
from app.main import run_server, Transport

# Initialize logger
logger = get_logger(__name__)

# Create typer app
app = typer.Typer(
    name="mcp-clickhouse",
    help="MCP ClickHouse Server - Enterprise-grade MCP server for ClickHouse integration",
    add_completion=False,
)


@app.callback()
def callback():
    """MCP ClickHouse Server - Enterprise-grade MCP server for ClickHouse integration."""
    # Load environment variables from .env file
    dotenv_path = Path(".env")
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
        logger.debug(f"Loaded environment variables from {dotenv_path}")

    # Configure logging
    configure_logging()


@app.command()
def run(
    transport: Optional[Transport] = typer.Option(
        None,
        "--transport",
        "-t",
        help="MCP transport protocol",
    ),
    env_file: Optional[str] = typer.Option(
        None,
        "--env-file",
        "-e",
        help="Path to .env file to load",
    ),
):
    run_server(
        transport=transport.value if transport else None,
        env_file=env_file,
    )


@app.command()
def version():
    """Show the version of the MCP ClickHouse server."""
    from app import __version__

    typer.echo(f"MCP ClickHouse Server v{__version__}")
    raise typer.Exit()


if __name__ == "__main__":
    app()
