"""Schema data models for MCP ClickHouse Server.

This module provides data models for database schema operations such as
creating databases and tables. These models are used by the
schema tools to validate input parameters and provide type hints for IDE integration.

Examples:
    Creating a database parameter object:

    >>> from app.models.schema import CreateDatabaseParams
    >>> params = CreateDatabaseParams(name="my_database", if_not_exists=True)
    >>> print(params.name)
    my_database

    Creating a table parameter object:

    >>> from app.models.schema import CreateTableParams, ColumnDefinition
    >>> columns = [
    ...     ColumnDefinition(name="id", type="UInt32"),
    ...     ColumnDefinition(name="name", type="String")
    ... ]
    >>> params = CreateTableParams(
    ...     name="my_table",
    ...     columns=columns,
    ...     engine="MergeTree()",
    ...     order_by="id"
    ... )
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


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
