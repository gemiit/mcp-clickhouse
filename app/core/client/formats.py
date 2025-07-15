"""ClickHouse result formats module for MCP ClickHouse Server.

This module defines the supported result formats for ClickHouse queries.

Examples:
    Basic usage:

    >>> from app.core.client.formats import ResultFormat
    >>> format = ResultFormat.JSON
    >>> print(format)
    json
"""

from enum import Enum


class ResultFormat(str, Enum):
    """Supported result formats for ClickHouse queries."""

    JSON = "json"
    JSON_COMPACT = "JSONCompact"
    PRETTY = "Pretty"
    CSV = "CSV"
    TSV = "TSV"
    PARQUET = "Parquet"
    ARROW = "Arrow"
    NATIVE = "Native"
    NULL = "Null"
