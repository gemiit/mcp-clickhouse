"""MCP tool handlers for ClickHouse schema operations.

This module provides MCP tool handlers for managing ClickHouse database schemas,
including creating databases and tables. These tools allow MCP clients
to manage the structure of ClickHouse databases without direct SQL access.

Examples:
    These tools can be registered with a FastMCP server:

    >>> from app.api.tools.schema import register_schema_tools
    >>> from app.core.client import ClickHouseClient
    >>> from mcp.server import FastMCP
    >>> server = FastMCP(name="ClickHouse MCP")
    >>> client = ClickHouseClient(host="localhost", port=9000)
    >>> register_schema_tools(server, client)

    Once registered, MCP clients can call the tools:

    >>> await session.call_tool("create_database", {"name": "my_database"})
    >>> await session.call_tool("create_table", {
    ...     "database": "my_database",
    ...     "name": "my_table",
    ...     "columns": [
    ...         {"name": "id", "type": "UInt32"},
    ...         {"name": "name", "type": "String"}
    ...     ],
    ...     "engine": "MergeTree()",
    ...     "order_by": "id"
    ... })
"""

import time
from typing import Any, Dict, List, Optional

from mcp.server import FastMCP
from pydantic import BaseModel, Field, field_validator

from app.core.client import ClickHouseClient
from app.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class CreateDatabaseParams(BaseModel):
    """Parameters for the create_database tool."""

    name: str = Field(..., description="Database name to create")
    if_not_exists: bool = Field(
        default=True,
        description="Whether to ignore errors if the database already exists",
    )


class ColumnDefinition(BaseModel):
    """Definition of a table column."""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")
    default_expression: Optional[str] = Field(
        default=None, description="Default expression for the column"
    )
    comment: Optional[str] = Field(default=None, description="Comment for the column")


class CreateTableParams(BaseModel):
    """Parameters for the create_table tool."""

    database: Optional[str] = Field(
        default=None,
        description="Database name (defaults to the client's default database)",
    )
    name: str = Field(..., description="Table name to create")
    columns: List[ColumnDefinition] = Field(
        ..., description="List of column definitions"
    )
    engine: str = Field(..., description="Table engine")
    order_by: str = Field(..., description="ORDER BY clause for the table")
    partition_by: Optional[str] = Field(
        default=None, description="PARTITION BY clause for the table"
    )
    primary_key: Optional[str] = Field(
        default=None, description="PRIMARY KEY clause for the table"
    )
    sample_by: Optional[str] = Field(
        default=None, description="SAMPLE BY clause for the table"
    )
    ttl: Optional[str] = Field(default=None, description="TTL clause for the table")
    settings: Optional[Dict[str, Any]] = Field(
        default=None, description="Table settings"
    )
    if_not_exists: bool = Field(
        default=True, description="Whether to ignore errors if the table already exists"
    )

    @field_validator("columns")
    def validate_columns_not_empty(cls, v):
        """Validate that columns list is not empty."""
        if not v:
            raise ValueError("Columns cannot be empty")
        return v


def register_schema_tools(server: FastMCP, client: ClickHouseClient) -> None:
    """Register ClickHouse schema management tools with the MCP server.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance
    """

    @server.tool("create_database")
    async def create_database(
        name: str,
        if_not_exists: bool = True,
    ) -> Dict[str, Any]:
        """Create a new database in ClickHouse.

        Args:
            name: Database name to create
            if_not_exists: Whether to ignore errors if the database already exists

        Returns:
            Result of the database creation operation
        """
        start_time = time.time()
        logger.info(
            "Creating database",
            name=name,
            if_not_exists=if_not_exists,
        )

        try:
            # Build SQL query
            sql = (
                f"CREATE DATABASE {'' if not if_not_exists else 'IF NOT EXISTS '}{name}"
            )

            # Execute query
            await client.execute(sql)

            duration = time.time() - start_time
            logger.info(
                "Database created successfully",
                name=name,
                duration=duration,
            )

            return {
                "name": name,
                "created": True,
                "duration": duration,
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Database creation failed",
                name=name,
                error=str(e),
                duration=duration,
            )
            raise ValueError(f"Database creation failed: {str(e)}")

    @server.tool("create_table")
    async def create_table(
        name: str,
        columns: List[Dict[str, Any]],
        engine: str,
        order_by: str,
        database: Optional[str] = None,
        partition_by: Optional[str] = None,
        primary_key: Optional[str] = None,
        sample_by: Optional[str] = None,
        ttl: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        if_not_exists: bool = True,
    ) -> Dict[str, Any]:
        """Create a new table in ClickHouse.

        Args:
            name: Table name to create
            columns: List of column definitions
            engine: Table engine
            order_by: ORDER BY clause for the table
            database: Database name (defaults to the client's default database)
            partition_by: PARTITION BY clause for the table
            primary_key: PRIMARY KEY clause for the table
            sample_by: SAMPLE BY clause for the table
            ttl: TTL clause for the table
            settings: Table settings
            if_not_exists: Whether to ignore errors if the table already exists

        Returns:
            Result of the table creation operation
        """
        start_time = time.time()
        db = database or client.database
        logger.info(
            "Creating table",
            database=db,
            name=name,
            columns_count=len(columns),
            engine=engine,
            if_not_exists=if_not_exists,
        )

        try:
            # Validate columns
            if not columns:
                raise ValueError("Columns cannot be empty")

            # Build column definitions
            column_defs = []
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                col_default = col.get("default_expression")
                col_comment = col.get("comment")

                col_def = f"`{col_name}` {col_type}"
                if col_default:
                    col_def += f" DEFAULT {col_default}"
                if col_comment:
                    col_def += f" COMMENT '{col_comment}'"

                column_defs.append(col_def)

            # Build SQL query
            sql = f"CREATE TABLE {'' if not if_not_exists else 'IF NOT EXISTS '}{db}.`{name}` (\n"
            sql += ",\n".join(f"    {col_def}" for col_def in column_defs)
            sql += f"\n) ENGINE = {engine}"

            if partition_by:
                sql += f"\nPARTITION BY {partition_by}"

            sql += f"\nORDER BY {order_by}"

            if primary_key and primary_key != order_by:
                sql += f"\nPRIMARY KEY {primary_key}"

            if sample_by:
                sql += f"\nSAMPLE BY {sample_by}"

            if ttl:
                sql += f"\nTTL {ttl}"

            if settings:
                settings_list = []
                for key, value in settings.items():
                    if isinstance(value, str):
                        settings_list.append(f"{key} = '{value}'")
                    else:
                        settings_list.append(f"{key} = {value}")

                if settings_list:
                    sql += f"\nSETTINGS {', '.join(settings_list)}"

            # Execute query
            await client.execute(sql)

            duration = time.time() - start_time
            logger.info(
                "Table created successfully",
                database=db,
                name=name,
                duration=duration,
            )

            return {
                "database": db,
                "name": name,
                "created": True,
                "duration": duration,
                "columns_count": len(columns),
                "engine": engine,
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Table creation failed",
                database=db,
                name=name,
                error=str(e),
                duration=duration,
            )
            raise ValueError(f"Table creation failed: {str(e)}")

    logger.info("Registered ClickHouse schema management tools")
