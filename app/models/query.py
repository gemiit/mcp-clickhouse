"""Query data models for MCP ClickHouse Server.

This module provides data models for query execution and data insertion operations.
These models are used by the query tools to validate input parameters and provide
type hints for IDE integration.

Examples:
    Creating a query parameter object:

    >>> from app.models.query import QueryParams
    >>> params = QueryParams(sql="SELECT * FROM my_table", format="json")
    >>> print(params.sql)
    SELECT * FROM my_table

    Creating an insert parameter object:

    >>> from app.models.query import InsertParams
    >>> data = [{"id": 1, "name": "test"}]
    >>> params = InsertParams(table="my_table", data=data)
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


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
