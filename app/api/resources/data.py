"""ClickHouse data MCP resource registration.

This module provides resource registration for ClickHouse data access with FastMCP.
Each resource returns content in markdown, JSON, or CSV/TSV format for easy frontend rendering.

Resource paths:
    - resource://data/{database}/{table}/sample         # Get table sample data
    - resource://data/{database}/{table}/count          # Get table row count

Usage example:
    >>> from app.api.resources.data import register_data_resources
    >>> from app.core.client import ClickHouseClient
    >>> from mcp.server import FastMCP
    >>> server = FastMCP(name="ClickHouse MCP")
    >>> client = ClickHouseClient(host="localhost", port=9000)
    >>> register_data_resources(server, client)
"""


from mcp.server import FastMCP
from app.core.client import ClickHouseClient
from app.utils.logging import get_logger

logger = get_logger(__name__)


def register_data_resources(server: FastMCP, client: ClickHouseClient) -> None:
    """Register ClickHouse data access MCP resources."""

    @server.resource(
        "resource://data/{database}/{table}/sample?start_time={start_time}&end_time={end_time}&time_column={time_column}&limit={limit}",
        title="Table Sample Data (with time filter)",
    )
    async def table_sample(
        database: str,
        table: str,
        limit: int = 10,
        start_time: str = None,
        end_time: str = None,
        time_column: str = None,
    ) -> str:
        """
        Get table sample data, with optional time range filtering.

        :param database: Database name
        :param table: Table name
        :param limit: Number of rows to return
        :param start_time: Start time (optional, ISO8601 string)
        :param end_time: End time (optional, ISO8601 string)
        :param time_column: Time column name (optional, auto-detects common fields by default)
        """
        try:
            # Check if database and table exist
            databases = await client.get_databases()
            if database not in databases:
                logger.warning("Database not found", database=database)
                return f"Database '{database}' not found"
            tables = await client.get_tables(database=database)
            if table not in tables:
                logger.warning("Table not found", database=database, table=table)
                return f"Table '{database}.{table}' not found"
            if limit < 1 or limit > 1000:
                logger.warning("Invalid sample limit", limit=limit)
                return f"Invalid sample limit: {limit}. Must be between 1 and 1000."

            # Time column inference
            if time_column is None:
                # Get table columns
                columns_info = await client.get_columns(database=database, table=table)
                candidate_names = [
                    "event_time",
                    "created_at",
                    "timestamp",
                    "ts",
                    "time",
                ]
                for cand in candidate_names:
                    if cand in [c[0] for c in columns_info]:
                        time_column = cand
                        break

            where_clauses = []
            if time_column:
                if start_time:
                    where_clauses.append(f"{time_column} >= '{start_time}'")
                if end_time:
                    where_clauses.append(f"{time_column} <= '{end_time}'")
            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            query_sql = f"SELECT * FROM {database}.{table} {where_sql} LIMIT {limit}"

            result = await client.execute(
                query_sql,
                with_column_types=True,
            )
            rows, column_types = result
            columns = [col[0] for col in column_types]

            content = f"# Sample data from {database}.{table}\n\n"
            if time_column and (start_time or end_time):
                content += f"**Time filter column**: `{time_column}`"
                if start_time:
                    content += f", **Start time**: `{start_time}`"
                if end_time:
                    content += f", **End time**: `{end_time}`"
                content += "\n\n"
            content += "| " + " | ".join(columns) + " |\n"
            content += "| " + " | ".join(["---" for _ in columns]) + " |\n"
            for row in rows:
                content += "| " + " | ".join(str(val) for val in row) + " |\n"
            logger.info(
                "Returned table sample", database=database, table=table, rows=len(rows)
            )
            return content
        except Exception as e:
            logger.error(
                "Error getting table sample",
                database=database,
                table=table,
                error=str(e),
            )
            return f"Error getting sample data for {database}.{table}: {str(e)}"

    @server.resource(
        "resource://data/{database}/{table}/count?start_time={start_time}&end_time={end_time}&time_column={time_column}",
        title="Table Row Count (with time filter)",
    )
    async def table_count(
        database: str,
        table: str,
        start_time: str = None,
        end_time: str = None,
        time_column: str = None,
    ) -> str:
        """
        Get table row count, with optional time range filtering.

        :param database: Database name
        :param table: Table name
        :param start_time: Start time (optional, ISO8601 string)
        :param end_time: End time (optional, ISO8601 string)
        :param time_column: Time column name (optional, auto-detects common fields by default)
        """
        try:
            databases = await client.get_databases()
            if database not in databases:
                logger.warning("Database not found", database=database)
                return f"Database '{database}' not found"
            tables = await client.get_tables(database=database)
            if table not in tables:
                logger.warning("Table not found", database=database, table=table)
                return f"Table '{database}.{table}' not found"

            # Time column inference
            if time_column is None:
                columns_info = await client.get_columns(database=database, table=table)
                candidate_names = [
                    "event_time",
                    "created_at",
                    "timestamp",
                    "ts",
                    "time",
                ]
                for cand in candidate_names:
                    if cand in [c[0] for c in columns_info]:
                        time_column = cand
                        break

            where_clauses = []
            if time_column:
                if start_time:
                    where_clauses.append(f"{time_column} >= '{start_time}'")
                if end_time:
                    where_clauses.append(f"{time_column} <= '{end_time}'")
            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            query_sql = f"SELECT count() FROM {database}.{table} {where_sql}"

            result = await client.execute(query_sql)
            count = result[0][0]
            content = f"# Row count for {database}.{table}\n\n"
            if time_column and (start_time or end_time):
                content += f"**Time filter column**: `{time_column}`"
                if start_time:
                    content += f", **Start time**: `{start_time}`"
                if end_time:
                    content += f", **End time**: `{end_time}`"
                content += "\n\n"
            content += f"Total rows: **{count}**\n"
            logger.info(
                "Returned table count", database=database, table=table, count=count
            )
            return content
        except Exception as e:
            logger.error(
                "Error getting table count",
                database=database,
                table=table,
                error=str(e),
            )
            return f"Error getting row count for {database}.{table}: {str(e)}"

    logger.info("Registered ClickHouse data resources")
