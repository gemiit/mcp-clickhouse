"""MCP resource handlers for ClickHouse data access.

This package provides MCP resource handlers for accessing ClickHouse data and schema information.
Resources are grouped by functionality into separate modules:

- data: Resources for accessing table data and query results
- schema: Resources for accessing database and table schema information

Examples:
    Resources can be registered with a FastMCP server:

    >>> from app.api.resources import register_all_resources
    >>> from mcp.server import FastMCP
    >>> server = FastMCP(name="ClickHouse MCP")
    >>> register_all_resources(server, client)

    Or individual resource groups can be registered:

    >>> from app.api.resources import register_schema_resources
    >>> register_schema_resources(server, client)
"""

from mcp.server import FastMCP

from app.core.client import ClickHouseClient

# Import resource registration functions from submodules
from app.api.resources.data import register_data_resources
from app.api.resources.schema import register_schema_resources


def register_all_resources(
    server: FastMCP,
    client: ClickHouseClient,
) -> None:
    """Register all ClickHouse resources with the MCP server.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance
    """
    # Register resource groups
    register_data_resources(server, client)
    register_schema_resources(server, client)


__all__ = [
    "register_all_resources",
    "register_data_resources",
    "register_schema_resources",
]
