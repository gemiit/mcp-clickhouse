"""Query optimization prompt handler."""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient


# English version prompt template
QUERY_OPTIMIZATION_PROMPT_TEMPLATE_EN = """Please analyze and optimize the following ClickHouse SQL query:

```sql
{query}
```

{context_section}

Please provide optimization recommendations covering:

1. **Query Structure**:
   - Analyze the query execution plan
   - Identify potential bottlenecks
   - Suggest query rewriting opportunities

2. **Index Usage**:
   - Check if existing indexes are being used effectively
   - Recommend additional indexes if needed
   - Suggest primary key optimization

3. **Join Optimization**:
   - Analyze join order and types
   - Recommend join algorithm optimizations
   - Suggest denormalization if beneficial

4. **Aggregation Optimization**:
   - Optimize GROUP BY and ORDER BY clauses
   - Recommend materialized views for repeated aggregations
   - Suggest pre-aggregation strategies

5. **Performance Tuning**:
   - Recommend query settings for better performance
   - Suggest memory and CPU optimizations
   - Identify opportunities for parallel processing

Please provide the optimized query along with explanations for each change."""


def register_query_optimization_prompt_en(
    server: FastMCP, client: ClickHouseClient
) -> None:
    """Register query optimization prompt (English version) with the MCP server."""

    @server.prompt(
        name="optimize_query_en",
        title="Optimize SQL Query",
        description="Analyze and suggest optimizations for ClickHouse SQL queries",
    )
    def optimize_query_en(query: str, context: str = "") -> List[Dict[str, Any]]:
        """
        Generate query optimization prompt (English version)

        Args:
            query: SQL query to optimize
            context: Additional context about the query purpose and expected performance (optional)

        Returns:
            List of messages containing query optimization prompt
        """

        # Process parameters and build sections
        context_section = f"**Context**: {context}" if context else ""

        # Use the template to generate prompt content
        prompt_content = QUERY_OPTIMIZATION_PROMPT_TEMPLATE_EN.format(
            query=query,
            context_section=context_section,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return optimize_query_en
