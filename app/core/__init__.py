"""Core package for MCP ClickHouse Server.

This package provides the core functionality for the MCP ClickHouse Server,
including the client for connecting to ClickHouse databases and the server
for exposing ClickHouse functionality through the Model Context Protocol.

Examples:
    Basic client usage:

    >>> from app.core import ClickHouseClient
    >>> client = ClickHouseClient(host="localhost", port=9000)
    >>> result = await client.execute("SELECT 1")
    >>> print(result)

    Basic server usage:

    >>> from app.core import ClickHouseServer
    >>> server = ClickHouseServer()
    >>> server.run()
"""

# Import client components
from app.core.client import (
    ClickHouseClient,
    ClickHouseConnection,
    ClickHouseConnectionPool,
    ResultFormat,
)

# Import server components
from app.core.server import ClickHouseServer

__all__ = [
    "ClickHouseClient",
    "ClickHouseConnection",
    "ClickHouseConnectionPool",
    "ClickHouseServer",
    "ResultFormat",
]
