"""Performance troubleshooting prompt handler."""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient


# English version prompt template
PERFORMANCE_TROUBLESHOOTING_PROMPT_TEMPLATE_EN = """Please help troubleshoot the following ClickHouse performance issue:

**Issue Description**: {issue_description}

{slow_query_section}

Please provide a systematic troubleshooting approach:

1. **Issue Analysis**:
   - Identify potential root causes
   - Categorize the type of performance issue
   - Assess the severity and impact

2. **Diagnostic Steps**:
   - Recommend system queries to gather more information
   - Suggest monitoring queries to track performance metrics
   - Identify key performance indicators to monitor

3. **Common Solutions**:
   - Check for common ClickHouse performance issues
   - Recommend configuration optimizations
   - Suggest query optimizations if applicable

4. **System-Level Checks**:
   - Review server resources (CPU, memory, disk I/O)
   - Check ClickHouse configuration settings
   - Analyze system logs for errors or warnings

5. **Query-Level Optimizations**:
   - Analyze query execution plans
   - Recommend index optimizations
   - Suggest query rewriting if needed

6. **Monitoring and Prevention**:
   - Set up monitoring for similar issues
   - Recommend preventive measures
   - Suggest performance testing strategies

Please provide specific SQL queries and commands to help diagnose and resolve the issue."""


def register_performance_troubleshooting_prompt_en(
    server: FastMCP, client: ClickHouseClient
) -> None:
    """Register performance troubleshooting prompt (English version) with the MCP server."""

    @server.prompt(
        name="troubleshoot_performance_en",
        title="Troubleshoot Performance Issues",
        description="Diagnose and resolve ClickHouse performance issues",
    )
    def troubleshoot_performance_en(
        issue_description: str, slow_query: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate performance troubleshooting prompt (English version)

        Args:
            issue_description: Description of the performance issue
            slow_query: Slow query causing the issue (optional)

        Returns:
            List of messages containing performance troubleshooting prompt
        """

        # Process parameters and build sections
        slow_query_section = (
            f"**Slow Query**:\n```sql\n{slow_query}\n```" if slow_query else ""
        )

        # Use the template to generate prompt content
        prompt_content = PERFORMANCE_TROUBLESHOOTING_PROMPT_TEMPLATE_EN.format(
            issue_description=issue_description,
            slow_query_section=slow_query_section,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return troubleshoot_performance_en
