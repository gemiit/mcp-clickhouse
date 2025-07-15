#!/usr/bin/env python3
"""Main entry point for MCP ClickHouse Server.

This module provides the business logic layer for the MCP ClickHouse Server.
It bridges the CLI interface with the core server functionality, handling
environment configuration and server lifecycle management.

Architecture:
    CLI Layer (app/cli/commands.py) → Business Logic Layer (this file) → Service Layer (app/core/server.py)

The server uses FastMCP's native configuration system with FASTMCP_* environment
variables for simplified setup. This module only handles essential parameters
like transport protocol and environment file loading.

Examples:
    Direct usage:

    >>> from app.main import run_server
    >>> run_server(transport="streamable-http")

    With custom .env file:

    >>> run_server(transport="sse", env_file=".env.production")

    Environment variables are handled by FastMCP and the Settings system:
    - FASTMCP_*: FastMCP server configuration
    - CH_*: ClickHouse connection settings
    - APP_NAME: Application name (used as server name)
"""

import signal
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from app.utils.logging import get_logger
from app.core import ClickHouseServer
from app.api import setup_api

# Initialize logger
logger = get_logger(__name__)

# Create typer app
app = typer.Typer(
    name="mcp-clickhouse",
    help="MCP ClickHouse Server - Enterprise-grade MCP server for ClickHouse integration",
    add_completion=False,
)


class Transport(str, Enum):
    """Supported MCP transport protocols."""

    STREAMABLE_HTTP = "streamable-http"
    SSE = "sse"
    STDIO = "stdio"


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def version_callback(value: bool) -> None:
    """Print version information and exit."""
    if value:
        from app import __version__

        typer.echo(f"MCP ClickHouse Server v{__version__}")
        raise typer.Exit()


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""

    def handle_signal(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


def run_server(
    transport: Optional[str] = None,
    env_file: Optional[str] = None,
) -> None:
    """Run the MCP ClickHouse server (业务逻辑层).

    Args:
        transport: MCP transport protocol
        env_file: Path to .env file to load
    """
    # Load environment variables from .env file if provided
    if env_file:
        load_dotenv(env_file)

    # Create and configure the server
    server = ClickHouseServer()

    # Set up API components
    setup_api(server.mcp_server, server.client)

    # Handle SIGINT and SIGTERM signals
    setup_signal_handlers()

    # Run the server
    server.run(
        transport=transport or "streamable-http",
    )


@app.command()
def main(
    transport: Optional[Transport] = typer.Option(
        None, "--transport", "-t", help="MCP transport protocol"
    ),
    env_file: Optional[Path] = typer.Option(
        None, "--env-file", "-e", help="Path to .env file"
    ),
) -> None:
    """Start the MCP ClickHouse Server."""
    run_server(
        transport=transport.value if transport else None,
        env_file=str(env_file) if env_file else None,
    )


if __name__ == "__main__":
    app()
