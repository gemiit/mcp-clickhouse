"""Query optimization prompt handler (Chinese version).

This module provides a modular prompt handler for ClickHouse query optimization in Chinese.
"""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient


# Chinese prompt template (keep content in Chinese as required)
QUERY_OPTIMIZATION_PROMPT_TEMPLATE_CN = """请分析并优化以下 ClickHouse SQL 查询:

```sql
{query}
```

{context_section}

请提供涵盖以下方面的优化建议:

1. **查询结构**:
   - 分析查询执行计划
   - 识别潜在瓶颈
   - 建议查询重写机会

2. **索引使用**:
   - 检查现有索引是否被有效使用
   - 推荐额外的索引（如需要）
   - 建议主键优化

3. **连接优化**:
   - 分析连接顺序和类型
   - 推荐连接算法优化
   - 建议反规范化（如有益）

4. **聚合优化**:
   - 优化 GROUP BY 和 ORDER BY 子句
   - 推荐用于重复聚合的物化视图
   - 建议预聚合策略

5. **性能调优**:
   - 推荐查询设置以获得更好性能
   - 建议内存和 CPU 优化
   - 识别并行处理机会

请提供优化后的查询以及每个更改的解释。"""


def register_query_optimization_prompt(
    server: FastMCP, client: ClickHouseClient
) -> None:
    """Register query optimization prompt (Chinese version) with the MCP server.

    This function provides a modular way to register only the query optimization prompt handler,
    without registering all other prompts.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance

    Example:
        >>> from mcp.server.fastmcp import FastMCP
        >>> from app.core.client import ClickHouseClient
        >>> from app.api.prompts.query_optimization import register_query_optimization_prompt
        >>>
        >>> server = FastMCP(name="Query Optimization")
        >>> client = ClickHouseClient(host="localhost", port=9000)
        >>> register_query_optimization_prompt(server, client)

    Request parameter example:
        The prompt accepts the following parameters via GetPromptRequestParams:

        Basic request (only required parameters):
        ```python
        params = GetPromptRequestParams(
            name="optimize_query",
            arguments={
                "query": "SELECT * FROM users WHERE age > 25 ORDER BY created_at"
            }
        )
        ```

        Full request (all parameters):
        ```python
        params = GetPromptRequestParams(
            name="optimize_query",
            arguments={
                "query": "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name ORDER BY COUNT(o.id) DESC",
                "context": "用于生成用户订单统计报告，每天执行一次，预期返回前100个用户"
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
                "name": "optimize_query",
                "arguments": {
                    "query": "SELECT date, sum(amount) FROM transactions WHERE date >= '2023-01-01' GROUP BY date ORDER BY date",
                    "context": "日常财务报告查询，需要快速响应"
                }
            }
        }
        ```
    """

    @server.prompt(
        name="optimize_query",
        title="查询优化",
        description="分析并建议 ClickHouse SQL 查询的优化方案",
    )
    def optimize_query(query: str, context: str = "") -> List[Dict[str, Any]]:
        """
        Generate query optimization prompt (Chinese version).

        Args:
            query: SQL query to optimize
            context: Additional context about the query purpose and expected performance (optional)

        Returns:
            List of messages containing query optimization prompt
        """

        # Process parameters and build sections
        context_section = f"**上下文**: {context}" if context else ""

        # Use the template to generate prompt content
        prompt_content = QUERY_OPTIMIZATION_PROMPT_TEMPLATE_CN.format(
            query=query,
            context_section=context_section,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return optimize_query
