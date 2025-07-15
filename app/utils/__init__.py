"""Utilities package for MCP ClickHouse Server.

This package provides utility functions and classes for the MCP ClickHouse Server,
including configuration management, logging, and metrics collection.

Examples:
    Import utilities directly from the package:

    >>> from app.utils import settings, configure_logging, get_logger, setup_metrics
    >>> configure_logging()
    >>> logger = get_logger(__name__)
    >>> setup_metrics(app)
"""

# Configuration utilities
from app.utils.config import settings

# Logging utilities
from app.utils.logging import (
    configure_logging,
    get_logger,
    time_request,
)

# Metrics utilities
from app.utils.metrics import (
    get_metrics,
    setup_metrics,
    increment_query_count,
    observe_query_duration,
    set_active_connections,
    increment_connection_errors,
    add_processed_bytes,
    QueryTimer,
)

__all__ = [
    # Configuration
    "settings",
    # Logging
    "configure_logging",
    "get_logger",
    "time_request",
    # Metrics
    "get_metrics",
    "setup_metrics",
    "increment_query_count",
    "observe_query_duration",
    "set_active_connections",
    "increment_connection_errors",
    "add_processed_bytes",
    "QueryTimer",
]
