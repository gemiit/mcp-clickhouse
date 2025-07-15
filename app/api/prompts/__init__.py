"""
ClickHouse Prompts API Package

This package provides modular prompt handler registration for various ClickHouse operations,
including table analysis, query optimization, schema design, performance troubleshooting, and migration planning.
Each functional area supports both Chinese and English prompt templates, allowing for flexible multi-language support.

Structure:
- table_analysis: Handlers for analyzing table structure and providing optimization suggestions.
- query_optimization: Handlers for analyzing and optimizing SQL queries.
- schema_design: Handlers for designing optimal ClickHouse schemas for specific use cases.
- performance_troubleshooting: Handlers for diagnosing and resolving performance issues.
- migration_planning: Handlers for planning data migration from other systems to ClickHouse.

All prompt handlers can be registered individually or collectively via the `register_all_prompts` function.
This design enables easy extension and maintainability for future prompt types and language support.
"""

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient

# Individual prompt handlers
from app.api.prompts.table_analysis import (
    register_table_analysis_prompt,
    register_table_analysis_prompt_en,
)
from app.api.prompts.query_optimization import (
    register_query_optimization_prompt,
    register_query_optimization_prompt_en,
)
from app.api.prompts.schema_design import (
    register_schema_design_prompt,
    register_schema_design_prompt_en,
)
from app.api.prompts.performance_troubleshooting import (
    register_performance_troubleshooting_prompt,
    register_performance_troubleshooting_prompt_en,
)
from app.api.prompts.migration_planning import (
    register_migration_planning_prompt,
    register_migration_planning_prompt_en,
)


def register_all_prompts(
    server: FastMCP,
    client: ClickHouseClient,
) -> None:
    """Register all ClickHouse tools with the MCP server.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance
    """
    # Register prompts
    register_table_analysis_prompt(server, client)
    register_table_analysis_prompt_en(server, client)
    register_query_optimization_prompt(server, client)
    register_query_optimization_prompt_en(server, client)
    register_schema_design_prompt(server, client)
    register_schema_design_prompt_en(server, client)
    register_performance_troubleshooting_prompt(server, client)
    register_performance_troubleshooting_prompt_en(server, client)
    register_migration_planning_prompt(server, client)
    register_migration_planning_prompt_en(server, client)


__all__ = [
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
