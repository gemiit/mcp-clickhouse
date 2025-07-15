"""CLI package for MCP ClickHouse Server.

This package provides the command-line interface for the MCP ClickHouse Server,
allowing users to interact with ClickHouse databases through the command line.

Examples:
    Basic usage:

    $ mcp-clickhouse --help
    $ mcp-clickhouse run
"""

from app.cli.commands import app

__all__ = ["app"]
