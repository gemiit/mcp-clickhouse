"""Migration planning prompt handler (Chinese version).

This module provides a modular prompt handler for ClickHouse migration planning in Chinese.
"""

from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from app.core.client import ClickHouseClient


# Chinese prompt template (keep content in Chinese as required)
MIGRATION_PLANNING_PROMPT_TEMPLATE_CN = """请帮助规划从 {source_system} 到 ClickHouse 的数据迁移:

**源系统**: {source_system}

{data_size_section}

{requirements_section}

请提供涵盖以下方面的全面迁移计划:

1. **迁移前评估**
   - 分析源系统 ({source_system}) 的数据结构和特点
   - 识别可能的兼容性问题
   - 评估数据量和迁移复杂度

2. **迁移策略**:
   - 推荐迁移方法（大爆炸式 vs. 分阶段）
   - 确定迁移工具和方法
   - 规划数据验证和测试

3. **模式映射**:
   - 将源模式映射到最优的 ClickHouse 模式
   - 推荐数据类型转换
   - 处理模式差异和约束

4. **数据提取**:
   - 推荐从源系统提取的方法
   - 规划增量 vs. 全量提取
   - 处理迁移期间的数据一致性

5. **数据转换**:
   - 识别必要的数据转换
   - 规划数据清理和验证
   - 处理数据格式转换

6. **加载策略**:
   - 推荐 ClickHouse 的最优加载方法
   - 规划批处理 vs. 流式摄取
   - 优化加载期间的性能

7. **技术实施方案**
   - 具体的迁移工具和脚本
   - 数据验证和一致性检查方法
   - 性能优化建议

8. **风险控制**
   - 潜在风险识别
   - 回滚方案
   - 测试策略

9. **测试和验证**:
   - 规划数据质量验证
   - 推荐测试策略
   - 设置监控和告警

10. **回滚和恢复**:
    - 规划回滚场景
    - 推荐备份策略
    - 处理迁移失败

请为迁移的每个阶段提供具体的命令、脚本和最佳实践。"""


def register_migration_planning_prompt(
    server: FastMCP, client: ClickHouseClient
) -> None:
    """Register migration planning prompt (Chinese version) with the MCP server.

    This function provides a modular way to register only the migration planning prompt handler,
    without registering all other prompts.

    Args:
        server: FastMCP server instance
        client: ClickHouseClient instance

    Example:
        >>> from mcp.server.fastmcp import FastMCP
        >>> from app.core.client import ClickHouseClient
        >>> from app.api.prompts.migration_planning import register_migration_planning_prompt
        >>>
        >>> server = FastMCP(name="Migration Planning")
        >>> client = ClickHouseClient(host="localhost", port=9000)
        >>> register_migration_planning_prompt(server, client)

    Request parameter example:
        The prompt accepts the following parameters via GetPromptRequestParams:

        Basic request (only required parameters):
        ```python
        params = GetPromptRequestParams(
            name="plan_migration",
            arguments={
                "source_system": "PostgreSQL"
            }
        )
        ```

        Full request (all parameters):
        ```python
        params = GetPromptRequestParams(
            name="plan_migration",
            arguments={
                "source_system": "MySQL 8.0 包含 50 个表",
                "data_size": "总计 500GB，每天增长 1000 万行",
                "requirements": "零停机迁移，保持数据一致性，支持实时分析"
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
                "name": "plan_migration",
                "arguments": {
                    "source_system": "PostgreSQL 14",
                    "data_size": "100GB",
                    "requirements": "最小停机时间，保留外键"
                }
            }
        }
        ```
    """

    @server.prompt(
        name="plan_migration",
        title="数据库迁移规划",
        description="为从指定源系统到 ClickHouse 的数据迁移生成详细规划方案",
    )
    def plan_migration(
        source_system: str, data_size: str = "", requirements: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate database migration planning prompt (Chinese version).

        Args:
            source_system: Source database system name (e.g., "PostgreSQL 14")
            data_size: Data size (optional, e.g., "100GB")
            requirements: Special requirements (optional)

        Returns:
            List of messages containing migration planning prompt
        """

        # Process parameters and build sections
        data_size_section = f"**数据大小**: {data_size}" if data_size else ""
        requirements_section = f"**要求**: {requirements}" if requirements else ""

        # Use the template to generate prompt content
        prompt_content = MIGRATION_PLANNING_PROMPT_TEMPLATE_CN.format(
            source_system=source_system,
            data_size_section=data_size_section,
            requirements_section=requirements_section,
        )

        # Return content in MCP compliant message format
        return [{"role": "user", "content": {"type": "text", "text": prompt_content}}]

    return plan_migration
