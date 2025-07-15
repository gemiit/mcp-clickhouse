"""ClickHouse schema MCP resource registration.

This module provides resource registration for ClickHouse database, table, and schema access with FastMCP.
Each resource returns content in markdown format for easy frontend rendering.

Resource paths:
    - resource://schema                      # List databases
    - resource://schema/{database}           # List tables in a database
    - resource://schema/{database}/{table}   # Get table schema

Usage example:
    >>> from app.api.resources.schema import register_schema_resources
    >>> from app.core.client import ClickHouseClient
    >>> from mcp.server import FastMCP
    >>> server = FastMCP(name="ClickHouse MCP")
    >>> client = ClickHouseClient(host="localhost", port=9000)
    >>> register_schema_resources(server, client)
"""

from mcp.server import FastMCP
from app.core.client import ClickHouseClient
from app.utils.logging import get_logger

logger = get_logger(__name__)


def register_schema_resources(server: FastMCP, client: ClickHouseClient) -> None:
    """Register ClickHouse schema-related MCP resources."""

    @server.resource("resource://schema", title="Database List")
    async def list_databases() -> str:
        """List all databases."""
        try:
            databases = await client.get_databases()
            content = "# ClickHouse Databases\n\n"
            content += "| Database |\n| -------- |\n"
            for db in databases:
                content += f"| {db} |\n"
            logger.info("Listed databases", count=len(databases))
            return content
        except Exception as e:
            logger.error("Error listing databases", error=str(e))
            return f"Error listing databases: {str(e)}"

    @server.resource("resource://schema/{database}", title="Table List")
    async def list_tables(database: str) -> str:
        """List all tables in the specified database."""
        try:
            # 检查数据库是否存在
            databases = await client.get_databases()
            if database not in databases:
                logger.warning("Database not found", database=database)
                return f"Database '{database}' not found"

            tables = await client.get_tables(database=database)
            content = f"# Tables in {database}\n\n"
            content += "| Table | Engine | Rows | Size |\n"
            content += "| ----- | ------ | ---- | ---- |\n"
            for table in tables:
                try:
                    schema = await client.get_table_schema(
                        table=table, database=database
                    )
                    engine = schema.get("engine", "")
                    rows = schema.get("total_rows", 0)
                    size = schema.get("total_bytes", 0)
                    size_str = f"{size / 1024 / 1024:.2f} MB" if size else "0 MB"
                    content += f"| {table} | {engine} | {rows} | {size_str} |\n"
                except Exception as e:
                    logger.warning(
                        "Failed to get table schema",
                        database=database,
                        table=table,
                        error=str(e),
                    )
                    content += f"| {table} | Error: {str(e)} | - | - |\n"
            logger.info("Listed tables", database=database, count=len(tables))
            return content
        except Exception as e:
            logger.error("Error listing tables", database=database, error=str(e))
            return f"Error listing tables for {database}: {str(e)}"

    @server.resource("resource://schema/{database}/{table}", title="Table Schema")
    async def get_table_schema(database: str, table: str) -> str:
        """Get the schema of the specified table."""
        try:
            schema = await client.get_table_schema(table=table, database=database)
            content = f"# Schema for {database}.{table}\n\n"
            content += f"**Engine**: {schema.get('engine', '')}\n\n"
            if schema.get("total_rows") is not None:
                content += f"**Rows**: {schema['total_rows']}\n\n"
            if schema.get("total_bytes") is not None:
                size_mb = schema["total_bytes"] / 1024 / 1024
                content += f"**Size**: {size_mb:.2f} MB\n\n"
            if schema.get("comment"):
                content += f"**Comment**: {schema['comment']}\n\n"

            content += "## Columns\n\n"
            content += "| Name | Type | Default | Comment |\n"
            content += "| ---- | ---- | ------- | ------- |\n"
            for column in schema.get("columns", []):
                name = column.get("name", "")
                type_ = column.get("type", "")
                default = ""
                if column.get("default_type") and column.get("default_expression"):
                    default = f"{column['default_type']} {column['default_expression']}"
                comment = column.get("comment", "")
                content += f"| {name} | {type_} | {default} | {comment} |\n"

            if schema.get("create_table_query"):
                content += "\n## Create Table SQL\n\n"
                content += "```sql\n"
                content += schema["create_table_query"]
                content += "\n```\n"
            logger.info("Got table schema", database=database, table=table)
            return content
        except Exception as e:
            logger.error(
                "Error getting schema", database=database, table=table, error=str(e)
            )
            return f"Error getting schema for {database}.{table}: {str(e)}"

    logger.info("Registered ClickHouse schema resources")
