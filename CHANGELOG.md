<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-mcp-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-mcp-light.svg">
    <img src="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-mcp-light.svg" alt="TelemetryFlow Logo" width="80%">
  </picture>

  <h3>TelemetryFlow Python MCP Server (TFO-Python-MCP)</h3>

[![Version](https://img.shields.io/badge/Version-1.1.2-orange.svg)](CHANGELOG.md)
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
  - MCP-specific convenience methods:
    - `record_tool_call()` - Tool execution metrics
    - `record_resource_read()` - Resource read metrics
    - `record_prompt_get()` - Prompt retrieval metrics
    - `record_session_event()` - Session lifecycle events

- **Metrics API**
  - `increment_counter()` - Counter metrics with attributes
  - `record_gauge()` - Gauge metrics for point-in-time values
  - `record_histogram()` - Histogram metrics for distributions

- **Tracing API**
  - `span()` context manager for distributed tracing
  - `add_span_event()` for span annotations
  - `@traced` decorator for automatic function tracing

- **Comprehensive telemetry configuration**
  - API credentials (`api_key_id`, `api_key_secret`)
  - Connection settings (endpoint, protocol, timeout, compression)
  - Signal configuration (traces, metrics, logs, exemplars)
  - Batch settings (timeout, max size)
  - Retry settings (enabled, max retries, backoff)
  - Rate limiting support

#### Built-in Tools

| Tool | Description |
|------|-------------|
| `echo` | Echo testing tool |
| `read_file` | Read file contents with encoding support |
| `write_file` | Write content to files with directory creation |
| `list_directory` | List directory contents (recursive option) |
| `search_files` | Search files by glob pattern |
| `execute_command` | Execute shell commands with timeout |
| `system_info` | Get system information |
| `claude_conversation` | Chat with Claude AI |

#### Built-in Resources

| Resource URI | Description |
|--------------|-------------|
| `config://server` | Server configuration |
| `status://health` | Health status |
| `file:///{path}` | File access (template) |

#### Built-in Prompts

| Prompt | Description |
|--------|-------------|
| `code_review` | Code review assistance |
| `explain_code` | Code explanation |
| `debug_help` | Debugging assistance |

#### Infrastructure

- Claude API client with retry logic (Anthropic SDK)
- Pydantic-based configuration management
- Structured logging with structlog
- In-memory repositories for session, conversation, tool, resource, and prompt storage
- Extended `TelemetryConfig` with 20+ configuration options
- Telemetry lifecycle management (initialization, shutdown, flush)
- Tool execution instrumentation with spans and metrics
- Resource and prompt instrumentation

#### Developer Experience

- CLI with Click (serve, validate, info, init-config commands)
- Comprehensive test suite (260+ tests)
- Docker and docker-compose support
- Pre-commit hooks configuration
- Full documentation (Architecture, Configuration, Development)
- Comprehensive README.md with architecture diagrams
- Environment variable reference in `.env.example`

---

## [Unreleased]

### Planned

- SSE transport support
- WebSocket transport support
- PostgreSQL persistence
- ClickHouse analytics integration
- Redis caching
- NATS JetStream message queue
- Rate limiting
- API key authentication

---

## Version History Summary

| Version | Date       | Highlights                                                     |
|---------|------------|----------------------------------------------------------------|
| 1.1.2   | 2025-01-12 | Initial release with DDD, TelemetryFlow SDK, 8 tools           |

---

## Migration Guide

### Fresh Installation

```bash
# Using pip
pip install tfo-mcp[full]

# Using Poetry
poetry add tfo-mcp[full]

# Using uv
uv pip install tfo-mcp[full]
```

### Enable Telemetry

```bash
# Install with telemetry support
pip install tfo-mcp[telemetry]

# Configure TelemetryFlow
export TELEMETRYFLOW_ENABLED=true
export TELEMETRYFLOW_API_KEY_ID=tfk_your_key_id
export TELEMETRYFLOW_API_KEY_SECRET=tfs_your_key_secret
export TELEMETRYFLOW_ENDPOINT=api.telemetryflow.id:4317

# Start server with telemetry
python -m tfo_mcp serve
```

---

## Links

- [GitHub Repository](https://github.com/devopscorner/telemetryflow-python-mcp)
- [TelemetryFlow Python SDK](https://github.com/devopscorner/telemetryflow-python-sdk)
- [Documentation](docs/README.md)
- [Issue Tracker](https://github.com/devopscorner/telemetryflow-python-mcp/issues)

[Unreleased]: https://github.com/devopscorner/telemetryflow-python-mcp/compare/v1.1.2...HEAD
[1.1.2]: https://github.com/devopscorner/telemetryflow-python-mcp/releases/tag/v1.1.2
