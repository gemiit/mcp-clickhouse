"""Schema design prompt handler."""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient


# English version prompt template
SCHEMA_DESIGN_PROMPT_TEMPLATE_EN = """Please help design an optimal ClickHouse database schema for the following use case:

**Use Case**: {use_case}

{data_volume_section}

{query_patterns_section}

Please provide a comprehensive schema design including:

1. **Table Structure**:
   - Recommend table names and column definitions
   - Choose optimal data types for ClickHouse
   - Design appropriate primary keys

2. **Table Engine Selection**:
   - Recommend the best table engine (MergeTree family)
   - Justify the choice based on use case requirements
   - Configure engine-specific parameters

3. **Partitioning Strategy**:
   - Design PARTITION BY clause if needed
   - Recommend partition granularity
   - Consider data retention and cleanup

4. **Ordering and Indexing**:
   - Design optimal ORDER BY clause
   - Recommend secondary indexes if needed
   - Consider skip indexes for specific columns

5. **Performance Considerations**:
   - Optimize for expected query patterns
   - Consider materialized views for aggregations
   - Plan for data ingestion patterns

6. **Scalability Planning**:
   - Design for expected data growth
   - Consider sharding strategies if needed
   - Plan for backup and replication

Please provide complete CREATE TABLE statements with explanations for each design decision."""


def register_schema_design_prompt_en(server: FastMCP, client: ClickHouseClient) -> None:
    """Register schema design prompt (English version) with the MCP server."""

    @server.prompt(
        name="design_schema_en",
        title="Design Database Schema",
        description="Help design optimal ClickHouse database schema for specific use cases",
    )
    def design_schema_en(
        use_case: str, data_volume: str = "", query_patterns: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate schema design prompt (English version)

        Args:
            use_case: Description of the use case and data requirements
            data_volume: Expected data volume (optional, e.g., '1M rows/day', '100GB/month')
            query_patterns: Common query patterns and access patterns (optional)

        Returns:
            List of messages containing schema design prompt
        """

        # Process parameters and build sections
        data_volume_section = (
            f"**Expected Data Volume**: {data_volume}" if data_volume else ""
        )
        query_patterns_section = (
            f"**Query Patterns**: {query_patterns}" if query_patterns else ""
        )

        # Use the template to generate prompt content
        prompt_content = SCHEMA_DESIGN_PROMPT_TEMPLATE_EN.format(
            use_case=use_case,
            data_volume_section=data_volume_section,
            query_patterns_section=query_patterns_section,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return design_schema_en
