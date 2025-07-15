"""ClickHouse client package for MCP ClickHouse Server.

This package provides a client for connecting to ClickHouse databases, with support for
connection pooling, query execution, result formatting, and error handling. It is
designed to be used with the MCP ClickHouse Server, but can also be used standalone.

Examples:
    Basic usage:

    >>> from app.core.client import ClickHouseClient
    >>> client = ClickHouseClient(host="localhost", port=9000)
    >>> result = await client.execute("SELECT 1")
    >>> print(result)

    With connection pooling:

    >>> client = ClickHouseClient(host="localhost", port=9000, pool_size=5)
    >>> async with client.get_connection() as conn:
    >>>     result = await conn.execute("SELECT 1")
"""

# Forward imports from submodules
from app.core.client.connection import ClickHouseConnection
from app.core.client.formats import ResultFormat
from app.core.client.pool import ClickHouseConnectionPool, ClickHouseClient


__all__ = [
    "ClickHouseClient",
    "ClickHouseConnection",
    "ClickHouseConnectionPool",
    "ResultFormat",
]
