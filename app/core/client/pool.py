"""ClickHouse connection pool and client module for MCP ClickHouse Server.

This module provides connection pooling and client classes for interacting with ClickHouse databases.
It handles connection management, query execution, and result formatting.

Examples:
    Basic usage:

    >>> from app.core.client.pool import ClickHouseClient
    >>> client = ClickHouseClient(host="localhost", port=9000)
    >>> result = await client.execute("SELECT 1")
    >>> print(result)
    >>> await client.close()

    With connection pooling:

    >>> client = ClickHouseClient(host="localhost", port=9000, pool_size=5)
    >>> async with client.connection() as conn:
    >>>     result = await conn.execute("SELECT 1")
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple, Union

from clickhouse_driver.errors import Error as ClickHouseError
from pydantic import SecretStr
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.client.connection import ClickHouseConnection
from app.core.client.formats import ResultFormat
from app.utils.config import settings
from app.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class ClickHouseConnectionPool:
    """A pool of ClickHouse connections."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: SecretStr,
        database: str = "default",
        pool_size: int = 5,
        pool_recycle: int = 3600,
        secure: bool = False,
        verify: bool = True,
        ca_cert: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        connect_timeout: int = 10,
        compression: bool = True,
    ):
        """Initialize a ClickHouse connection pool.

        Args:
            host: ClickHouse server hostname or IP address
            port: ClickHouse server port
            user: Username for authentication
            password: Password for authentication
            database: Default database to use
            pool_size: Maximum number of connections in the pool
            pool_recycle: Time in seconds after which a connection is recycled
            secure: Whether to use TLS/SSL
            verify: Whether to verify TLS/SSL certificates
            ca_cert: Path to CA certificate file
            client_cert: Path to client certificate file
            client_key: Path to client key file
            connect_timeout: Connection timeout in seconds
            compression: Whether to use compression
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.pool_size = pool_size
        self.pool_recycle = pool_recycle
        self.secure = secure
        self.verify = verify
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        self.connect_timeout = connect_timeout
        self.compression = compression

        self._pool: List[ClickHouseConnection] = []
        self._lock = asyncio.Lock()

    async def _create_connection(self) -> ClickHouseConnection:
        """Create a new ClickHouse connection.

        Returns:
            A new ClickHouseConnection instance
        """
        conn = ClickHouseConnection(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            secure=self.secure,
            verify=self.verify,
            ca_cert=self.ca_cert,
            client_cert=self.client_cert,
            client_key=self.client_key,
            connect_timeout=self.connect_timeout,
            compression=self.compression,
        )
        conn.connect()
        return conn

    async def get_connection(self) -> ClickHouseConnection:
        """Get a connection from the pool.

        If there are no available connections and the pool is not full,
        a new connection is created. If the pool is full, this method
        waits for a connection to become available.

        Returns:
            A ClickHouseConnection instance
        """
        async with self._lock:
            # Try to find an existing connection that is not in use
            for conn in self._pool:
                if not conn.is_in_use:
                    # Check if the connection needs to be recycled
                    if time.time() - conn.last_used > self.pool_recycle:
                        logger.debug("Recycling connection")
                        conn.disconnect()
                        self._pool.remove(conn)
                        break

                    # Mark the connection as in use
                    conn._in_use = True
                    return conn

            # If we get here, either all connections are in use or
            # there are no connections in the pool
            if len(self._pool) < self.pool_size:
                # Create a new connection
                logger.debug(
                    "Creating new connection",
                    pool_size=len(self._pool),
                    max_pool_size=self.pool_size,
                )
                conn = await self._create_connection()
                conn._in_use = True
                self._pool.append(conn)
                return conn

            # If we get here, the pool is full and all connections are in use
            # Wait for a connection to become available
            logger.debug(
                "Waiting for connection to become available",
                pool_size=len(self._pool),
                max_pool_size=self.pool_size,
            )
            while True:
                for conn in self._pool:
                    if not conn.is_in_use:
                        conn._in_use = True
                        return conn
                await asyncio.sleep(0.1)

    @asynccontextmanager
    async def connection(self):
        """Get a connection from the pool as an async context manager.

        Example:
            >>> async with pool.connection() as conn:
            >>>     result = await conn.execute("SELECT 1")

        Yields:
            A ClickHouseConnection instance
        """
        conn = await self.get_connection()
        try:
            yield conn
        finally:
            conn._in_use = False

    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        with_column_types: bool = False,
        query_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Union[List[Tuple], Tuple[List[Tuple], List[Tuple[str, str]]]]:
        """Execute a SQL query on the ClickHouse server.

        Args:
            query: SQL query to execute
            params: Parameters for the query
            with_column_types: Whether to return column types
            query_id: Query ID for tracing
            settings: ClickHouse settings for the query

        Returns:
            Query results, optionally with column types

        Raises:
            ClickHouseError: If the query fails
        """
        async with self.connection() as conn:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    query=query,
                    params=params,
                    with_column_types=with_column_types,
                    query_id=query_id,
                    settings=settings,
                ),
            )

    async def execute_with_format(
        self,
        query: str,
        format_name: ResultFormat,
        params: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute a SQL query and return the result in a specific format.

        Args:
            query: SQL query to execute
            format_name: Result format
            params: Parameters for the query
            query_id: Query ID for tracing
            settings: ClickHouse settings for the query

        Returns:
            Query results in the specified format

        Raises:
            ClickHouseError: If the query fails
        """
        async with self.connection() as conn:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute_with_format(
                    query=query,
                    format_name=format_name,
                    params=params,
                    query_id=query_id,
                    settings=settings,
                ),
            )

    async def close(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            for conn in self._pool:
                conn.disconnect()
            self._pool = []


class ClickHouseClient:
    """A client for interacting with ClickHouse databases."""

    def __init__(
        self,
        host: str = settings.clickhouse.host,
        port: int = settings.clickhouse.port,
        user: str = settings.clickhouse.user,
        password: SecretStr = settings.clickhouse.password,
        database: str = settings.clickhouse.database,
        pool_size: int = 5,  # Default pool size
        pool_recycle: int = 3600,  # Default pool recycle time (1 hour)
        query_timeout: int = settings.clickhouse.query_timeout,
        secure: bool = settings.clickhouse.secure,
        verify: bool = settings.clickhouse.verify,
        ca_cert: Optional[str] = settings.clickhouse.ca_cert,
        client_cert: Optional[str] = settings.clickhouse.client_cert,
        client_key: Optional[str] = settings.clickhouse.client_key,
        connect_timeout: int = settings.clickhouse.connect_timeout,
        compression: bool = settings.clickhouse.compression,
    ):
        """Initialize a ClickHouse client.

        Args:
            host: ClickHouse server hostname or IP address
            port: ClickHouse server port
            user: Username for authentication
            password: Password for authentication
            database: Default database to use
            pool_size: Maximum number of connections in the pool
            pool_recycle: Time in seconds after which a connection is recycled
            query_timeout: Query timeout in seconds
            secure: Whether to use TLS/SSL
            verify: Whether to verify TLS/SSL certificates
            ca_cert: Path to CA certificate file
            client_cert: Path to client certificate file
            client_key: Path to client key file
            connect_timeout: Connection timeout in seconds
            compression: Whether to use compression
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.pool_size = pool_size
        self.pool_recycle = pool_recycle
        self.query_timeout = query_timeout
        self.secure = secure
        self.verify = verify
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        self.connect_timeout = connect_timeout
        self.compression = compression

        self._pool = ClickHouseConnectionPool(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            pool_size=pool_size,
            pool_recycle=pool_recycle,
            secure=secure,
            verify=verify,
            ca_cert=ca_cert,
            client_cert=client_cert,
            client_key=client_key,
            connect_timeout=connect_timeout,
            compression=compression,
        )

    @property
    def connection(self):
        """Get a connection from the pool as an async context manager.

        Example:
            >>> async with client.connection() as conn:
            >>>     result = await conn.execute("SELECT 1")

        Returns:
            An async context manager that yields a ClickHouseConnection instance
        """
        return self._pool.connection()

    @retry(
        retry=retry_if_exception_type(ClickHouseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        with_column_types: bool = False,
        query_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Union[List[Tuple], Tuple[List[Tuple], List[Tuple[str, str]]]]:
        """Execute a SQL query on the ClickHouse server.

        Args:
            query: SQL query to execute
            params: Parameters for the query
            with_column_types: Whether to return column types
            query_id: Query ID for tracing
            settings: ClickHouse settings for the query

        Returns:
            Query results, optionally with column types

        Raises:
            ClickHouseError: If the query fails after retries
        """
        # Add query timeout setting if not provided
        if settings is None:
            settings = {}
        if "max_execution_time" not in settings:
            settings["max_execution_time"] = self.query_timeout

        return await self._pool.execute(
            query=query,
            params=params,
            with_column_types=with_column_types,
            query_id=query_id,
            settings=settings,
        )

    @retry(
        retry=retry_if_exception_type(ClickHouseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def execute_with_format(
        self,
        query: str,
        format_name: ResultFormat,
        params: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute a SQL query and return the result in a specific format.

        Args:
            query: SQL query to execute
            format_name: Result format
            params: Parameters for the query
            query_id: Query ID for tracing
            settings: ClickHouse settings for the query

        Returns:
            Query results in the specified format

        Raises:
            ClickHouseError: If the query fails after retries
        """
        # Add query timeout setting if not provided
        if settings is None:
            settings = {}
        if "max_execution_time" not in settings:
            settings["max_execution_time"] = self.query_timeout

        return await self._pool.execute_with_format(
            query=query,
            format_name=format_name,
            params=params,
            query_id=query_id,
            settings=settings,
        )

    async def get_databases(self) -> List[str]:
        """Get a list of all databases on the ClickHouse server.

        Returns:
            A list of database names
        """
        result = await self.execute("SHOW DATABASES")
        return [row[0] for row in result]

    async def get_tables(self, database: Optional[str] = None) -> List[str]:
        """Get a list of all tables in a database.

        Args:
            database: Database name (defaults to the client's default database)

        Returns:
            A list of table names
        """
        db = database or self.database
        result = await self.execute(f"SHOW TABLES FROM {db}")
        return [row[0] for row in result]

    async def get_table_schema(
        self, table: str, database: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the schema of a table.

        Args:
            table: Table name
            database: Database name (defaults to the client's default database)

        Returns:
            A dictionary containing the table schema

        Raises:
            ClickHouseError: If the table does not exist
        """
        db = database or self.database

        # Get column information
        columns_result = await self.execute(
            f"DESCRIBE TABLE {db}.{table}",
            with_column_types=True,
        )

        # Get table information
        table_result = await self.execute(
            f"""
            SELECT
                engine,
                create_table_query,
                total_rows,
                total_bytes,
                comment
            FROM system.tables
            WHERE database = '{db}' AND name = '{table}'
            """,
        )

        if not table_result:
            raise ClickHouseError(f"Table {db}.{table} does not exist")

        # Extract column information
        columns = []
        for row in columns_result[0]:
            columns.append(
                {
                    "name": row[0],
                    "type": row[1],
                    "default_type": row[2],
                    "default_expression": row[3],
                    "comment": row[4],
                    "codec_expression": row[5],
                    "ttl_expression": row[6],
                }
            )

        # Extract table information
        engine, create_table_query, total_rows, total_bytes, comment = table_result[0]

        return {
            "database": db,
            "table": table,
            "engine": engine,
            "create_table_query": create_table_query,
            "total_rows": total_rows,
            "total_bytes": total_bytes,
            "comment": comment,
            "columns": columns,
        }

    async def insert_data(
        self,
        table: str,
        data: List[Dict[str, Any]],
        database: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Insert data into a table.

        Args:
            table: Table name
            data: List of dictionaries containing the data to insert
            database: Database name (defaults to the client's default database)
            settings: ClickHouse settings for the query

        Returns:
            A dictionary containing the result of the insert operation

        Raises:
            ClickHouseError: If the insert fails
        """
        if not data:
            return {
                "database": database or self.database,
                "table": table,
                "rows_inserted": 0,
            }

        db = database or self.database

        # Extract column names from the first row
        columns = list(data[0].keys())

        # Extract values from all rows
        values = []
        for row in data:
            values.append([row.get(col) for col in columns])

        # Add query timeout setting if not provided
        if settings is None:
            settings = {}
        if "max_execution_time" not in settings:
            settings["max_execution_time"] = self.query_timeout

        # Execute insert query
        async with self.connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    f"INSERT INTO {db}.{table} ({', '.join(columns)}) VALUES",
                    params=values,
                    settings=settings,
                ),
            )

        return {
            "database": db,
            "table": table,
            "rows_inserted": len(data),
        }

    async def close(self) -> None:
        """Close all connections in the pool."""
        await self._pool.close()
