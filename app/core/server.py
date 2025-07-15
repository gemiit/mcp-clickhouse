"""Core server module for ClickHouse integration with MCP.

This module provides the core ClickHouseServer class for integrating ClickHouse
databases with the Model Context Protocol (MCP). It uses FastMCP's native
configuration system (FASTMCP_* environment variables) for simplified setup.

The server automatically configures itself from environment variables and provides
methods for registering tools and resources. It supports multiple transport protocols
including streamable-http, sse, and stdio.

Examples:
    Basic usage with environment variables:

    >>> from app.core.server import ClickHouseServer
    >>> server = ClickHouseServer()
    >>> server.run()

    With custom ClickHouse settings:

    >>> server = ClickHouseServer(
    ...     name="Production ClickHouse",
    ...     host="clickhouse.example.com",
    ...     port=9000,
    ... )
    >>> server.run(transport="streamable-http")

    FastMCP configuration is handled via FASTMCP_* environment variables:
    - FASTMCP_HOST: Host to bind to
    - FASTMCP_PORT: Port to bind to
    - FASTMCP_MOUNT_PATH: Mount path for HTTP transport
    - FASTMCP_DEBUG: Enable debug mode
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Response
from mcp.server import FastMCP
from pydantic import SecretStr

from app.core.client import ClickHouseClient

from app.utils.config import settings
from app.utils.logging import get_logger

# Initialize logger
# Initialize logger
logger = get_logger(__name__)


class ClickHouseServer:
    """MCP server for ClickHouse integration."""

    def __init__(
        self,
        name: str = settings.app_name,
        host: str = settings.clickhouse.host,
        port: int = settings.clickhouse.port,
        user: str = settings.clickhouse.user,
        password: SecretStr = settings.clickhouse.password,
        database: str = settings.clickhouse.database,
        secure: bool = settings.clickhouse.secure,
        verify: bool = settings.clickhouse.verify,
        ca_cert: Optional[str] = settings.clickhouse.ca_cert,
        client_cert: Optional[str] = settings.clickhouse.client_cert,
        client_key: Optional[str] = settings.clickhouse.client_key,
        pool_size: int = 5,
        query_timeout: int = settings.clickhouse.query_timeout,
        temp_dir: str = str(settings.temp_dir),
        metrics_enabled: bool = settings.metrics.enabled,
        metrics_path: str = settings.metrics.path,
        tracing_enabled: bool = settings.tracing.enabled,
        tracing_exporter_endpoint: Optional[str] = settings.tracing.otlp_endpoint,
    ):
        """Initialize the ClickHouse server.

        Args:
            name: Server name displayed to clients
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
            pool_size: Maximum number of connections in the pool
            query_timeout: Query timeout in seconds
            temp_dir: Directory for temporary files
            metrics_enabled: Whether to enable Prometheus metrics
            metrics_path: Path for Prometheus metrics endpoint
            tracing_enabled: Whether to enable OpenTelemetry tracing
            tracing_exporter_endpoint: OpenTelemetry exporter endpoint
        """
        self.name = name
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.secure = secure
        self.verify = verify
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.client_key = client_key
        self.pool_size = pool_size
        self.query_timeout = query_timeout
        self.temp_dir = temp_dir
        self.metrics_enabled = metrics_enabled
        self.metrics_path = metrics_path
        self.tracing_enabled = tracing_enabled
        self.tracing_exporter_endpoint = tracing_exporter_endpoint

        # ------------------------------------------------------------------ #
        # Create FastMCP server instance (simplified)                       #
        # ------------------------------------------------------------------ #
        # FastMCP reads its configuration from FASTMCP_* environment variables.
        # No need to pass explicit kwargs since we use FastMCP's native config.
        self.mcp_server = FastMCP(
            name=self.name,
        )

        # Initialize ClickHouse client
        self.client = ClickHouseClient(
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
            pool_size=self.pool_size,
            query_timeout=self.query_timeout,
        )

        # Create temporary directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)

    def setup_metrics(self, app: FastAPI) -> None:
        """Set up Prometheus metrics for the FastAPI app.

        Args:
            app: FastAPI application instance
        """
        if not self.metrics_enabled:
            logger.info("Metrics disabled")
            return

        logger.info("Setting up metrics", path=self.metrics_path)

        try:
            from prometheus_client import (
                REGISTRY,
                Counter,
                Gauge,
                Histogram,
                generate_latest,
            )

            # Define metrics
            REQUEST_COUNT = Counter(
                "mcp_clickhouse_requests_total",
                "Total number of requests",
                ["method", "endpoint", "status"],
            )

            REQUEST_TIME = Histogram(
                "mcp_clickhouse_request_duration_seconds",
                "Request duration in seconds",
                ["method", "endpoint"],
            )

            QUERIES_TOTAL = Counter(
                "mcp_clickhouse_queries_total",
                "Total number of ClickHouse queries",
                ["database", "status"],
            )

            QUERY_TIME = Histogram(
                "mcp_clickhouse_query_duration_seconds",
                "Query duration in seconds",
                ["database"],
            )

            CONNECTIONS_ACTIVE = Gauge(
                "mcp_clickhouse_connections_active",
                "Number of active ClickHouse connections",
            )

            # Add metrics endpoint
            @app.get(self.metrics_path)
            async def metrics():
                return Response(
                    content=generate_latest(REGISTRY),
                    media_type="text/plain",
                )

            # Add middleware to collect request metrics
            @app.middleware("http")
            async def metrics_middleware(request: Request, call_next):
                start_time = time.time()

                # Process request
                response = await call_next(request)

                # Record metrics
                duration = time.time() - start_time
                REQUEST_TIME.labels(
                    method=request.method,
                    endpoint=request.url.path,
                ).observe(duration)

                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code,
                ).inc()

                return response

            # Store metrics in app state for use in tool handlers
            app.state.metrics = {
                "queries_total": QUERIES_TOTAL,
                "query_time": QUERY_TIME,
                "connections_active": CONNECTIONS_ACTIVE,
            }

            logger.info("Metrics setup complete")
        except ImportError as e:
            logger.error(
                "Metrics setup failed: required packages not installed",
                error=str(e),
            )
            raise

    def setup_tracing(self, app: FastAPI) -> None:
        """Set up OpenTelemetry tracing for the FastAPI app.

        Args:
            app: FastAPI application instance
        """
        if not self.tracing_enabled:
            logger.info("Tracing disabled")
            return

        logger.info(
            "Setting up tracing",
            exporter_endpoint=self.tracing_exporter_endpoint,
        )

        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            # Set up tracer provider
            resource = Resource(attributes={SERVICE_NAME: self.name})
            tracer_provider = TracerProvider(resource=resource)

            # Set up exporter
            exporter = OTLPSpanExporter(endpoint=self.tracing_exporter_endpoint)
            span_processor = BatchSpanProcessor(exporter)
            tracer_provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(tracer_provider)

            # Instrument FastAPI
            FastAPIInstrumentor.instrument_app(app)

            logger.info("Tracing setup complete")
        except ImportError as e:
            logger.error(
                "Tracing setup failed: required packages not installed",
                error=str(e),
            )
            raise

    def setup_health_check(self, app: FastAPI) -> None:
        """Set up health check endpoint for the FastAPI app.

        Args:
            app: FastAPI application instance
        """
        logger.info("Setting up health check endpoint")

        @app.get("/health")
        async def health_check():
            try:
                # Check ClickHouse connection
                result = await self.client.execute("SELECT 1")
                if result != [(1,)]:
                    raise ValueError("Unexpected result from ClickHouse")

                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    # NOTE: mcp package does not expose __version__, so we
                    #       use the pinned version from pyproject.toml.
                    "version": "1.10.1",
                    "clickhouse": {
                        "host": self.host,
                        "port": self.port,
                        "database": self.database,
                        "status": "connected",
                    },
                }
            except Exception as e:
                logger.error("Health check failed", error=str(e))
                return Response(
                    status_code=500,
                    content=json.dumps(
                        {
                            "status": "unhealthy",
                            "timestamp": datetime.utcnow().isoformat(),
                            "error": str(e),
                        }
                    ),
                    media_type="application/json",
                )

    def register_tools(self) -> None:
        """Register MCP tools for ClickHouse operations.

        This method should be overridden by subclasses to register specific tools.
        The actual tool implementations will be defined in the api package.
        """
        pass

    def register_resources(self) -> None:
        """Register MCP resources for ClickHouse data access.

        This method should be overridden by subclasses to register specific resources.
        The actual resource implementations will be defined in the api package.
        """
        pass

    def setup(self) -> FastAPI:
        """Set up the FastAPI application with MCP server and middleware.

        Returns:
            The configured FastAPI application
        """
        # Create FastAPI app
        # NOTE: FastMCP now exposes `streamable_http_app()` to obtain the underlying
        # FastAPI application instance instead of `get_app()`.
        app = self.mcp_server.streamable_http_app()

        # Set up metrics
        self.setup_metrics(app)

        # Set up tracing
        self.setup_tracing(app)

        # Set up health check
        self.setup_health_check(app)

        # Register tools and resources
        self.register_tools()
        self.register_resources()

        return app

    def run(
        self,
        transport: str = "streamable-http",
    ) -> None:
        """Run the MCP server with the specified transport.

        Args:
            transport: Transport protocol to use (streamable-http, sse, stdio)
            host: Host to bind to
            port: Port to bind to
            mount_path: Path to mount the MCP server at
        """
        logger.info(
            "Starting MCP ClickHouse server", name=self.name, transport=transport
        )

        # Register tools & resources before the server starts
        self.register_tools()
        self.register_resources()

        # Run the server with the specified transport using the new async helpers
        # NOTE:
        # `*_async` helpers return **coroutines** — they must be awaited.
        # Since `run()` is a synchronous entry-point (invoked from Typer CLI),
        # we execute the coroutine via `asyncio.run(...)` to ensure it is
        # awaited and to avoid “coroutine was never awaited” warnings.
        if transport == "streamable-http":
            asyncio.run(self.mcp_server.run_streamable_http_async())
        elif transport == "sse":
            # SSE helper only requires the mount path
            asyncio.run(self.mcp_server.run_sse_async())
        elif transport == "stdio":
            asyncio.run(self.mcp_server.run_stdio_async())
        else:
            raise ValueError(f"Unsupported transport: {transport}")

    async def shutdown(self) -> None:
        """Shut down the server and clean up resources."""
        logger.info("Shutting down MCP ClickHouse server")

        # Close ClickHouse client
        await self.client.close()
