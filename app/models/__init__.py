"""Models package for MCP ClickHouse Server.

This package provides data models and schemas for the MCP ClickHouse Server.
Models are organized by functionality into separate modules:

- query: Models for query execution and data operations
- schema: Models for database schema operations

Examples:
    Import models from the package:

    >>> from app.models import CreateDatabaseParams, QueryParams
    >>> params = CreateDatabaseParams(name="my_database")
    >>> query = QueryParams(sql="SELECT 1")
"""

# Import models from submodules
from app.models.query import (
    QueryParams,
    InsertParams,
)
from app.models.schema import (
    CreateDatabaseParams,
    ColumnDefinition,
    CreateTableParams,
)

__all__ = [
    # Query models
    "QueryParams",
    "InsertParams",
    # Schema models
    "CreateDatabaseParams",
    "ColumnDefinition",
    "CreateTableParams",
]
