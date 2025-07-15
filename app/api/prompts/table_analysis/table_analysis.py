"""Table analysis prompt handler (Chinese version).

This module provides a modular prompt handler for ClickHouse table analysis in Chinese.
"""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Chinese prompt template (keep content in Chinese as required)
TABLE_ANALYSIS_PROMPT_TEMPLATE_CN = """请分析 ClickHouse 表 '{database}.{table}' 并提供洞察和优化建议。

{schema_info}{stats_info}

请提供以下方面的分析:

1. **模式设计**: 
   - 数据类型是否针对用例进行了优化？
   - 是否有冗余或缺失的列？
   - 表结构是否适当地为 ClickHouse 进行了规范化？

2. **性能优化**:
   - 如果尚未使用最佳表引擎，推荐最优表引擎
   - 为查询模式建议合适的 ORDER BY 子句
   - 推荐 PARTITION BY 策略（如适用）
   - 识别可能有帮助的潜在索引或投影

3. **存储优化**:
   - 分析压缩比并建议改进
   - 推荐数据保留策略（如适用）
   - 建议旧数据的归档策略

4. **查询模式**:
   - 识别与此模式配合良好的常见查询模式
   - 为复杂聚合建议物化视图
   - 推荐查询优化技术

请提供具体的、可操作的建议，并在适用的地方提供示例 SQL 语句。"""


def register_table_analysis_prompt(server: FastMCP, client: ClickHouseClient) -> None:
    """Register table analysis prompt (Chinese version) with the MCP server.

    This function provides a modular way to register only the table analysis prompt handler,
    without registering all other prompts.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance

    Example:
        >>> from mcp.server.fastmcp import FastMCP
        >>> from app.core.client import ClickHouseClient
        >>> from app.api.prompts.table_analysis import register_table_analysis_prompt
        >>>
        >>> server = FastMCP(name="Table Analysis")
        >>> client = ClickHouseClient(host="localhost", port=9000)
        >>> register_table_analysis_prompt(server, client)

    Request parameter example:
        The prompt accepts the following parameters via GetPromptRequestParams:

        Basic request (only required parameters):
        ```python
        params = GetPromptRequestParams(
            name="analyze_table",
            arguments={
                "database": "analytics",
                "table": "user_events"
            }
        )
        ```

        Full request (all parameters):
        ```python
        params = GetPromptRequestParams(
            name="analyze_table",
            arguments={
                "database": "ecommerce",
                "table": "orders",
                "sample_size": "5000"
            }
        )
        ```

        JSON-RPC request format:
        ```json
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/get",
            "params": {
                "name": "analyze_table",
                "arguments": {
                    "database": "logs",
                    "table": "application_logs",
                    "sample_size": "2000"
                }
            }
        }
        ```
    """

    @server.prompt(
        name="analyze_table",
        title="表分析",
        description="分析 ClickHouse 表结构、数据分布并建议优化方案",
    )
    async def analyze_table(
        database: str, table: str, sample_size: str = "1000"
    ) -> List[Dict[str, Any]]:
        """
        Generate table analysis prompt (Chinese version).

        Args:
            database: Name of the database containing the table
            table: Name of the table to analyze
            sample_size: Number of sample rows to analyze (optional, default: 1000)

        Returns:
            List of messages containing table analysis prompt
        """

        # Get table information
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
        prompt_content = TABLE_ANALYSIS_PROMPT_TEMPLATE_CN.format(
            database=database,
            table=table,
            schema_info=schema_info,
            stats_info=stats_info,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return analyze_table
