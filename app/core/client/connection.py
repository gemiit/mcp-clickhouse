"""ClickHouse connection module for MCP ClickHouse Server.

This module provides a connection class for interacting with ClickHouse databases.
It handles connection establishment, query execution, and result formatting.

Examples:
    Basic usage:

    >>> from app.core.client.connection import ClickHouseConnection
    >>> conn = ClickHouseConnection(host="localhost", port=9000)
    >>> conn.connect()
    >>> result = conn.execute("SELECT 1")
    >>> print(result)
    >>> conn.disconnect()
"""

import time
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from clickhouse_driver import Client as SyncClient
from pydantic import SecretStr

from app.core.client.formats import ResultFormat
from app.utils.logging import get_logger, time_request

# Initialize logger
logger = get_logger(__name__)


class ClickHouseConnection:
    """A single connection to a ClickHouse server."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: SecretStr,
        database: str = "default",
        secure: bool = False,
        verify: bool = True,
        ca_cert: Optional[str] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        connect_timeout: int = 10,
        compression: bool = True,
    ):
        """Initialize a ClickHouse connection.

        Args:
            host: ClickHouse server hostname or IP address
            port: ClickHouse server port
            user: Username for authentication
            password: Password for authentication
            database: Default database to use
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
        self.password = password.get_secret_value() if password else ""
        self.database = database
        self.secure = secure
        self.verify = verify
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        self.connect_timeout = connect_timeout
        self.compression = compression

        self._client: Optional[SyncClient] = None
        self._in_use: bool = False
        self._last_used: float = 0.0

    @property
    def is_connected(self) -> bool:
        """Check if the connection is established.

        Returns:
            True if connected, False otherwise
        """
        return self._client is not None

    @property
    def is_in_use(self) -> bool:
        """Check if the connection is currently in use.

        Returns:
            True if in use, False otherwise
        """
        return self._in_use

    @property
    def last_used(self) -> float:
        """Get the timestamp of when the connection was last used.

        Returns:
            Timestamp in seconds since the epoch
        """
        return self._last_used

    def connect(self) -> None:
        """Establish a connection to the ClickHouse server.

        Raises:
            ClickHouseError: If the connection fails
        """
        logger.debug(
            "Connecting to ClickHouse",
            host=self.host,
            port=self.port,
            user=self.user,
            database=self.database,
            secure=self.secure,
        )

        # Create SSL context if using secure connection
        ssl_options = {}
        if self.secure:
            ssl_options = {
                "verify": self.verify,
                "ca_certs": self.ca_cert,
                "keyfile": self.client_key,
                "certfile": self.client_cert,
            }

        # Create client
        self._client = SyncClient(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            connect_timeout=self.connect_timeout,
            compression=self.compression,
            secure=self.secure,
            **ssl_options,
        )

        # Test connection
        try:
            self._client.execute("SELECT 1")
            logger.debug(
                "Connected to ClickHouse",
                host=self.host,
                port=self.port,
                database=self.database,
            )
        except Exception as e:
            self._client = None
            logger.error(
                "Failed to connect to ClickHouse",
                host=self.host,
                port=self.port,
                database=self.database,
                error=str(e),
            )
            raise

    def disconnect(self) -> None:
        """Disconnect from the ClickHouse server."""
        if self._client:
            logger.debug(
                "Disconnecting from ClickHouse",
                host=self.host,
                port=self.port,
                database=self.database,
            )
            self._client = None

    def execute(
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
        if not self._client:
            self.connect()

        try:
            self._in_use = True
            with time_request(logger, f"ClickHouse query: {query[:100]}"):
                result = self._client.execute(
                    query,
                    params=params,
                    with_column_types=with_column_types,
                    query_id=query_id,
                    settings=settings,
                )
            self._last_used = time.time()
            return result
        except Exception as e:
            logger.error(
                "Query execution failed",
                query=query,
                params=params,
                error=str(e),
            )
            raise
        finally:
            self._in_use = False

    def execute_with_format(
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
        if not self._client:
            self.connect()

        # Add FORMAT clause if not already present
        if "FORMAT" not in query.upper():
            query = f"{query} FORMAT {format_name.value}"

        try:
            self._in_use = True
            with time_request(logger, f"ClickHouse formatted query: {query[:100]}"):
                result = self._client.execute(
                    query,
                    params=params,
                    query_id=query_id,
                    settings=settings,
                )
            self._last_used = time.time()
            return result
        except Exception as e:
            logger.error(
                "Formatted query execution failed",
                query=query,
                format=format_name.value,
                params=params,
                error=str(e),
            )
            raise
        finally:
            self._in_use = False

    def execute_iter(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        query_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Tuple]:
        """Execute a SQL query and return an iterator over the results.

        Args:
            query: SQL query to execute
            params: Parameters for the query
            query_id: Query ID for tracing
            settings: ClickHouse settings for the query

        Returns:
            Iterator over query results

        Raises:
            ClickHouseError: If the query fails
        """
        if not self._client:
            self.connect()

        try:
            self._in_use = True
            with time_request(logger, f"ClickHouse iter query: {query[:100]}"):
                result = self._client.execute_iter(
                    query,
                    params=params,
                    query_id=query_id,
                    settings=settings,
                )
                for row in result:
                    yield row
            self._last_used = time.time()
        except Exception as e:
            logger.error(
                "Iterator query execution failed",
                query=query,
                params=params,
                error=str(e),
            )
            raise
        finally:
            self._in_use = False
