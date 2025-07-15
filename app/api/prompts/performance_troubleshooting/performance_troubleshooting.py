"""Performance troubleshooting prompt handler (Chinese version).

This module provides a modular prompt handler for ClickHouse performance troubleshooting in Chinese.
"""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient


# Chinese prompt template (keep content in Chinese as required)
PERFORMANCE_TROUBLESHOOTING_PROMPT_TEMPLATE_CN = """请帮助排查以下 ClickHouse 性能问题:

**问题描述**: {issue_description}

{slow_query_section}

请提供系统性的故障排查方法:

1. **问题分析**:
   - 识别潜在的根本原因
   - 对性能问题进行分类
   - 评估严重程度和影响范围

2. **诊断步骤**:
   - 推荐系统查询以收集更多信息
   - 建议监控查询以跟踪性能指标
   - 识别需要监控的关键性能指标

3. **常见解决方案**:
   - 检查常见的 ClickHouse 性能问题
   - 推荐配置优化
   - 建议查询优化（如适用）

4. **系统级检查**:
   - 检查服务器资源（CPU、内存、磁盘 I/O）
   - 检查 ClickHouse 配置设置
   - 分析系统日志中的错误或警告

5. **查询级优化**:
   - 分析查询执行计划
   - 推荐索引优化
   - 建议查询重写（如需要）

6. **监控和预防**:
   - 为类似问题设置监控
   - 推荐预防措施
   - 建议性能测试策略

请提供具体的 SQL 查询和命令来帮助诊断和解决问题。"""


def register_performance_troubleshooting_prompt(
    server: FastMCP, client: ClickHouseClient
) -> None:
    """Register performance troubleshooting prompt (Chinese version) with the MCP server.

    This function provides a modular way to register only the performance troubleshooting prompt handler,
    without registering all other prompts.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance

    Example:
        >>> from mcp.server.fastmcp import FastMCP
        >>> from app.core.client import ClickHouseClient
        >>> from app.api.prompts.performance_troubleshooting import register_performance_troubleshooting_prompt
        >>>
        >>> server = FastMCP(name="Performance Troubleshooting")
        >>> client = ClickHouseClient(host="localhost", port=9000)
        >>> register_performance_troubleshooting_prompt(server, client)

    Request parameter example:
        The prompt accepts the following parameters via GetPromptRequestParams:

        Basic request (only required parameters):
        ```python
        params = GetPromptRequestParams(
            name="troubleshoot_performance",
            arguments={
                "issue_description": "查询响应时间过长"
            }
        )
        ```

        Full request (all parameters):
        ```python
        params = GetPromptRequestParams(
            name="troubleshoot_performance",
            arguments={
                "issue_description": "聚合查询在大表上执行时间超过 30 秒",
                "slow_query": "SELECT count(*), avg(price) FROM sales WHERE date >= '2023-01-01' GROUP BY category"
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
                "name": "troubleshoot_performance",
                "arguments": {
                    "issue_description": "内存使用率过高导致查询失败",
                    "slow_query": "SELECT * FROM large_table ORDER BY timestamp DESC LIMIT 1000"
                }
            }
        }
        ```
    """

    @server.prompt(
        name="troubleshoot_performance",
        title="性能故障排查",
        description="诊断和解决 ClickHouse 性能问题",
    )
    def troubleshoot_performance(
        issue_description: str, slow_query: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate performance troubleshooting prompt (Chinese version).

        Args:
            issue_description: Description of the performance issue
            slow_query: Slow query causing the issue (optional)

        Returns:
            List of messages containing performance troubleshooting prompt
        """

        # Process parameters and build sections
        slow_query_section = (
            f"**慢查询**:\n```sql\n{slow_query}\n```" if slow_query else ""
        )

        # Use the template to generate prompt content
        prompt_content = PERFORMANCE_TROUBLESHOOTING_PROMPT_TEMPLATE_CN.format(
            issue_description=issue_description,
            slow_query_section=slow_query_section,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return troubleshoot_performance
