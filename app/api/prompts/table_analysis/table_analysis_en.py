"""Table analysis prompt handler."""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient
from app.utils.logging import get_logger

logger = get_logger(__name__)


# English version prompt template
TABLE_ANALYSIS_PROMPT_TEMPLATE_EN = """Please analyze the ClickHouse table '{database}.{table}' and provide insights and optimization recommendations.

{schema_info}{stats_info}

Please provide analysis on:

1. **Schema Design**: 
   - Are the data types optimal for the use case?
   - Are there any redundant or missing columns?
   - Is the table structure normalized appropriately for ClickHouse?

2. **Performance Optimization**:
   - Recommend optimal table engine if not already using the best one
   - Suggest appropriate ORDER BY clause for query patterns
   - Recommend PARTITION BY strategy if applicable
   - Identify potential indexes or projections that could help

3. **Storage Optimization**:
   - Analyze compression ratios and suggest improvements
   - Recommend data retention policies if applicable
   - Suggest archival strategies for old data

4. **Query Patterns**:
   - Identify common query patterns that would work well with this schema
   - Suggest materialized views for complex aggregations
   - Recommend query optimization techniques

Please provide specific, actionable recommendations with example SQL statements where applicable."""


def register_table_analysis_prompt_en(
    server: FastMCP, client: ClickHouseClient
) -> None:
    """Register table analysis prompt (English version) with the MCP server."""

    @server.prompt(
        name="analyze_table_en",
        title="Analyze Table Structure",
        description="Analyze ClickHouse table structure, data distribution, and suggest optimizations",
    )
    async def analyze_table_en(
        database: str, table: str, sample_size: str = "1000"
    ) -> List[Dict[str, Any]]:
        """
        Generate table analysis prompt (English version)

        Args:
            database: Database name containing the table
            table: Table name to analyze
            sample_size: Number of sample rows to analyze (optional, default: 1000)

        Returns:
            List of messages containing table analysis prompt
        """

        # Get table schema information
        try:
            # Get table structure
            schema_query = f"""
            SELECT 
                name,
                type,
                default_kind,
                default_expression,
                comment
            FROM system.columns 
            WHERE database = '{database}' AND table = '{table}'
            ORDER BY position
            """
            schema_result = await client.execute(schema_query, with_column_types=True)

            # Get table statistics
            stats_query = f"""
            SELECT 
                count() as total_rows,
                formatReadableSize(sum(data_compressed_bytes)) as compressed_size,
                formatReadableSize(sum(data_uncompressed_bytes)) as uncompressed_size
            FROM system.parts 
            WHERE database = '{database}' AND table = '{table}' AND active = 1
            """
            stats_result = await client.execute(stats_query)

            # Format schema information
            schema_info = "Table Schema:\n"
            for row in schema_result[0]:
                name, type_, default_kind, default_expr, comment = row
                schema_info += f"- {name}: {type_}"
                if default_kind:
                    schema_info += f" (default: {default_kind}"
                    if default_expr:
                        schema_info += f" {default_expr}"
                    schema_info += ")"
                if comment:
                    schema_info += f" -- {comment}"
                schema_info += "\n"

            # Format statistics
            if stats_result and len(stats_result) > 0:
                total_rows, compressed_size, uncompressed_size = stats_result[0]
                stats_info = f"\nTable Statistics:\n- Total rows: {total_rows:,}\n- Compressed size: {compressed_size}\n- Uncompressed size: {uncompressed_size}\n"
            else:
                stats_info = "\nTable Statistics: No data available\n"

        except Exception as e:
            logger.warning(f"Failed to get table information: {e}")
            schema_info = f"Unable to retrieve schema for {database}.{table}"
            stats_info = ""

        # Use the template to generate prompt content
        prompt_content = TABLE_ANALYSIS_PROMPT_TEMPLATE_EN.format(
            database=database,
            table=table,
            schema_info=schema_info,
            stats_info=stats_info,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return analyze_table_en
