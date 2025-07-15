"""MCP tool handlers for ClickHouse operations.

This package provides MCP tool handlers for interacting with ClickHouse databases.
Tools are grouped by functionality into separate modules:

- query: Tools for executing queries and inserting data
- schema: Tools for managing database schemas (create databases and tables)

Examples:
    Tools can be registered with a FastMCP server:

    >>> from app.api.tools import register_all_tools
    >>> from mcp.server import FastMCP
    >>> server = FastMCP(name="ClickHouse MCP")
    >>> register_all_tools(server, client)

    Or individual tool groups can be registered:

    >>> from app.api.tools import register_query_tools
    >>> register_query_tools(server, client)
"""

from mcp.server import FastMCP

from app.core.client import ClickHouseClient

# Import tool registration functions from submodules
# These will be implemented in their respective files
from app.api.tools.query import register_query_tools
from app.api.tools.schema import register_schema_tools


def register_all_tools(
    server: FastMCP,
    client: ClickHouseClient,
) -> None:
    """Register all ClickHouse tools with the MCP server.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance
    """
    # Register tool groups
    register_query_tools(server, client)
    register_schema_tools(server, client)


__all__ = [
    "register_all_tools",
    "register_query_tools",
    "register_schema_tools",
]
