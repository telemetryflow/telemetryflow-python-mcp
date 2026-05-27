<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-mcp-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-mcp-light.svg">
    <img src="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-mcp-light.svg" alt="TelemetryFlow Logo" width="80%">
  </picture>

  <h3>TelemetryFlow Python MCP Server (TFO-Python-MCP)</h3>

[![Version](https://img.shields.io/badge/Version-1.2.0-orange.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://python.org/)
[![MCP Protocol](https://img.shields.io/badge/MCP-2024--11--05-purple?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnoiIGZpbGw9IiNmZmYiLz48L3N2Zz4=)](https://modelcontextprotocol.io/)
[![Claude API](https://img.shields.io/badge/Claude-Opus%204%20%7C%20Sonnet%204-E1BEE7?logo=anthropic)](https://anthropic.com)
[![OTEL SDK](https://img.shields.io/badge/OpenTelemetry_SDK-1.28.0-blueviolet)](https://opentelemetry.io/)
[![Architecture](https://img.shields.io/badge/Architecture-DDD%2FCQRS-success)](docs/ARCHITECTURE.md)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://www.postgresql.org/)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-23+-FFCC00?logo=clickhouse)](https://clickhouse.com/)

</div>

---

# Changelog

All notable changes to TelemetryFlow Python MCP Server (TFO-Python-MCP) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-05-27

### Changed

- **Official MCP Python SDK** integration (`mcp>=1.27.0`) — replaced custom JSON-RPC server with `mcp.server.Server` SDK
- Server uses `mcp.server.stdio.stdio_server` transport
- Tool/resource/prompt registration via `server.register_tool()`, `server.register_resource()`, `server.register_prompt()`
- Full MCP 2024-11-05 protocol compliance via SDK
- **TelemetryFlow Python SDK** upgraded to `telemetryflow-sdk>=1.2.0`

### Added

- **111 LLM Models across 12 Providers** from TFO-Platform seed data:
  - Anthropic Claude (11 models): claude-opus-4-7, claude-sonnet-4-6, claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5, claude-sonnet-4, claude-mythos-preview, etc.
  - Google Gemini (10 models): gemini-3.5-flash, gemini-2.5-pro, gemini-2.5-flash, etc.
  - OpenAI (10 models): gpt-5.5-pro, gpt-5.5, gpt-5, gpt-4.1, o3, etc.
  - DeepSeek (10 models): deepseek-v4-pro, deepseek-chat, deepseek-reasoner, etc.
  - Alibaba Qwen (10 models): qwen3.6-max-preview, qwen3.6-plus, etc.
  - Ollama (10 models): llama4:maverick-17b, gemma4:26b, phi4:14b, etc.
  - Mistral AI (10 models): mistral-medium-3-5, codestral-2508, etc.
  - xAI Grok (10 models): grok-4.3, grok-4.20-multi-agent, etc.
  - Kimi/Moonshot (10 models): kimi-k2.6, moonshot-v1-128k, etc.
  - Zhipu GLM (10 models): glm-5.1, glm-5-turbo, glm-4.7, etc.
  - Xiaomi MiMo (10 models): mimo-v2.5-pro, mimo-v2-omni, etc.
  - Custom (1 model)
- `ProviderType` enum for provider identification
- `Model.get_provider()` method for model-to-provider mapping

#### TFO Datasource Tools — PostgreSQL (4 tools)

| Tool                | Description                                             |
| ------------------- | ------------------------------------------------------- |
| `pg_query`          | Execute read-only SQL against TFO PostgreSQL datasource |
| `pg_list_tables`    | List tables in TFO PostgreSQL schema                    |
| `pg_describe_table` | Describe table schema (columns, indexes)                |
| `pg_sessions`       | Query MCP session history from PostgreSQL               |

#### TFO Datasource Tools — ClickHouse Analytics (5 tools)

| Tool                   | Description                                                     |
| ---------------------- | --------------------------------------------------------------- |
| `ch_query`             | Execute read-only SQL against TFO ClickHouse analytics          |
| `ch_tool_analytics`    | Tool call analytics (counts, durations, success rates)          |
| `ch_session_analytics` | Session analytics (duration, tokens, call counts)               |
| `ch_error_analytics`   | Error analytics (types, counts, trends)                         |
| `ch_api_usage`         | Claude API usage analytics (tokens, durations, model breakdown) |

- References to TFO-Platform `ContextCollector` service for telemetry context collection from ClickHouse materialized views and PostgreSQL
- References to TFO-Platform `PromptBuilder` service for context-aware system prompts per context type

#### TFO-Platform ContextCollector Service (Python Port)

- `ContextCollectorService` application service mirroring TFO-Platform `ContextCollector.service.ts`
- 78 context types across 8 categories: Observability (metrics, logs, traces, exemplars, correlations, dashboard), Infrastructure (uptime, status-page, audit, infra-overview/cpu/memory/storage/network), Kubernetes (overview, clusters, namespaces, nodes, pods, deployments, pv, api-server, coredns), Hybrid (agents, service-map, network-map), Platform (alerts, IAM, tenancy, retention, subscription, api-keys, notifications, reports), Security (data-masking, ai-assistant, system-setup), Account (profile, security, sessions, notifications, preferences, organization), AI Intelligence (anomaly-detection, corrective-maintenance, predictive-maintenance, cost-optimization), DB Monitoring (inventory, clickhouse, mariadb, mysql, percona, sqlite3, timescaledb, aurora, mssql, postgresql, mongodb-community, mongodb-atlas, aws-rds-mysql, aws-rds-aurora, aws-dynamodb, cockroachdb, qan)
- ClickHouse materialized view queries: `metrics_5m`, `logs_1h`, `service_latency_percentiles_1h`, `service_error_rates_1h`, `exemplars_1h`, `uptime_checks`, `audit_logs_1h`, `signal_correlations_1h`, `vm_metrics_1h`, `kubernetes_metrics_1h`, `service_map_metrics_1h`, `network_map_traffic_1h`, `network_map_connection_metrics_1h`
- PostgreSQL context queries: alerts, IAM, tenancy, retention, subscription, api-keys, notifications, reports, data-masking, ai-assistant, system-setup, kubernetes inventory, agents, service-map, network-map
- Hybrid PG+CH contexts: kubernetes (clusters/nodes/pods/deployments/PV + CH metrics), agents (PG inventory + CH vm_metrics), service-map (PG topology + CH metrics), network-map (PG topology + CH traffic)
- 5-second context collection timeout with graceful degradation

#### TFO-Platform PromptBuilder Service (Python Port)

- `PromptBuilderService` application service mirroring TFO-Platform `PromptBuilder.service.ts`
- 60+ specialized analyst personas as system prompts, one per context type
- `build_system_prompt()` — context-aware system prompt generation with IMPORTANT INSTRUCTIONS
- `build_context_prompt()` — formats TelemetryContext as markdown with truncated JSON (10000 char limit)
- `build_insight_prompt()` — 5 insight types: chronology, prediction, recommendation, root-cause, pattern
- `get_available_context_types()` — lists all 78 context types

#### Domain Value Objects

- `ContextType` enum — 78 context types matching TFO-Platform's ContextType union
- `InsightType` enum — chronology, prediction, recommendation, root-cause, pattern
- `TelemetryContext` frozen dataclass — type, time_range, summary, data
- `TimeRange` frozen dataclass — from_time, to_time with validation

#### Docker & Infrastructure

- `docker-compose.yaml` synchronized with TFO Python-SDK patterns:
  - Network: `telemetryflow_python_mcp_net` with subnet `172.154.0./16`, static IPs
  - Profiles: `dev`, `full`, `platform`, `analytics`, `observability`
  - Added `tfo-collector` service (TelemetryFlow Collector v1.2.1, dual OTLP v1/v2 ingestion)
  - Added `tfo-backend` + `tfo-viz` platform services (TelemetryFlow Platform v1.4.0)
  - Aligned PostgreSQL (tfo_admin, telemetryflow_db, PGDATA, VOLUMES_BASE_PATH)
  - Aligned ClickHouse (tfo_admin, telemetryflow_db, separate data/logs volumes)
  - Aligned Redis (maxmemory, maxmemory-policy, appendonly, appendfsync)
  - Aligned NATS (--js --sd /data -m 8222)
- `.env.example` synchronized with TFO Python-SDK patterns:
  - 25 sections with [N] numbering, same variable naming and defaults
  - Container names: `telemetryflow_mcp_*` prefix
  - Static IPs: `172.154.x.x` range
  - Production deployment checklist
  - Versions: MCP 1.2.0, Collector 1.2.1, Platform 1.4.0

### Security

- Dockerfile CVE patching, OCI labels, non-root user

### Test Coverage

- Reorganized test suite into DDD-aligned subfolders: `tests/unit/domain/`, `tests/unit/application/`, `tests/unit/presentation/`, `tests/unit/infrastructure/`, `tests/integration/domain/`, `tests/integration/presentation/`, `tests/integration/infrastructure/`, `tests/e2e/protocol/`
- 1174 tests passing, 98% code coverage

---

## [1.1.2] - 2025-01-12

### Added

#### Core Implementation

- Initial Python implementation of TelemetryFlow Python MCP Server
- Full MCP 2024-11-05 protocol support
- JSON-RPC 2.0 over stdio transport
- Domain-Driven Design (DDD) architecture
- CQRS pattern for command/query separation

#### TelemetryFlow SDK Integration

- **TelemetryFlow Python SDK** integration (`telemetryflow>=1.1.0`)
  - Native integration with TelemetryFlow observability platform
  - Automatic metrics, traces, and logs collection
  - MCP-specific telemetry with `mcp.*` prefixed metrics

- **MCPTelemetryClient wrapper** (`infrastructure/telemetry/client.py`)
  - Thread-safe singleton pattern with `_telemetry_lock`
  - Graceful degradation when telemetry SDK not installed
  - MCP-specific convenience methods

#### Built-in Tools (8)

| Tool                  | Description                                    |
| --------------------- | ---------------------------------------------- |
| `echo`                | Echo testing tool                              |
| `read_file`           | Read file contents with encoding support       |
| `write_file`          | Write content to files with directory creation |
| `list_directory`      | List directory contents (recursive option)     |
| `search_files`        | Search files by glob pattern                   |
| `execute_command`     | Execute shell commands with timeout            |
| `system_info`         | Get system information                         |
| `claude_conversation` | Chat with Claude AI                            |

#### Built-in Resources (3)

| Resource URI      | Description            |
| ----------------- | ---------------------- |
| `config://server` | Server configuration   |
| `status://health` | Health status          |
| `file:///{path}`  | File access (template) |

#### Built-in Prompts (3)

| Prompt         | Description            |
| -------------- | ---------------------- |
| `code_review`  | Code review assistance |
| `explain_code` | Code explanation       |
| `debug_help`   | Debugging assistance   |

---

## [Unreleased]

### Planned

- SSE transport support via MCP SDK
- Streamable HTTP transport via MCP SDK
- Redis caching
- NATS JetStream message queue
- Rate limiting
- API key authentication

---

## Version History Summary

| Version | Date       | Highlights                                                                                                                                                     |
| ------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.2.0   | 2026-05-27 | MCP SDK migration, 111 LLM models, TFO datasource tools (PG+CH), ContextCollector/PromptBuilder services (78 context types), Docker & infrastructure alignment |
| 1.1.2   | 2025-01-12 | Initial release with DDD, TelemetryFlow SDK, 8 tools                                                                                                           |

---

## Migration Guide

### Upgrading from 1.1.2 to 1.2.0

```bash
# Update package
pip install --upgrade tfo-mcp

# Or from source
git pull
pip install -e ".[all]"
```

**Breaking changes:**

- Custom JSON-RPC server replaced by official MCP SDK
- `MCPServer` API changed — tools/resources/prompts now registered via `server.register_tool()`, `server.register_resource()`, `server.register_prompt()`
- `server.session` no longer a domain Session aggregate
- Integration/E2E tests that used `_handle_request()` need rewriting to test via MCP SDK

**New TFO datasource tools:**

```bash
# Install with PostgreSQL support
pip install tfo-mcp[postgres]

# Install with ClickHouse support
pip install tfo-mcp[clickhouse]

# Install with everything
pip install tfo-mcp[all]
```

### Fresh Installation

```bash
# Using pip
pip install tfo-mcp[all]

# Using Docker
docker pull telemetryflow/telemetryflow-python-mcp:1.2.0
```

---

## Links

- [GitHub Repository](https://github.com/telemetryflow/telemetryflow-python-mcp)
- [TelemetryFlow Python SDK](https://github.com/telemetryflow/telemetryflow-python-sdk)
- [Documentation](docs/README.md)
- [Issue Tracker](https://github.com/telemetryflow/telemetryflow-python-mcp/issues)

[Unreleased]: https://github.com/telemetryflow/telemetryflow-python-mcp/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/telemetryflow/telemetryflow-python-mcp/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/telemetryflow/telemetryflow-python-mcp/releases/tag/v1.1.2
