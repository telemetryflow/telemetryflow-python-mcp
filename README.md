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

**Enterprise-Grade Model Context Protocol Server with Claude AI Integration**

A comprehensive MCP server implementation built using Python and following Domain-Driven Design (DDD) patterns, providing seamless integration between the Model Context Protocol and Anthropic's Claude AI.

This server works as the **AI integration layer** for the TelemetryFlow Platform, providing:

- Claude AI conversation capabilities via MCP
- Tool execution with built-in and custom tools
- Resource management and prompt templates
- TelemetryFlow SDK observability integration

---

## TelemetryFlow Ecosystem

```mermaid
graph LR
    subgraph "TelemetryFlow Ecosystem v1.1.2"
        subgraph "Instrumentation"
            SDK_GO[TFO-Go-SDK<br/>OTEL SDK v1.39.0]
            SDK_PY[TFO-Python-SDK<br/>OTEL SDK v1.28.0]
            SDK_OTHER[TFO-AnyStacks-SDK<br/>OTEL AnyStacks SDK]
        end
        subgraph "Collection"
            AGENT[TFO-Agent<br/>OTEL SDK v1.39.0]
        end
        subgraph "Processing"
            COLLECTOR[TFO-Collector<br/>OTEL v0.142.0]
        end
        subgraph "AI Integration"
            MCP_GO[TFO-Go-MCP<br/>Claude API + MCP]
            MCP_PY[TFO-Python-MCP<br/>Claude API + MCP]
        end
        subgraph "Platform"
            CORE[TFO-Core<br/>NestJS IAM v1.1.4]
        end
    end

    SDK_GO --> AGENT
    SDK_PY --> AGENT
    SDK_OTHER --> AGENT
    AGENT --> COLLECTOR
    COLLECTOR --> CORE
    MCP_GO --> CORE
    MCP_PY --> CORE
    MCP_GO -.-> |AI Capabilities| COLLECTOR
    MCP_PY -.-> |AI Capabilities| COLLECTOR

    style MCP_GO fill:#E1BEE7,stroke:#7B1FA2
    style MCP_PY fill:#FFA1E1,stroke:#C989B4,stroke-width:5px
    style SDK_GO fill:#C8E6C9,stroke:#388E3C
    style SDK_PY fill:#C8E6C9,stroke:#388E3C
    style SDK_OTHER fill:#DFDFDF,stroke:#0F0F0F
    style AGENT fill:#BBDEFB,stroke:#1976D2
    style COLLECTOR fill:#FFE0B2,stroke:#F57C00
    style CORE fill:#B3E5FC,stroke:#0288D1
```

| Component          | Version    | OTEL Base       | Role                              |
| ------------------ | ---------- | --------------- | --------------------------------- |
| TFO-Core           | v1.1.4     | -               | Identity & Access Management      |
| TFO-Agent          | v1.1.2     | SDK v1.39.0     | Telemetry Collection Agent        |
| TFO-Collector      | v1.1.2     | v0.142.0        | Central Telemetry Processing      |
| TFO-Go-SDK         | v1.1.2     | SDK v1.39.0     | Go Instrumentation                |
| TFO-Python-SDK     | v1.1.2     | SDK v1.28.0     | Python Instrumentation            |
| TFO-Go-MCP         | v1.1.2     | SDK v1.39.0     | Go MCP Server + Claude AI         |
| **TFO-Python-MCP** | **v1.1.2** | **SDK v1.28.0** | **Python MCP Server + Claude AI** |

---

## Quick Facts

| Property             | Value                                                   |
| -------------------- | ------------------------------------------------------- |
| **Version**          | 1.1.2                                                   |
| **Language**         | Python 3.11+                                            |
| **MCP Protocol**     | 2024-11-05                                              |
| **Claude SDK**       | anthropic>=0.40.0                                       |
| **OTEL SDK**         | TelemetryFlow SDK v1.28.0                               |
| **Architecture**     | DDD/CQRS                                                |
| **Transport**        | stdio, SSE (planned), WebSocket (planned)               |
| **Built-in Tools**   | 8 tools                                                 |
| **Supported Models** | Claude 4 Opus, Claude 4 Sonnet, Claude 3.5 Sonnet/Haiku |
| **Async Runtime**    | asyncio with async/await                                |

---

## System Architecture

```mermaid
graph TB
    subgraph "Client Applications"
        CC[Claude Code]
        IDE[IDE Extensions]
        CLI[CLI Tools]
        CUSTOM[Custom MCP Clients]
    end

    subgraph "TFO-Python-MCP Server"
        subgraph "Presentation Layer"
            SERVER[MCP Server<br/>JSON-RPC 2.0]
            TOOLS[Built-in Tools]
            RESOURCES[Resources]
            PROMPTS[Prompts]
        end

        subgraph "Application Layer - CQRS"
            CMD[Commands]
            QRY[Queries]
            HANDLERS[Handlers]
        end

        subgraph "Domain Layer - DDD"
            AGG[Aggregates<br/>Session, Conversation]
            ENT[Entities<br/>Message, Tool, Resource]
            VO[Value Objects<br/>IDs, Content, Types]
            EVT[Domain Events]
            SVC[Domain Services]
        end

        subgraph "Infrastructure Layer"
            CLAUDE[Claude API Client]
            CONFIG[Configuration<br/>Pydantic Settings]
            REPO[Repositories]
            LOG[Structured Logging<br/>structlog]
            OTEL[TelemetryFlow SDK]
        end
    end

    subgraph "External Services"
        ANTHROPIC[Anthropic Claude API]
        TFO[TelemetryFlow Platform]
    end

    CC --> SERVER
    IDE --> SERVER
    CLI --> SERVER
    CUSTOM --> SERVER

    SERVER --> CMD
    SERVER --> QRY
    TOOLS --> HANDLERS
    RESOURCES --> HANDLERS
    PROMPTS --> HANDLERS

    HANDLERS --> AGG
    HANDLERS --> SVC
    AGG --> ENT
    AGG --> VO
    AGG --> EVT

    SVC --> CLAUDE
    HANDLERS --> REPO
    CONFIG --> SERVER
    LOG --> SERVER
    OTEL --> TFO

    CLAUDE --> ANTHROPIC

    style SERVER fill:#3776AB,stroke:#FFD43B,stroke-width:2px
    style CLAUDE fill:#FFCDD2,stroke:#C62828
    style ANTHROPIC fill:#FFCDD2,stroke:#C62828
    style AGG fill:#C8E6C9,stroke:#388E3C
    style HANDLERS fill:#BBDEFB,stroke:#1976D2
    style OTEL fill:#E1BEE7,stroke:#7B1FA2
```

---

## Built-in Tools

```mermaid
graph TB
    subgraph "Tool Registry"
        REG[Tool Registry<br/>Manages all tools]
    end

    subgraph "AI Tools"
        T1[claude_conversation<br/>AI-powered chat]
    end

    subgraph "File Tools"
        T2[read_file<br/>Read file contents]
        T3[write_file<br/>Write to files]
        T4[list_directory<br/>List directory]
        T5[search_files<br/>Search by pattern]
    end

    subgraph "System Tools"
        T6[execute_command<br/>Run shell commands]
        T7[system_info<br/>System information]
    end

    subgraph "Utility Tools"
        T8[echo<br/>Testing utility]
    end

    REG --> T1
    REG --> T2
    REG --> T3
    REG --> T4
    REG --> T5
    REG --> T6
    REG --> T7
    REG --> T8

    style T1 fill:#E1BEE7,stroke:#7B1FA2,stroke-width:2px
    style REG fill:#FFE0B2,stroke:#F57C00
```

### Tool Reference

| Tool                  | Category | Description                | Key Parameters                      |
| --------------------- | -------- | -------------------------- | ----------------------------------- |
| `claude_conversation` | AI       | Send messages to Claude AI | `message`, `model`, `system_prompt` |
| `read_file`           | File     | Read file contents         | `path`, `encoding`                  |
| `write_file`          | File     | Write content to file      | `path`, `content`, `create_dirs`    |
| `list_directory`      | File     | List directory contents    | `path`, `recursive`                 |
| `search_files`        | File     | Search files by pattern    | `path`, `pattern`                   |
| `execute_command`     | System   | Execute shell commands     | `command`, `working_dir`, `timeout` |
| `system_info`         | System   | Get system information     | -                                   |
| `echo`                | Utility  | Echo input (testing)       | `message`                           |

---

## Built-in Resources

| Resource          | Description            |
| ----------------- | ---------------------- |
| `config://server` | Server configuration   |
| `status://health` | Health status          |
| `file:///{path}`  | File access (template) |

---

## Built-in Prompts

| Prompt         | Description              |
| -------------- | ------------------------ |
| `code_review`  | Get thorough code review |
| `explain_code` | Get code explanation     |
| `debug_help`   | Get debugging assistance |

---

## Installation

### Prerequisites

- Python 3.11 or later
- Anthropic API key

### From Source

```bash
# Clone the repository
git clone https://github.com/telemetryflow/telemetryflow-python-mcp.git
cd telemetryflow-python-mcp

# Install package
pip install -e .

# Or with all optional dependencies
pip install -e ".[all]"

# Or with telemetry support only
pip install -e ".[telemetry]"
```

### Using pip

```bash
pip install tfo-mcp
```

### Docker

```bash
# Build image
docker build -t telemetryflow-python-mcp:1.1.2 .

# Run container
docker run --rm -it \
  -e ANTHROPIC_API_KEY="your-api-key" \
  telemetryflow-python-mcp:1.1.2
```

---

## Configuration

### Configuration File

Create `tfo-mcp.yaml` or run `tfo-mcp init-config`:

```yaml
# =============================================================================
# TelemetryFlow Python MCP Server Configuration
# Version: 1.1.2
# =============================================================================

server:
  name: "TelemetryFlow-MCP"
  version: "1.1.2"
  transport: "stdio" # stdio, sse, websocket
  debug: false

claude:
  # api_key: Set via ANTHROPIC_API_KEY env var
  default_model: "claude-sonnet-4-20250514"
  max_tokens: 4096
  temperature: 1.0
  timeout: 120.0
  max_retries: 3

mcp:
  protocol_version: "2024-11-05"
  enable_tools: true
  enable_resources: true
  enable_prompts: true
  enable_logging: true
  tool_timeout: 30.0

logging:
  level: "info" # debug, info, warn, error
  format: "json" # json, text
  output: "stderr"

telemetry:
  enabled: false
  api_key_id: "" # or TELEMETRYFLOW_API_KEY_ID env var
  api_key_secret: "" # or TELEMETRYFLOW_API_KEY_SECRET env var
  endpoint: "api.telemetryflow.id:4317"
  service_name: "telemetryflow-python-mcp"
  environment: "production"
```

### Environment Variables

| Variable                                 | Description               | Default                     |
| ---------------------------------------- | ------------------------- | --------------------------- |
| `ANTHROPIC_API_KEY`                      | Claude API key (required) | -                           |
| `TELEMETRYFLOW_MCP_SERVER_DEBUG`         | Debug mode                | `false`                     |
| `TELEMETRYFLOW_MCP_LOG_LEVEL`            | Log level                 | `info`                      |
| `TELEMETRYFLOW_MCP_CLAUDE_DEFAULT_MODEL` | Default Claude model      | `claude-sonnet-4-20250514`  |
| `TELEMETRYFLOW_ENABLED`                  | Enable telemetry          | `false`                     |
| `TELEMETRYFLOW_API_KEY_ID`               | TelemetryFlow API key ID  | -                           |
| `TELEMETRYFLOW_API_KEY_SECRET`           | TelemetryFlow API secret  | -                           |
| `TELEMETRYFLOW_ENDPOINT`                 | OTLP endpoint             | `api.telemetryflow.id:4317` |

---

## Usage

### Running the Server

```bash
# Run with default config
tfo-mcp serve

# Run with custom config
tfo-mcp serve --config /path/to/config.yaml

# Run in debug mode
tfo-mcp serve --debug

# Show version
tfo-mcp --version

# Validate configuration
tfo-mcp validate

# Show server info
tfo-mcp info

# Generate default config
tfo-mcp init-config
```

### Integration with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "telemetryflow": {
      "command": "tfo-mcp",
      "args": ["serve"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key"
      }
    }
  }
}
```

---

## TelemetryFlow SDK Integration

The MCP server integrates with the TelemetryFlow Python SDK to provide comprehensive observability:

### Enable Telemetry

```bash
# Install with telemetry support
pip install -e ".[telemetry]"

# Configure via environment variables
export TELEMETRYFLOW_ENABLED=true
export TELEMETRYFLOW_API_KEY_ID=tfk_your-key-id
export TELEMETRYFLOW_API_KEY_SECRET=tfs_your-secret-key
export TELEMETRYFLOW_ENDPOINT=api.telemetryflow.id:4317
```

### Collected Telemetry

| Signal  | Metric/Span           | Description                   |
| ------- | --------------------- | ----------------------------- |
| Metrics | `mcp.tools.calls`     | Tool call count by tool name  |
| Metrics | `mcp.tools.duration`  | Tool execution duration       |
| Metrics | `mcp.tools.errors`    | Tool error count              |
| Metrics | `mcp.resources.reads` | Resource read count           |
| Metrics | `mcp.prompts.gets`    | Prompt get count              |
| Metrics | `mcp.sessions.events` | Session lifecycle events      |
| Traces  | `mcp.tools.execute.*` | Tool execution spans          |
| Logs    | Various               | Structured logs for debugging |

---

## Project Structure

```
telemetryflow-python-mcp/
├── src/tfo_mcp/
│   ├── domain/                    # Domain Layer (DDD)
│   │   ├── aggregates/            # Session, Conversation aggregates
│   │   ├── entities/              # Message, Tool, Resource, Prompt
│   │   ├── valueobjects/          # Immutable value objects
│   │   ├── events/                # Domain events
│   │   ├── repositories/          # Repository interfaces
│   │   └── services/              # Domain service interfaces
│   ├── application/               # Application Layer (CQRS)
│   │   ├── commands/              # Write operations
│   │   ├── queries/               # Read operations
│   │   └── handlers/              # Command/Query handlers
│   ├── infrastructure/            # Infrastructure Layer
│   │   ├── claude/                # Claude API client
│   │   ├── config/                # Pydantic configuration
│   │   ├── logging/               # Structured logging
│   │   ├── persistence/           # Repository implementations
│   │   └── telemetry/             # TelemetryFlow SDK integration
│   ├── presentation/              # Presentation Layer
│   │   ├── server/                # MCP server implementation
│   │   ├── tools/                 # Built-in tools
│   │   ├── resources/             # Built-in resources
│   │   └── prompts/               # Built-in prompts
│   └── main.py                    # CLI entry point
├── configs/                       # Configuration files
├── tests/                         # Test suites
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
├── docs/                          # Documentation
├── .kiro/                         # Specifications and steering
├── Makefile                       # Build automation
├── Dockerfile                     # Container build
├── docker-compose.yaml            # Development stack
├── pyproject.toml                 # Python package config
└── .env.example                   # Environment template
```

---

## Development

### Make Commands

```bash
# Development
make deps               # Install dependencies
make dev                # Install with dev dependencies
make setup              # Full development setup

# Code Quality
make fmt                # Format code (black + ruff)
make lint               # Run linters
make typecheck          # Run mypy type checking

# Testing
make test               # Run all tests
make test-unit          # Run unit tests
make test-integration   # Run integration tests
make test-cov           # Tests with coverage

# CI/CD
make ci-test            # Full CI test pipeline
make ci-lint            # CI lint pipeline
make ci-security        # Security scanning

# Docker
make docker-build       # Build Docker image
make docker-run         # Run Docker container
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/unit/test_config.py -v

# Run CI test pipeline
make ci-test
```

---

## MCP Capabilities Matrix

| Capability              | Status | Description                   |
| ----------------------- | ------ | ----------------------------- |
| `tools`                 | ✅     | Tool listing and execution    |
| `tools.listChanged`     | ✅     | Dynamic tool registration     |
| `resources`             | ✅     | Resource listing and reading  |
| `resources.subscribe`   | ✅     | Resource change subscriptions |
| `resources.listChanged` | ✅     | Dynamic resource registration |
| `prompts`               | ✅     | Prompt templates              |
| `prompts.listChanged`   | ✅     | Dynamic prompt registration   |
| `logging`               | ✅     | Log level management          |
| `sampling`              | 🔜     | LLM sampling (planned)        |

---

## Claude AI Integration

### Supported Models

| Model             | ID                           | Use Case                       |
| ----------------- | ---------------------------- | ------------------------------ |
| Claude 4 Opus     | `claude-opus-4-20250514`     | Complex reasoning, analysis    |
| Claude 4 Sonnet   | `claude-sonnet-4-20250514`   | Balanced performance (default) |
| Claude 3.7 Sonnet | `claude-3-7-sonnet-20250219` | Extended thinking              |
| Claude 3.5 Sonnet | `claude-3-5-sonnet-20241022` | Fast, capable                  |
| Claude 3.5 Haiku  | `claude-3-5-haiku-20241022`  | Quick responses                |

---

## Security Considerations

| Aspect                | Implementation                        |
| --------------------- | ------------------------------------- |
| **API Key Storage**   | Environment variables only            |
| **Command Execution** | Configurable timeout, path validation |
| **File Access**       | Path validation, no traversal         |
| **Rate Limiting**     | Configurable per-minute limits        |
| **Input Validation**  | Pydantic validation for all inputs    |

---

## Documentation Index

| Document                                       | Description                         |
| ---------------------------------------------- | ----------------------------------- |
| [README.md](README.md)                         | Project overview and quick start    |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)   | Detailed architecture documentation |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Configuration reference             |
| [docs/COMMANDS.md](docs/COMMANDS.md)           | CLI commands reference              |
| [CONTRIBUTING.md](CONTRIBUTING.md)             | Contribution guidelines             |
| [SECURITY.md](SECURITY.md)                     | Security policy                     |
| [CHANGELOG.md](CHANGELOG.md)                   | Version history                     |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow Python best practices and PEP 8
- Use DDD patterns for domain logic
- Write unit tests for all handlers
- Document public APIs
- Keep commits atomic and well-described

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Related Projects

- [TelemetryFlow Go MCP](https://github.com/telemetryflow/telemetryflow-go-mcp) - Go implementation
- [TelemetryFlow Python SDK](https://github.com/telemetryflow/telemetryflow-python-sdk) - Python observability SDK
- [TelemetryFlow Go SDK](https://github.com/telemetryflow/telemetryflow-go-sdk) - Go observability SDK
- [TelemetryFlow Platform](https://github.com/telemetryflow/telemetryflow) - Main platform

---

## Support

- **Documentation**: [TelemetryFlow Docs](https://docs.telemetryflow.id)
- **Issues**: [GitHub Issues](https://github.com/telemetryflow/telemetryflow-python-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/telemetryflow/telemetryflow-python-mcp/discussions)

---

<p align="center">
  <strong>Built with Python and Claude AI integration for the TelemetryFlow Platform</strong>
  <br/>
  <sub>Copyright &copy; 2024-2026 DevOpsCorner Indonesia. All rights reserved.</sub>
</p>
