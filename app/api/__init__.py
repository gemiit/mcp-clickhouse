"""API package for MCP ClickHouse Server.

This package provides the API components for the MCP ClickHouse Server, including
tools for interacting with ClickHouse databases and resources for accessing data
and schema information.

The API is organized into two main components:
- Tools: Callable functions that perform operations on ClickHouse (query, insert, etc.)
- Resources: Data sources that provide access to ClickHouse data and schema information

Examples:
    Setting up all API components:

    >>> from app.api import setup_api
    >>> from app.core import ClickHouseServer, ClickHouseClient
    >>> server = ClickHouseServer()
    >>> client = ClickHouseClient()
    >>> setup_api(server.mcp_server, client)

    Or setting up specific components:

    >>> from app.api.tools import register_query_tools
    >>> from app.api.resources import register_schema_resources
    >>> register_query_tools(server.mcp_server, client)
    >>> register_schema_resources(server.mcp_server, client)
"""

from mcp.server import FastMCP

from app.core.client import ClickHouseClient

# Import tool registration functions
from app.api.tools import (
    register_all_tools,
    register_query_tools,
    register_schema_tools,
)

# Import resource registration functions
from app.api.resources import (
    register_all_resources,
    register_data_resources,
    register_schema_resources,
)

# Import prompts registration functions
from app.api.prompts import (
    register_all_prompts,
    register_migration_planning_prompt,
    register_migration_planning_prompt_en,
    register_table_analysis_prompt,
    register_table_analysis_prompt_en,
    register_query_optimization_prompt,
    register_query_optimization_prompt_en,
    register_schema_design_prompt,
    register_schema_design_prompt_en,
    register_performance_troubleshooting_prompt,
    register_performance_troubleshooting_prompt_en,
)


def setup_api(
    server: FastMCP,
    client: ClickHouseClient,
) -> None:
    """Set up all API components for the MCP ClickHouse Server.

    This function registers all tools, resources, and prompts with the MCP server,
    providing a complete API for interacting with ClickHouse databases.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance
    """
    # Register all tools
    register_all_tools(server, client)

    # Register all resources
    register_all_resources(server, client)

    # Register all prompts
    register_all_prompts(server, client)


__all__ = [
    # Main setup function
    "setup_api",
    # Tool registration functions
    "register_all_tools",
    "register_query_tools",
    "register_schema_tools",
    # Resource registration functions
    "register_all_resources",
    "register_data_resources",
    "register_schema_resources",
    # Prompts registration functions
    "register_all_prompts",
    "register_migration_planning_prompt",
    "register_migration_planning_prompt_en",
    "register_table_analysis_prompt",
    "register_table_analysis_prompt_en",
    "register_query_optimization_prompt",
    "register_query_optimization_prompt_en",
    "register_schema_design_prompt",
    "register_schema_design_prompt_en",
    "register_performance_troubleshooting_prompt",
    "register_performance_troubleshooting_prompt_en",
]
