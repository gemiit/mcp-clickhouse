"""MCP ClickHouse Server - Enterprise-grade service bridging MCP and ClickHouse.

This package provides a Model Context Protocol (MCP) server for managing and interacting
with ClickHouse databases. It enables LLM applications to provision, query, and manage
ClickHouse clusters through a standardized interface.

Examples:
    Basic usage:

    >>> from app import ClickHouseServer
    >>> server = ClickHouseServer()
    >>> server.run()

For detailed documentation, please refer to the project README.md or the official docs.
"""

from importlib import metadata

__version__ = metadata.version("mcp-clickhouse-server")
__author__ = "gemiit"
__license__ = "Apache-2.0"
__copyright__ = f"Copyright 2025 {__author__}"
__description__ = "Enterprise-grade MCP server for ClickHouse integration"
__url__ = "https://github.com/gemiit/mcp-clickhouse"
__status__ = "Beta"

# Package exports
from app.utils.config import settings  # noqa
from app.utils.logging import configure_logging, get_logger  # noqa

# Core application objects
from app.core import (  # noqa
    ClickHouseServer,
    ClickHouseClient,
    ResultFormat,
)

# Configure package-level logger
logger = get_logger(__name__)

# Initialize the package
configure_logging()

__all__ = [
    "ClickHouseServer",
    "ClickHouseClient",
    "ResultFormat",
    "settings",
    "configure_logging",
    "get_logger",
    "logger",
]
