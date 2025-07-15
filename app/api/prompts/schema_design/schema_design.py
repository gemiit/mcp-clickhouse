"""Schema design prompt handler (Chinese version).

This module provides a modular prompt handler for ClickHouse schema design in Chinese.
"""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient


# Chinese prompt template (keep content in Chinese as required)
SCHEMA_DESIGN_PROMPT_TEMPLATE_CN = """请帮助为以下用例设计最优的 ClickHouse 数据库模式:

**用例**: {use_case}

{data_volume_section}

{query_patterns_section}

请提供包含以下方面的全面模式设计:

1. **表结构**:
   - 推荐表名和列定义
   - 为 ClickHouse 选择最优数据类型
   - 设计合适的主键

2. **表引擎选择**:
   - 推荐最佳表引擎（MergeTree 系列）
   - 基于用例需求证明选择理由
   - 配置引擎特定参数

3. **分区策略**:
   - 设计 PARTITION BY 子句（如需要）
   - 推荐分区粒度
   - 考虑数据保留和清理

4. **排序和索引**:
   - 设计最优 ORDER BY 子句
   - 推荐二级索引（如需要）
   - 考虑特定列的跳跃索引

5. **性能考虑**:
   - 针对预期查询模式进行优化
   - 考虑用于聚合的物化视图
   - 规划数据摄取模式

6. **可扩展性规划**:
   - 为预期数据增长进行设计
   - 考虑分片策略（如需要）
   - 规划备份和复制

请提供完整的 CREATE TABLE 语句以及每个设计决策的解释。"""


def register_schema_design_prompt(server: FastMCP, client: ClickHouseClient) -> None:
    """Register schema design prompt (Chinese version) with the MCP server.

    This function provides a modular way to register only the schema design prompt handler,
    without registering all other prompts.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance

    Example:
        >>> from mcp.server.fastmcp import FastMCP
        >>> from app.core.client import ClickHouseClient
        >>> from app.api.prompts.schema_design import register_schema_design_prompt
        >>>
        >>> server = FastMCP(name="Schema Design")
        >>> client = ClickHouseClient(host="localhost", port=9000)
        >>> register_schema_design_prompt(server, client)

    Request parameter example:
        The prompt accepts the following parameters via GetPromptRequestParams:

        Basic request (only required parameters):
        ```python
        params = GetPromptRequestParams(
            name="design_schema",
            arguments={
                "use_case": "电商网站的用户行为分析系统"
            }
        )
        ```

        Full request (all parameters):
        ```python
        params = GetPromptRequestParams(
            name="design_schema",
            arguments={
                "use_case": "实时日志分析系统，需要存储和分析应用程序日志",
                "data_volume": "每天 1000 万条日志记录，每月约 50GB",
                "query_patterns": "按时间范围查询、按错误级别聚合、按用户ID过滤"
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
                "name": "design_schema",
                "arguments": {
                    "use_case": "IoT 设备数据收集和分析平台",
                    "data_volume": "每秒 10000 个数据点，每年 300TB",
                    "query_patterns": "时间序列聚合、设备状态监控、异常检测查询"
                }
            }
        }
        ```
    """

    @server.prompt(
        name="design_schema",
        title="模式设计",
        description="为特定用例设计最优的 ClickHouse 数据库模式",
    )
    def design_schema(
        use_case: str, data_volume: str = "", query_patterns: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate schema design prompt (Chinese version).

        Args:
            use_case: Description of the use case and data requirements
            data_volume: Expected data volume (optional, e.g., "每天100万行", "每月100GB")
            query_patterns: Common query patterns and access patterns (optional)

        Returns:
            List of messages containing schema design prompt
        """

        # Process parameters and build sections
        data_volume_section = f"**预期数据量**: {data_volume}" if data_volume else ""
        query_patterns_section = (
            f"**查询模式**: {query_patterns}" if query_patterns else ""
        )

        # Use the template to generate prompt content
        prompt_content = SCHEMA_DESIGN_PROMPT_TEMPLATE_CN.format(
            use_case=use_case,
            data_volume_section=data_volume_section,
            query_patterns_section=query_patterns_section,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return design_schema
