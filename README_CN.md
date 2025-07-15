# MCP-ClickHouse Server（中文）

**👉 [English Version](README.md)**  

轻量级 [Model Context Protocol](https://modelcontextprotocol.io/)（MCP）服务，专为 **单实例 ClickHouse** 设计。  
通过 MCP 工具 / 资源暴露查询、写入与结构发现能力，让 LLM 代理或其他 MCP 客户端可用简洁的 JSON-RPC 接口操作 ClickHouse —— **无需驱动、DSN 或解析 SQL。**

---

## 核心特性
* 任意 SQL 查询，结果支持 JSON / CSV / Pretty
* 高吞吐批量 `INSERT`
* 即时架构 / 数据发现：`schema://…` & `data://…`
* **🤖 AI 助手 Prompts** —— 5个专业的 ClickHouse 咨询助手，涵盖表分析、查询优化、模式设计、性能故障排查和迁移规划
* 内置 Prometheus `/metrics`
* 可选 OpenTelemetry（OTLP）链路追踪
* 完全异步（FastAPI + clickhouse-driver），生产就绪
* 支持 STDIO / SSE / Streamable-HTTP，多种部署方式

---

## 可用工具

| 工具 | 分类 | 说明 |
|------|------|------|
| `query`            | SQL    | 执行任意 SQL 并流式返回结果 |
| `insert`           | SQL    | 批量写入行（`[{列: 值,…}]`） |
| `create_database`  | Schema | 新建数据库 |
| `create_table`     | Schema | 创建表（引擎 / 列信息 JSON） |
| `server_info`      | Admin  | 返回 ClickHouse 版本、运行时间、数据库数量等 |

_资源_
`resource://schema` —— 浏览数据库 / 表 / 列并获取 DDL
`resource://data`   —— 获取示例行、计数或通过查询参数执行只读 SQL

## AI 助手 Prompts

| Prompt | 功能 | 说明 |
|--------|------|------|
| `analyze_table`              | 表分析 | 分析 ClickHouse 表结构、数据分布并建议优化方案 |
| `optimize_query`             | 查询优化 | 分析并建议 ClickHouse SQL 查询的优化方案 |
| `design_schema`              | 模式设计 | 为特定用例设计最优的 ClickHouse 数据库模式 |
| `troubleshoot_performance`   | 性能故障排查 | 诊断和解决 ClickHouse 性能问题 |
| `plan_migration`             | 迁移规划 | 为从指定源系统到 ClickHouse 的数据迁移生成详细规划方案 |

_每个 Prompt 都提供中英文版本，帮助用户获得专业的 ClickHouse 咨询建议_

---

## 快速开始

### 1 · Docker

```bash
docker run --rm -p 8000:8000 \
  -e CH_HOST=host.docker.internal \
  mcp/clickhouse run -t sse
```

### 2 · Poetry 本地运行

```bash
poetry install
poetry run mcp-clickhouse run -t sse
```

---

## 配置

所有选项均为环境变量（可放入 `.env`）。

> 本项目直接使用 [FastMCP](https://github.com/modelcontextprotocol/python-sdk) 的原生配置系统。  
> 使用 `FASTMCP_` 前缀的环境变量直接配置 FastMCP 服务器，无需额外的封装层。  
> 这样设计更简单、更直接，减少了配置复杂性。

FastMCP 服务器配置示例：

```dotenv
# FastMCP 服务器基本设置
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=3000
FASTMCP_DEBUG=false
FASTMCP_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# FastMCP 路径配置
FASTMCP_MOUNT_PATH=/mcp
FASTMCP_SSE_PATH=/sse
FASTMCP_MESSAGE_PATH=/messages/
FASTMCP_STREAMABLE_HTTP_PATH=/mcp

# FastMCP 传输设置
FASTMCP_STATELESS_HTTP=false
FASTMCP_JSON_RESPONSE=false

# FastMCP 资源管理
FASTMCP_WARN_ON_DUPLICATE_RESOURCES=true
FASTMCP_WARN_ON_DUPLICATE_TOOLS=true
FASTMCP_WARN_ON_DUPLICATE_PROMPTS=true
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| **MCP** |||
| `FASTMCP_HOST` | `0.0.0.0` | 监听地址 |
| `FASTMCP_PORT` | `3000` | 监听端口 |
| `FASTMCP_TRANSPORT` | `streamable-http` | `streamable-http` / `sse` / `stdio` |
| **ClickHouse** |||
| `CH_HOST` | `localhost` | 主机 |
| `CH_PORT` | `9000` | 端口 |
| `CH_USER` / `CH_PASSWORD` | `default` / 空 | 凭据 |
| `CH_DATABASE` | `default` | 默认数据库 |
| `CH_SECURE` | `false` | 是否启用 TLS |
| **可观测性** |||
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `METRICS_ENABLED` | `true` | 暴露 `/metrics` |
| `TRACING_ENABLED` | `false` | 启用 OTLP |
| `OTLP_ENDPOINT` |  | Collector URL |
| **其他** |||
| `TEMP_DIR` | `/tmp/mcp-clickhouse` | 临时目录 |
| `MAX_UPLOAD_SIZE` | `104857600` | 上传大小上限（字节） |

---

## 使用与集成

### STDIO（本地 AI 助手最简）

```bash
poetry run mcp-clickhouse run -t stdio
```

### SSE / Streamable-HTTP 服务模式

```bash
# SSE
poetry run mcp-clickhouse run -t sse
# Streamable-HTTP
poetry run mcp-clickhouse run -t streamable-http
```

### Claude Desktop 配置示例

```jsonc
{
  "mcpServers": {
    "clickhouse": {
      "command": "mcp-clickhouse",
      "args": ["-t", "stdio"],
      "env": {
        "CH_HOST": "localhost",
        "CH_PORT": "9000"
      }
    }
  }
}
```

> 若使用 Docker，可将 `command` 替换为  
> `docker run --rm -i mcp/clickhouse run -t stdio`

### Claude Desktop（SSE模式）

如果你希望使用 **SSE 模式**（HTTP 长轮询，可支持多客户端并发）运行服务器，可按以下方式配置 Claude Desktop：

```jsonc
{
  "mcpServers": {
    "clickhouse": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

在使用上述配置前，需要先单独以 **SSE 模式**启动服务器：

```bash
# 本地（Poetry）
poetry run mcp-clickhouse run -t sse

# 或使用 Docker
docker run --rm -p 8000:8000 \
  -e CH_HOST=host.docker.internal \
  mcp/clickhouse run -t sse
```

---

## 使用示例

本节提供完整的使用示例，从基础操作到AI助手功能，帮助您快速上手并充分利用MCP-ClickHouse的所有功能。

### 基础操作示例

#### 快速查询 - 系统信息和基础操作

```python
from mcp.client.quick import call_tool

# 获取ClickHouse服务器信息
server_info = call_tool(
    "http://localhost:3000/mcp",
    "server_info",
    {}
)
print("=== 服务器信息 ===")
print(f"版本: {server_info.get('version')}")
print(f"运行时间: {server_info.get('uptime')}")

# 执行基础查询
current_time = call_tool(
    "http://localhost:3000/mcp",
    "query",
    {
        "sql": "SELECT now() as current_time, version() as version, uptime() as uptime",
        "format": "JSONEachRow"
    }
)
print("\n=== 当前状态 ===")
for row in current_time:
    print(f"时间: {row[0]}")
    print(f"版本: {row[1]}")
    print(f"运行时间: {row[2]}秒")

# 查看数据库列表
databases = call_tool(
    "http://localhost:3000/mcp",
    "query",
    {"sql": "SHOW DATABASES"}
)
print(f"\n=== 可用数据库 ({len(databases)}个) ===")
for db in databases:
    print(f"- {db[0]}")
```

### 高级操作示例

#### 完整数据工作流程 - 创建、插入、查询、分析

```python
import asyncio
import random
import datetime as dt
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def complete_data_workflow():
    """演示完整的数据操作流程"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # 1. 创建数据库
            print("=== 1. 创建测试数据库 ===")
            await session.call_tool("create_database", {
                "database": "demo_analytics"
            })
            
            # 2. 创建表
            print("=== 2. 创建用户事件表 ===")
            await session.call_tool("create_table", {
                "database": "demo_analytics",
                "table": "user_events",
                "engine": "MergeTree",
                "columns": [
                    {"name": "event_time", "type": "DateTime"},
                    {"name": "user_id", "type": "UInt32"},
                    {"name": "event_type", "type": "String"},
                    {"name": "page_url", "type": "String"},
                    {"name": "session_duration", "type": "UInt32"}
                ],
                "order_by": ["event_time", "user_id"],
                "partition_by": "toYYYYMM(event_time)"
            })
            
            # 3. 生成并插入测试数据
            print("=== 3. 插入测试数据 ===")
            events = []
            event_types = ['login', 'view', 'click', 'purchase', 'logout']
            pages = ['/home', '/product', '/cart', '/checkout', '/profile']
            
            for i in range(1000):
                events.append({
                    "event_time": (dt.datetime.now() - dt.timedelta(
                        minutes=random.randint(0, 1440)
                    )).strftime('%Y-%m-%d %H:%M:%S'),
                    "user_id": random.randint(1, 100),
                    "event_type": random.choice(event_types),
                    "page_url": random.choice(pages),
                    "session_duration": random.randint(10, 3600)
                })
            
            await session.call_tool("insert", {
                "database": "demo_analytics",
                "table": "user_events",
                "rows": events
            })
            print(f"成功插入 {len(events)} 条记录")
            
            # 4. 数据验证和基础分析
            print("=== 4. 数据验证和分析 ===")
            
            # 总记录数
            total_count = await session.call_tool("query", {
                "sql": "SELECT count() FROM demo_analytics.user_events"
            })
            print(f"总记录数: {total_count[0][0]:,}")
            
            # 用户活跃度分析
            user_activity = await session.call_tool("query", {
                "sql": """
                SELECT
                    event_type,
                    count() as event_count,
                    uniq(user_id) as unique_users,
                    avg(session_duration) as avg_duration
                FROM demo_analytics.user_events
                GROUP BY event_type
                ORDER BY event_count DESC
                """
            })
            
            print("\n用户活跃度分析:")
            print("事件类型\t\t事件数\t\t独立用户\t平均时长")
            print("-" * 60)
            for row in user_activity:
                print(f"{row[0]:<12}\t{row[1]:<8}\t{row[2]:<8}\t{row[3]:.1f}秒")
            
            return session, "demo_analytics", "user_events"

# 运行基础工作流程
session, database, table = asyncio.run(complete_data_workflow())
```

#### 资源发现和系统监控

```python
async def advanced_features_demo():
    """演示高级功能：资源发现、监控和优化"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # 1. 使用资源发现功能
            print("=== 1. 数据库架构发现 ===")
            
            # 获取所有数据库的架构信息
            schema_info = await session.get_resource("resource://schema")
            print("可用数据库架构:")
            print(schema_info.get("content", ""))
            # 获取表样本数据（支持时间过滤）
            sample = await session.get_resource(
                "resource://data/demo_analytics/user_events/sample"
                "?start_time=2024-07-01T00:00:00"
                "&end_time=2024-07-01T23:59:59"
                "&time_column=event_time"
                "&limit=5"
            )
            print("表样本数据（指定时间范围）:")
            print(sample)
            
            # 2. 系统性能监控
            print("\n=== 2. 系统性能监控 ===")
            
            # 查询当前系统负载
            system_metrics = await session.call_tool("query", {
                "sql": """
                SELECT
                    'CPU核心数' as metric,
                    toString(value) as value
                FROM system.asynchronous_metrics
                WHERE metric = 'jemalloc.background_thread.num_threads'
                UNION ALL
                SELECT
                    '内存使用量',
                    formatReadableSize(value)
                FROM system.asynchronous_metrics
                WHERE metric = 'MemoryTracking'
                """
            })
            
            print("系统资源状态:")
            for metric in system_metrics:
                print(f"- {metric[0]}: {metric[1]}")

asyncio.run(advanced_features_demo())
```

### AI 助手功能示例

基于上述基础操作，您可以使用AI助手获得专业的ClickHouse咨询建议：

#### 表分析 - 深度分析表结构和性能
```python
import asyncio
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def analyze_table_performance():
    """分析表结构、数据分布和性能瓶颈"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # 获取专业的表分析建议
            result = await session.call_tool("prompts/get", {
                "name": "analyze_table",
                "arguments": {
                    "database": "ecommerce",
                    "table": "order_events",
                    "sample_size": "10000"  # 分析1万条样本数据
                }
            })
            
            print("=== 表分析报告 ===")
            print(result[0]["content"]["text"])
            
            # 可以结合实际查询验证建议
            stats = await session.call_tool("query", {
                "sql": "SELECT count(), formatReadableSize(sum(data_compressed_bytes)) FROM system.parts WHERE database='ecommerce' AND table='order_events'"
            })
            print(f"当前表统计: {stats}")

# 运行分析
asyncio.run(analyze_table_performance())
```

### 查询优化 - 智能SQL性能调优
```python
async def optimize_slow_query():
    """获取查询优化建议并验证效果"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            slow_query = """
            SELECT
                user_id,
                COUNT(*) as event_count,
                AVG(session_duration) as avg_duration
            FROM user_events
            WHERE event_date >= '2024-01-01'
                AND event_type IN ('login', 'purchase', 'view')
            GROUP BY user_id
            HAVING COUNT(*) > 10
            ORDER BY event_count DESC
            LIMIT 100
            """
            
            # 获取优化建议
            optimization = await session.call_tool("prompts/get", {
                "name": "optimize_query",
                "arguments": {
                    "query": slow_query,
                    "context": "用户行为分析报表，每小时执行一次，当前执行时间超过30秒"
                }
            })
            
            print("=== 查询优化建议 ===")
            print(optimization[0]["content"]["text"])
            
            # 可以测试原始查询性能
            print("\n=== 执行原始查询 ===")
            import time
            start_time = time.time()
            result = await session.call_tool("query", {"sql": slow_query})
            execution_time = time.time() - start_time
            print(f"执行时间: {execution_time:.2f}秒, 结果行数: {len(result)}")

asyncio.run(optimize_slow_query())
```

### 模式设计 - 为业务场景设计最优架构
```python
async def design_analytics_schema():
    """为特定业务场景设计数据库模式"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # 获取模式设计建议
            schema_design = await session.call_tool("prompts/get", {
                "name": "design_schema",
                "arguments": {
                    "use_case": "电商平台实时数据分析系统，需要支持用户行为追踪、订单分析、商品推荐和实时大屏展示",
                    "data_volume": "日活用户100万，每天产生5000万事件，每月数据增长约200GB",
                    "query_patterns": "实时用户画像查询、商品销售趋势分析、漏斗转化分析、实时监控大屏聚合查询"
                }
            })
            
            print("=== 数据库模式设计方案 ===")
            print(schema_design[0]["content"]["text"])
            
            # 可以根据建议创建示例表
            print("\n=== 根据建议创建示例表结构 ===")
            # 这里可以执行建议的CREATE TABLE语句

asyncio.run(design_analytics_schema())
```

### 性能故障排查 - 系统性能问题诊断
```python
async def diagnose_performance_issues():
    """诊断和解决ClickHouse性能问题"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # 先收集系统信息
            system_info = await session.call_tool("query", {
                "sql": """
                SELECT
                    'CPU使用率' as metric,
                    toString(round(avg(ProfileEvent_OSCPUVirtualTimeMicroseconds)/1000000, 2)) as value
                FROM system.metric_log
                WHERE event_time >= now() - INTERVAL 1 HOUR
                UNION ALL
                SELECT
                    '内存使用率',
                    formatReadableSize(max(CurrentMetric_MemoryTracking))
                FROM system.metric_log
                WHERE event_time >= now() - INTERVAL 1 HOUR
                """
            })
            
            # 获取性能诊断建议
            troubleshooting = await session.call_tool("prompts/get", {
                "name": "troubleshoot_performance",
                "arguments": {
                    "issue_description": "大表聚合查询响应时间从5秒增长到60秒，内存使用率持续上升，偶尔出现查询超时",
                    "slow_query": """
                    SELECT
                        toYYYYMM(order_date) as month,
                        category,
                        sum(amount) as total_sales,
                        count() as order_count
                    FROM orders
                    WHERE order_date >= '2023-01-01'
                    GROUP BY month, category
                    ORDER BY month DESC, total_sales DESC
                    """
                }
            })
            
            print("=== 系统当前状态 ===")
            for row in system_info:
                print(f"{row[0]}: {row[1]}")
                
            print("\n=== 性能问题诊断报告 ===")
            print(troubleshooting[0]["content"]["text"])

asyncio.run(diagnose_performance_issues())
```

### 迁移规划 - 数据库迁移全流程规划
```python
async def plan_database_migration():
    """制定从其他数据库到ClickHouse的迁移方案"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # 获取迁移规划方案
            migration_plan = await session.call_tool("prompts/get", {
                "name": "plan_migration",
                "arguments": {
                    "source_system": "MySQL 8.0 集群，包含订单系统(50GB)、用户系统(20GB)、日志系统(500GB)",
                    "data_size": "总计570GB历史数据，每天新增2GB，峰值QPS 5000",
                    "requirements": "业务零停机迁移，保持数据强一致性，迁移后查询性能提升10倍，支持实时分析"
                }
            })
            
            print("=== 数据库迁移规划方案 ===")
            print(migration_plan[0]["content"]["text"])
            
            # 可以验证源系统连接和目标系统准备情况
            print("\n=== 迁移前环境检查 ===")
            ch_version = await session.call_tool("query", {
                "sql": "SELECT version()"
            })
            print(f"目标ClickHouse版本: {ch_version[0][0]}")
            
            # 检查可用存储空间
            storage_info = await session.call_tool("query", {
                "sql": """
                SELECT
                    formatReadableSize(free_space) as free_space,
                    formatReadableSize(total_space) as total_space
                FROM system.disks
                WHERE name = 'default'
                """
            })
            print(f"可用存储空间: {storage_info[0][0]} / {storage_info[0][1]}")

asyncio.run(plan_database_migration())
```


---

## 开发指南

```bash
# 安装依赖
poetry install

# 代码格式 & 类型检查
ruff format .
ruff check . --fix

# 运行测试
poetry run pytest -v
```

### 发布镜像

```bash
docker build -t mcp/clickhouse .
docker run --rm -p 3000:3000 mcp/clickhouse
```

---

## 贡献

欢迎提交 Issue / PR！  
请确保 `pytest`、`black`、`isort`、`mypy` 通过后再提交。

---

## 许可证

Apache 2.0 © 2025 San Francisco AI Factory
