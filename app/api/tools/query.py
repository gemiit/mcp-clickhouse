"""MCP tool handlers for ClickHouse query operations.

This module provides MCP tool handlers for executing queries against ClickHouse
databases and inserting data into ClickHouse tables. These tools are the primary
way for MCP clients to interact with ClickHouse data.

Examples:
    These tools can be registered with a FastMCP server:

    >>> from app.api.tools.query import register_query_tools
    >>> from app.core.client import ClickHouseClient
    >>> from mcp.server import FastMCP
    >>> server = FastMCP(name="ClickHouse MCP")
    >>> client = ClickHouseClient(host="localhost", port=9000)
    >>> register_query_tools(server, client)

    Once registered, MCP clients can call the tools:

    >>> result = await session.call_tool("query", {"sql": "SELECT 1"})
    >>> await session.call_tool("insert", {"table": "my_table", "data": [{"id": 1, "name": "test"}]})
"""

import time
from typing import Any, Dict, List, Optional

from mcp.server import FastMCP
from pydantic import BaseModel, Field, field_validator

from app.core.client import ClickHouseClient, ResultFormat
from app.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class QueryParams(BaseModel):
    """Parameters for the query tool."""

    sql: str = Field(..., description="SQL query to execute")
    format: str = Field(
        default="json", description="Output format (json, pretty, csv, tsv)"
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Parameters for the query"
    )


class InsertParams(BaseModel):
    """Parameters for the insert tool."""

    table: str = Field(..., description="Table name to insert into")
    data: List[Dict[str, Any]] = Field(..., description="Data to insert")
    database: Optional[str] = Field(
        default=None,
        description="Database name (defaults to the client's default database)",
    )

    @field_validator("data")
    def validate_data_not_empty(cls, v):
        """Validate that data is not empty."""
        if not v:
            raise ValueError("Data cannot be empty")
        return v


def register_query_tools(server: FastMCP, client: ClickHouseClient) -> None:
    """Register ClickHouse query tools with the MCP server.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance
    """

    @server.tool("query")
    async def query(
        sql: str,
        format: str = "json",
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a SQL query on the ClickHouse server.

        Args:
            sql: SQL query to execute
            format: Output format (json, pretty, csv, tsv)
            params: Parameters for the query

        Returns:
            Query results and metadata
        """
        start_time = time.time()
        logger.info(
            "Executing query",
            sql=sql[:100] + ("..." if len(sql) > 100 else ""),
            format=format,
            has_params=params is not None,
        )

        try:
            # Validate format
            try:
                result_format = ResultFormat(format.lower())
            except ValueError:
                logger.warning(f"Invalid format: {format}, using JSON")
                result_format = ResultFormat.JSON

            # Execute the query
            if result_format == ResultFormat.PRETTY:
                result_str = await client.execute_with_format(
                    query=sql,
                    format_name=result_format,
                    params=params,
                )
                result_data = result_str
                rows = result_str.count("\n")
            else:
                result_data = await client.execute(
                    query=sql,
                    params=params,
                    with_column_types=True,
                )
                rows = len(result_data[0])

                if result_format == ResultFormat.JSON:
                    # Format as JSON
                    columns = [col[0] for col in result_data[1]]
                    result_rows = []
                    for row in result_data[0]:
                        result_rows.append(dict(zip(columns, row)))
                    result_data = result_rows

            duration = time.time() - start_time
            logger.info(
                "Query executed successfully",
                rows=rows,
                duration=duration,
            )

            return {
                "result": result_data,
                "rows": rows,
                "query": sql,
                "duration": duration,
                "format": format,
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Query execution failed",
                sql=sql[:100] + ("..." if len(sql) > 100 else ""),
                error=str(e),
                duration=duration,
            )
            raise ValueError(f"Query execution failed: {str(e)}")

    @server.tool("insert")
    async def insert(
        table: str,
        data: List[Dict[str, Any]],
        database: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert data into a ClickHouse table.

        Args:
            table: Table name to insert into
            data: List of dictionaries containing the data to insert
            database: Database name (defaults to the client's default database)

        Returns:
            Result of the insert operation
        """
        start_time = time.time()
        logger.info(
            "Inserting data",
            table=table,
            database=database or client.database,
            rows=len(data),
        )

        try:
            # Validate data
            if not data:
                raise ValueError("Data cannot be empty")

            # Insert data
            result = await client.insert_data(
                table=table,
                data=data,
                database=database,
            )

            duration = time.time() - start_time
            logger.info(
                "Data inserted successfully",
                table=table,
                database=database or client.database,
                rows=len(data),
                duration=duration,
            )

            return {
                **result,
                "duration": duration,
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Data insertion failed",
                table=table,
                database=database or client.database,
                error=str(e),
                duration=duration,
            )
            raise ValueError(f"Data insertion failed: {str(e)}")

    @server.tool("get_tables")
    async def get_tables(
        database: str,
    ) -> Dict[str, Any]:
        """
        Get all tables in a ClickHouse database.

        Args:
            database: Database name

        Returns:
            Dictionary with table list and database name
        """
        start_time = time.time()
        logger.info("Getting tables", database=database)
        try:
            tables = await client.get_tables(database)
            duration = time.time() - start_time
            logger.info(
                "Got tables",
                database=database,
                count=len(tables),
                duration=duration,
            )
            return {
                "database": database,
                "tables": tables,
                "count": len(tables),
                "duration": duration,
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Get tables failed",
                database=database,
                error=str(e),
                duration=duration,
            )
            raise ValueError(f"Get tables failed: {str(e)}")

    logger.info("Registered ClickHouse query tools")
