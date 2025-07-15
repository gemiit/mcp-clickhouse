# MCP-ClickHouse Server

**📖 [简体中文](README_CN.md)**  

A minimal yet powerful [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that exposes **single-instance ClickHouse** as a set of structured tools and resources.  
It lets LLM agents, chat-ops bots, or any MCP-compatible client **query, write and explore** ClickHouse using a simple JSON-RPC interface – no driver, DSN or SQL parsing required.

---

## Feature Highlights
* Arbitrary SQL queries – results in JSON / CSV / Pretty formats
* High-throughput batch `INSERT` for structured data
* Instant schema & data discovery via `schema://` / `data://` resources
* **🤖 AI Assistant Prompts** – 5 professional ClickHouse consulting assistants covering table analysis, query optimization, schema design, performance troubleshooting, and migration planning
* Built-in Prometheus `/metrics` endpoint
* Optional OpenTelemetry tracing (OTLP)
* Fully async & production-ready (FastAPI + clickhouse-driver)
* Container & K8s manifests provided – but equally happy to run via `stdio` for local AI assistants
* **Zero external dependencies** beyond ClickHouse itself

---
## Available Tools

| Tool name            | Category | Description                                                                          |
|----------------------|----------|--------------------------------------------------------------------------------------|
| `query`              | SQL      | Execute arbitrary SQL and stream results                                             |
| `insert`             | SQL      | Bulk-insert rows (`[{column: value, …}, …]`)                                         |
| `create_database`    | Schema   | Create a new database                                                                |
| `create_table`       | Schema   | Create a table (engine, columns, etc. as JSON)                                       |
| `server_info`        | Admin    | Return ClickHouse version, uptime, databases, etc.                                   |

_Resources_
`resource://schema` – browse DBs / tables / columns, incl. DDL
`resource://data`   – sample rows, counts, custom readonly SQL via query string

## AI Assistant Prompts

| Prompt name                  | Function | Description                                                                          |
|------------------------------|----------|--------------------------------------------------------------------------------------|
| `analyze_table`              | Table Analysis | Analyze ClickHouse table structure, data distribution and suggest optimizations |
| `optimize_query`             | Query Optimization | Analyze and suggest optimizations for ClickHouse SQL queries |
| `design_schema`              | Schema Design | Design optimal ClickHouse database schema for specific use cases |
| `troubleshoot_performance`   | Performance Troubleshooting | Diagnose and resolve ClickHouse performance issues |
| `plan_migration`             | Migration Planning | Generate detailed migration plans from specified source systems to ClickHouse |

_Each prompt is available in both Chinese and English versions, providing professional ClickHouse consulting advice_

---

## Quick Start

### 1 · Docker

```bash
docker run --rm -p 8000:8000 \
  -e CH_HOST=host.docker.internal \
  mcp/clickhouse run -t sse
```

### 2 · Poetry (local)

```bash
poetry install
poetry run mcp-clickhouse run -t sse
```

---

## Configuration

All options are simple environment variables (can live in `.env`).

> This project directly uses [FastMCP](https://github.com/modelcontextprotocol/python-sdk)'s native configuration system.  
> Uses `FASTMCP_` prefixed environment variables to configure FastMCP server directly, without additional wrapper layers.  
> This design is simpler and more direct, reducing configuration complexity.

FastMCP server configuration example:

```dotenv
# FastMCP Server Basic Settings
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=3000
FASTMCP_DEBUG=false
FASTMCP_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# FastMCP Path Configuration
FASTMCP_MOUNT_PATH=/mcp
FASTMCP_SSE_PATH=/sse
FASTMCP_MESSAGE_PATH=/messages/
FASTMCP_STREAMABLE_HTTP_PATH=/mcp

# FastMCP Transport Settings
FASTMCP_STATELESS_HTTP=false
FASTMCP_JSON_RESPONSE=false

# FastMCP Resource Management
FASTMCP_WARN_ON_DUPLICATE_RESOURCES=true
FASTMCP_WARN_ON_DUPLICATE_TOOLS=true
FASTMCP_WARN_ON_DUPLICATE_PROMPTS=true
```

| Variable | Default | Description |
|----------|---------|-------------|
| **MCP** |||
| `FASTMCP_HOST` | `0.0.0.0` | Bind address |
| `FASTMCP_PORT` | `3000` | Port |
| `FASTMCP_TRANSPORT` | `streamable-http` | `streamable-http`, `sse`, `stdio` |
| **ClickHouse** |||
| `CH_HOST` | `localhost` | Host |
| `CH_PORT` | `9000` | Port |
| `CH_USER` / `CH_PASSWORD` | `default` / _empty_ | Credentials |
| `CH_DATABASE` | `default` | Default DB |
| `CH_SECURE` | `false` | Enable TLS |
| **Observability** |||
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, … |
| `METRICS_ENABLED` | `true` | Expose `/metrics` |
| `TRACING_ENABLED` | `false` | Enable OTLP export |
| `OTLP_ENDPOINT` |  | Collector URL |
| **Misc** |||
| `TEMP_DIR` | `/tmp/mcp-clickhouse` | Temp files |
| `MAX_UPLOAD_SIZE` | `104857600` | Upload limit (bytes) |

---

## Usage & Integration

### STDIO (ideal for local AI assistants)

```bash
poetry run mcp-clickhouse run -t stdio
```

### SSE or Streamable-HTTP server

```bash
poetry run mcp-clickhouse run -t sse
# or
poetry run mcp-clickhouse run -t streamable-http
```

### Claude Desktop snippet

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

(Replace `command` with `docker run --rm -i mcp/clickhouse run -t stdio` if you prefer Docker.)

### Claude Desktop (SSE)

If you prefer to run the server in **SSE mode** (HTTP long-poll, supports multiple concurrent clients):

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

First start the server separately:

```bash
# Local (Poetry)
poetry run mcp-clickhouse run -t sse

# Or via Docker
docker run --rm -p 8000:8000 \
  -e CH_HOST=host.docker.internal \
  mcp/clickhouse run -t sse
```

---

## AI Assistant Usage Examples
## Usage Examples

This section provides comprehensive usage examples, from basic operations to AI assistant features, helping you quickly get started and fully utilize all MCP-ClickHouse capabilities.

### Basic Operations

#### Quick Query - System Information and Basic Operations

```python
from mcp.client.quick import call_tool

# Get ClickHouse server information
server_info = call_tool(
    "http://localhost:3000/mcp",
    "server_info",
    {}
)
print("=== Server Information ===")
print(f"Version: {server_info.get('version')}")
print(f"Uptime: {server_info.get('uptime')}")

# Execute basic queries
current_status = call_tool(
    "http://localhost:3000/mcp",
    "query",
    {
        "sql": "SELECT now() as current_time, version() as version, uptime() as uptime",
        "format": "JSONEachRow"
    }
)
print("\n=== Current Status ===")
for row in current_status:
    print(f"Time: {row[0]}")
    print(f"Version: {row[1]}")
    print(f"Uptime: {row[2]} seconds")

# List available databases
databases = call_tool(
    "http://localhost:3000/mcp",
    "query",
    {"sql": "SHOW DATABASES"}
)
print(f"\n=== Available Databases ({len(databases)} total) ===")
for db in databases:
    print(f"- {db[0]}")
```

### Advanced Operations

#### Complete Data Workflow - Create, Insert, Query, Analyze

```python
import asyncio
import random
import datetime as dt
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def complete_data_workflow():
    """Demonstrate complete data operations workflow"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # 1. Create database
            print("=== 1. Creating Test Database ===")
            await session.call_tool("create_database", {
                "database": "demo_analytics"
            })
            
            # 2. Create table
            print("=== 2. Creating User Events Table ===")
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
            
            # 3. Generate and insert test data
            print("=== 3. Inserting Test Data ===")
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
            print(f"Successfully inserted {len(events)} records")
            
            # 4. Data verification and basic analysis
            print("=== 4. Data Verification and Analysis ===")
            
            # Total record count
            total_count = await session.call_tool("query", {
                "sql": "SELECT count() FROM demo_analytics.user_events"
            })
            print(f"Total records: {total_count[0][0]:,}")
            
            # User activity analysis
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
            
            print("\nUser Activity Analysis:")
            print("Event Type\t\tEvents\t\tUnique Users\tAvg Duration")
            print("-" * 65)
            for row in user_activity:
                print(f"{row[0]:<12}\t{row[1]:<8}\t{row[2]:<12}\t{row[3]:.1f}s")
            
            return session, "demo_analytics", "user_events"

# Run basic workflow
session, database, table = asyncio.run(complete_data_workflow())
```

#### Resource Discovery and System Monitoring

```python
async def advanced_features_demo():
    """Demonstrate advanced features: resource discovery, monitoring and optimization"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # 1. Use resource discovery features
            print("=== 1. Database Schema Discovery ===")
            
            # Get schema information for all databases
            schema_info = await session.get_resource("resource://schema")
            print("Available database schemas:")
            print(schema_info.get("content", ""))
            # Get table sample data (with time filter)
            sample = await session.get_resource(
                "resource://data/demo_analytics/user_events/sample"
                "?start_time=2024-07-01T00:00:00"
                "&end_time=2024-07-01T23:59:59"
                "&time_column=event_time"
                "&limit=5"
            )
            print("Table sample data (with time range):")
            print(sample)
            
            # 2. System performance monitoring
            print("\n=== 2. System Performance Monitoring ===")
            
            # Query current system load
            system_metrics = await session.call_tool("query", {
                "sql": """
                SELECT
                    'CPU Cores' as metric,
                    toString(value) as value
                FROM system.asynchronous_metrics
                WHERE metric = 'jemalloc.background_thread.num_threads'
                UNION ALL
                SELECT
                    'Memory Usage',
                    formatReadableSize(value)
                FROM system.asynchronous_metrics
                WHERE metric = 'MemoryTracking'
                """
            })
            
            print("System resource status:")
            for metric in system_metrics:
                print(f"- {metric[0]}: {metric[1]}")

asyncio.run(advanced_features_demo())
```

### AI Assistant Features

Based on the above basic operations, you can use AI assistants to get professional ClickHouse consulting advice:

#### Table Analysis - Deep Structure and Performance Analysis
```python
import asyncio
import time
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def analyze_table_performance():
    """Analyze table structure, data distribution and performance bottlenecks"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # Get professional table analysis recommendations
            result = await session.call_tool("prompts/get", {
                "name": "analyze_table",
                "arguments": {
                    "database": "ecommerce",
                    "table": "order_events",
                    "sample_size": "10000"  # Analyze 10k sample records
                }
            })
            
            print("=== Table Analysis Report ===")
            print(result[0]["content"]["text"])
            
            # Verify recommendations with actual queries
            stats = await session.call_tool("query", {
                "sql": "SELECT count(), formatReadableSize(sum(data_compressed_bytes)) FROM system.parts WHERE database='ecommerce' AND table='order_events'"
            })
            print(f"Current table stats: {stats}")

# Run analysis
asyncio.run(analyze_table_performance())
```

### Query Optimization - Intelligent SQL Performance Tuning
```python
async def optimize_slow_query():
    """Get query optimization suggestions and verify improvements"""
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
            
            # Get optimization recommendations
            optimization = await session.call_tool("prompts/get", {
                "name": "optimize_query",
                "arguments": {
                    "query": slow_query,
                    "context": "User behavior analytics report, executed hourly, currently takes over 30 seconds"
                }
            })
            
            print("=== Query Optimization Recommendations ===")
            print(optimization[0]["content"]["text"])
            
            # Test original query performance
            print("\n=== Original Query Performance ===")
            import time
            start_time = time.time()
            result = await session.call_tool("query", {"sql": slow_query})
            execution_time = time.time() - start_time
            print(f"Execution time: {execution_time:.2f}s, Result rows: {len(result)}")

asyncio.run(optimize_slow_query())
```

### Schema Design - Optimal Architecture for Business Scenarios
```python
async def design_analytics_schema():
    """Design database schema for specific business scenarios"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # Get schema design recommendations
            schema_design = await session.call_tool("prompts/get", {
                "name": "design_schema",
                "arguments": {
                    "use_case": "E-commerce platform real-time analytics system supporting user behavior tracking, order analysis, product recommendations, and live dashboards",
                    "data_volume": "1M daily active users, 50M events per day, ~200GB monthly growth",
                    "query_patterns": "Real-time user profiling, product sales trends, funnel analysis, live monitoring dashboard aggregations"
                }
            })
            
            print("=== Database Schema Design Plan ===")
            print(schema_design[0]["content"]["text"])
            
            # Create example tables based on recommendations
            print("\n=== Creating Example Table Structure ===")
            # Execute recommended CREATE TABLE statements here

asyncio.run(design_analytics_schema())
```

### Performance Troubleshooting - System Performance Issue Diagnosis
```python
async def diagnose_performance_issues():
    """Diagnose and resolve ClickHouse performance issues"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # Collect system information first
            system_info = await session.call_tool("query", {
                "sql": """
                SELECT
                    'CPU Usage' as metric,
                    toString(round(avg(ProfileEvent_OSCPUVirtualTimeMicroseconds)/1000000, 2)) as value
                FROM system.metric_log
                WHERE event_time >= now() - INTERVAL 1 HOUR
                UNION ALL
                SELECT
                    'Memory Usage',
                    formatReadableSize(max(CurrentMetric_MemoryTracking))
                FROM system.metric_log
                WHERE event_time >= now() - INTERVAL 1 HOUR
                """
            })
            
            # Get performance diagnosis recommendations
            troubleshooting = await session.call_tool("prompts/get", {
                "name": "troubleshoot_performance",
                "arguments": {
                    "issue_description": "Large table aggregation queries increased from 5s to 60s response time, memory usage continuously rising, occasional query timeouts",
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
            
            print("=== Current System Status ===")
            for row in system_info:
                print(f"{row[0]}: {row[1]}")
                
            print("\n=== Performance Issue Diagnosis Report ===")
            print(troubleshooting[0]["content"]["text"])

asyncio.run(diagnose_performance_issues())
```

### Migration Planning - Complete Database Migration Workflow
```python
async def plan_database_migration():
    """Create migration plan from other databases to ClickHouse"""
    async with streamablehttp_client("http://localhost:3000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # Get migration planning recommendations
            migration_plan = await session.call_tool("prompts/get", {
                "name": "plan_migration",
                "arguments": {
                    "source_system": "MySQL 8.0 cluster with order system (50GB), user system (20GB), logging system (500GB)",
                    "data_size": "Total 570GB historical data, 2GB daily growth, peak 5000 QPS",
                    "requirements": "Zero downtime migration, maintain strong data consistency, 10x query performance improvement, real-time analytics support"
                }
            })
            
            print("=== Database Migration Plan ===")
            print(migration_plan[0]["content"]["text"])
            
            # Verify source system connectivity and target system readiness
            print("\n=== Pre-migration Environment Check ===")
            ch_version = await session.call_tool("query", {
                "sql": "SELECT version()"
            })
            print(f"Target ClickHouse version: {ch_version[0][0]}")
            
            # Check available storage space
            storage_info = await session.call_tool("query", {
                "sql": """
                SELECT
                    formatReadableSize(free_space) as free_space,
                    formatReadableSize(total_space) as total_space
                FROM system.disks
                WHERE name = 'default'
                """
            })
            print(f"Available storage: {storage_info[0][0]} / {storage_info[0][1]}")
# Run complete demonstration
asyncio.run(complete_data_workflow())
```

---

## Development Guide

```bash
# create venv & install deps
poetry install

# run lint & type-check
ruff format .
ruff check . --fix

# run tests
poetry run pytest -v
```

### Releasing

```bash
docker build -t mcp/clickhouse .
docker run --rm -p 3000:3000 mcp/clickhouse run
```

---

## Contributing

Bugs, features or docs improvements welcome!  
Open an issue or submit a PR – make sure `pytest`, `black`, `isort`, `mypy` pass.

---

## License

Apache 2.0 © 2025 San Francisco AI Factory
