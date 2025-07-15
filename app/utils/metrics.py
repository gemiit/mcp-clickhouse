"""Metrics utilities for MCP ClickHouse Server.

This module provides utilities for collecting and exporting metrics from the
MCP ClickHouse Server. It uses Prometheus for metrics collection and export.

The module defines common metrics used throughout the application and provides
utility functions to simplify recording metrics.

Examples:
    Basic usage:

    >>> from app.utils.metrics import get_metrics, increment_query_count
    >>> metrics = get_metrics()
    >>> increment_query_count("default", "success")

    Using metrics in FastAPI:

    >>> from fastapi import FastAPI
    >>> app = FastAPI()
    >>> setup_metrics(app)
    >>> # Now metrics are available at /metrics
"""

import time
from typing import Dict, Any

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Summary,
        REGISTRY,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from app.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Define default metrics
_metrics: Dict[str, Any] = {}

# Define metric names and descriptions
METRIC_DEFINITIONS = {
    "requests_total": {
        "type": "counter",
        "name": "mcp_clickhouse_requests_total",
        "description": "Total number of requests",
        "labels": ["method", "endpoint", "status"],
    },
    "request_duration_seconds": {
        "type": "histogram",
        "name": "mcp_clickhouse_request_duration_seconds",
        "description": "Request duration in seconds",
        "labels": ["method", "endpoint"],
        "buckets": [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
    },
    "queries_total": {
        "type": "counter",
        "name": "mcp_clickhouse_queries_total",
        "description": "Total number of ClickHouse queries",
        "labels": ["database", "status"],
    },
    "query_duration_seconds": {
        "type": "histogram",
        "name": "mcp_clickhouse_query_duration_seconds",
        "description": "Query duration in seconds",
        "labels": ["database"],
        "buckets": [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60],
    },
    "connections_active": {
        "type": "gauge",
        "name": "mcp_clickhouse_connections_active",
        "description": "Number of active ClickHouse connections",
    },
    "connection_errors_total": {
        "type": "counter",
        "name": "mcp_clickhouse_connection_errors_total",
        "description": "Total number of ClickHouse connection errors",
        "labels": ["error_type"],
    },
    "data_bytes_processed": {
        "type": "counter",
        "name": "mcp_clickhouse_data_bytes_processed",
        "description": "Total number of bytes processed by ClickHouse queries",
        "labels": ["database", "operation"],
    },
}


def initialize_metrics() -> Dict[str, Any]:
    """Initialize Prometheus metrics based on definitions.

    Returns:
        Dictionary of initialized metrics
    """
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, metrics will be disabled")
        return {}

    metrics = {}

    for metric_id, definition in METRIC_DEFINITIONS.items():
        metric_type = definition["type"]
        name = definition["name"]
        description = definition["description"]
        labels = definition.get("labels", [])

        try:
            if metric_type == "counter":
                metrics[metric_id] = Counter(name, description, labels)
            elif metric_type == "gauge":
                metrics[metric_id] = Gauge(name, description, labels)
            elif metric_type == "histogram":
                buckets = definition.get("buckets")
                if buckets:
                    metrics[metric_id] = Histogram(
                        name, description, labels, buckets=buckets
                    )
                else:
                    metrics[metric_id] = Histogram(name, description, labels)
            elif metric_type == "summary":
                metrics[metric_id] = Summary(name, description, labels)
            else:
                logger.warning(f"Unknown metric type: {metric_type}")
        except Exception as e:
            logger.error(f"Failed to initialize metric {name}: {e}")

    logger.debug(f"Initialized {len(metrics)} metrics")
    return metrics


def get_metrics() -> Dict[str, Any]:
    """Get the metrics dictionary, initializing if necessary.

    Returns:
        Dictionary of metrics
    """
    global _metrics
    if not _metrics and PROMETHEUS_AVAILABLE:
        _metrics = initialize_metrics()
    return _metrics


def generate_metrics() -> bytes:
    """Generate Prometheus metrics output.

    Returns:
        Prometheus metrics in text format
    """
    if not PROMETHEUS_AVAILABLE:
        return b"# Prometheus metrics not available\n"

    # Ensure metrics are initialized
    get_metrics()

    try:
        return generate_latest(REGISTRY)
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return b"# Error generating metrics\n"


def setup_metrics(app: Any) -> None:
    """Set up metrics for a FastAPI application.

    Args:
        app: FastAPI application
    """
    if not PROMETHEUS_AVAILABLE:
        logger.warning(
            "Prometheus client not available, metrics endpoint will not be set up"
        )
        return

    # Initialize metrics
    metrics = get_metrics()

    # Store metrics in app state
    app.state.metrics = metrics

    # Add metrics middleware
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time

        try:
            if "request_duration_seconds" in metrics:
                metrics["request_duration_seconds"].labels(
                    method=request.method,
                    endpoint=request.url.path,
                ).observe(duration)

            if "requests_total" in metrics:
                metrics["requests_total"].labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code,
                ).inc()
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")

        return response

    # Add metrics endpoint
    from fastapi import Response

    @app.get("/metrics")
    async def metrics_endpoint():
        return Response(
            content=generate_metrics().decode("utf-8"),
            media_type="text/plain",
        )

    logger.info("Metrics endpoint set up at /metrics")


def increment_query_count(database: str, status: str) -> None:
    """Increment the query count metric.

    Args:
        database: Database name
        status: Query status (success, error)
    """
    metrics = get_metrics()
    if "queries_total" in metrics:
        try:
            metrics["queries_total"].labels(database=database, status=status).inc()
        except Exception as e:
            logger.error(f"Failed to increment query count: {e}")


def observe_query_duration(database: str, duration: float) -> None:
    """Record a query duration observation.

    Args:
        database: Database name
        duration: Query duration in seconds
    """
    metrics = get_metrics()
    if "query_duration_seconds" in metrics:
        try:
            metrics["query_duration_seconds"].labels(database=database).observe(
                duration
            )
        except Exception as e:
            logger.error(f"Failed to observe query duration: {e}")


def set_active_connections(count: int) -> None:
    """Set the number of active connections.

    Args:
        count: Number of active connections
    """
    metrics = get_metrics()
    if "connections_active" in metrics:
        try:
            metrics["connections_active"].set(count)
        except Exception as e:
            logger.error(f"Failed to set active connections: {e}")


def increment_connection_errors(error_type: str) -> None:
    """Increment the connection error count.

    Args:
        error_type: Type of connection error
    """
    metrics = get_metrics()
    if "connection_errors_total" in metrics:
        try:
            metrics["connection_errors_total"].labels(error_type=error_type).inc()
        except Exception as e:
            logger.error(f"Failed to increment connection errors: {e}")


def add_processed_bytes(database: str, operation: str, bytes_count: int) -> None:
    """Add the number of bytes processed.

    Args:
        database: Database name
        operation: Operation type (query, insert)
        bytes_count: Number of bytes processed
    """
    metrics = get_metrics()
    if "data_bytes_processed" in metrics:
        try:
            metrics["data_bytes_processed"].labels(
                database=database, operation=operation
            ).inc(bytes_count)
        except Exception as e:
            logger.error(f"Failed to add processed bytes: {e}")


class QueryTimer:
    """Context manager for timing queries and recording metrics.

    Examples:
        >>> with QueryTimer("default") as timer:
        ...     result = await client.execute("SELECT 1")
        >>> # Query duration is automatically recorded
    """

    def __init__(self, database: str):
        """Initialize the query timer.

        Args:
            database: Database name
        """
        self.database = database
        self.start_time = None
        self.status = "success"

    def __enter__(self):
        """Enter the context manager."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and record metrics.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if exc_type is not None:
            self.status = "error"

        duration = time.time() - self.start_time
        observe_query_duration(self.database, duration)
        increment_query_count(self.database, self.status)
