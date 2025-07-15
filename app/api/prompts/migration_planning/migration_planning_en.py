"""Migration planning prompt handler (English version)."""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient


# Define the prompt template
MIGRATION_PLANNING_PROMPT_TEMPLATE = """Please help plan a data migration from {source_system} to ClickHouse:

**Source System**: {source_system}

{data_size_section}

{requirements_section}

Please provide a comprehensive migration plan covering:

1. **Migration Strategy**:
   - Recommend migration approach (big bang vs. phased)
   - Identify migration tools and methods
   - Plan for data validation and testing

2. **Schema Mapping**:
   - Map source schema to optimal ClickHouse schema
   - Recommend data type conversions
   - Handle schema differences and constraints

3. **Data Extraction**:
   - Recommend extraction methods from source system
   - Plan for incremental vs. full extraction
   - Handle data consistency during migration

4. **Data Transformation**:
   - Identify necessary data transformations
   - Plan for data cleaning and validation
   - Handle data format conversions

5. **Loading Strategy**:
   - Recommend optimal loading methods for ClickHouse
   - Plan for batch vs. streaming ingestion
   - Optimize for performance during loading

6. **Testing and Validation**:
   - Plan for data quality validation
   - Recommend testing strategies
   - Set up monitoring and alerting

7. **Rollback and Recovery**:
   - Plan for rollback scenarios
   - Recommend backup strategies
   - Handle migration failures

Please provide specific commands, scripts, and best practices for each phase of the migration."""


def register_migration_planning_prompt_en(
    server: FastMCP, client: ClickHouseClient
) -> None:
    """Register migration planning prompt (English version) with the MCP server."""

    @server.prompt(
        name="plan_migration_en",
        title="Database Migration Planning",
        description="Generate detailed migration planning from specified source system to ClickHouse",
    )
    def plan_migration_en(
        source_system: str, data_size: str = "", requirements: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate database migration planning prompt (English version)

        Args:
            source_system: Source database system name (e.g., "PostgreSQL 14")
            data_size: Data size (optional, e.g., "100GB")
            requirements: Special requirements (optional)

        Returns:
            List of messages containing migration planning prompt
        """

        # Process parameters and build sections
        data_size_section = f"**Data Size**: {data_size}" if data_size else ""
        requirements_section = (
            f"**Requirements**: {requirements}" if requirements else ""
        )

        # Use the template to generate prompt content
        prompt_content = MIGRATION_PLANNING_PROMPT_TEMPLATE.format(
            source_system=source_system,
            data_size_section=data_size_section,
            requirements_section=requirements_section,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return plan_migration_en
