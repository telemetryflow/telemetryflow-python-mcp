# TelemetryFlow Python MCP Server - Development Guide

This document provides guidance for developing and contributing to the TelemetryFlow Python MCP Server.

## Prerequisites

- Python 3.11 or higher
- Git
- Make (optional, for convenience commands)

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/telemetryflow/telemetryflow-python-mcp.git
cd telemetryflow-python-mcp
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### 3. Install Development Dependencies

```bash
# Using make
make dev

# Or manually
pip install -e ".[dev]"
pre-commit install
```

### 4. Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

The synchronized `.env.example` contains **25 configuration sections** aligned with TFO Python-SDK patterns, covering MCP server, LLM, telemetry exporter, datasource, caching, queue, and Docker profile settings.

## Project Structure

```
telemetryflow-python-mcp/
├── src/tfo_mcp/
│   ├── domain/           # Domain Layer (DDD)
│   │   ├── aggregates/   # Session, Conversation
│   │   ├── entities/     # Message, Tool, Resource, Prompt
│   │   ├── valueobjects/ # IDs, MCP types, Content types
│   │   ├── events/       # Domain events
│   │   ├── repositories/ # Repository interfaces
│   │   └── services/     # Service interfaces
│   ├── application/      # Application Layer (CQRS)
│   │   ├── commands/     # Write operations
│   │   ├── queries/      # Read operations
│   │   ├── handlers/     # Command/Query handlers
│   │   └── services/     # Application services (ContextCollector, PromptBuilder)
│   ├── infrastructure/   # Infrastructure Layer
│   │   ├── claude/       # LLM API client (12 providers)
│   │   ├── config/       # Configuration management
│   │   ├── logging/      # Structured logging
│   │   ├── cache/        # Redis cache (optional)
│   │   ├── queue/        # NATS queue (optional)
│   │   └── persistence/  # Repository implementations
│   ├── presentation/     # Presentation Layer
│   │   ├── server/       # MCP server (official MCP SDK mcp>=1.27.0)
│   │   ├── tools/        # Built-in tools (17 + ContextCollector + PromptBuilder)
│   │   ├── resources/    # Built-in resources
│   │   └── prompts/      # Built-in prompts
│   └── main.py           # CLI entry point
├── tests/                # Test suite (1174 tests, 98% coverage)
│   ├── unit/             # Unit tests
│   │   ├── domain/       # Domain layer tests
│   │   ├── application/  # Application layer tests
│   │   ├── infrastructure/ # Infrastructure layer tests
│   │   └── presentation/ # Presentation layer tests
│   ├── integration/      # Integration tests
│   │   ├── datasource/   # PostgreSQL & ClickHouse tests
│   │   ├── handlers/     # Handler integration tests
│   │   └── server/       # Server integration tests
│   ├── e2e/              # End-to-end tests
│   │   ├── protocol/     # MCP protocol tests
│   │   └── flow/         # Full flow tests
│   ├── conftest.py       # Shared fixtures
│   └── __init__.py
├── configs/              # Configuration files
├── migrations/           # Database migrations
├── docs/                 # Documentation
└── pyproject.toml        # Project configuration
```

## Development Workflow

### Running the Server

```bash
# Standard run
make run

# Debug mode
make run-debug

# With custom config
tfo-mcp serve -c configs/tfo-mcp.yaml --debug
```

### Docker Compose Profiles

The project includes Docker Compose profiles for different development and deployment scenarios:

| Profile         | Services                                                                               | Use Case                    |
| --------------- | -------------------------------------------------------------------------------------- | --------------------------- |
| `dev`           | tfo-mcp + tfo-collector                                                                | Development with telemetry  |
| `full`          | dev + prometheus                                                                       | Full observability stack    |
| `platform`      | tfo-mcp + postgres + clickhouse + redis + nats + tfo-backend + tfo-viz + tfo-collector | Full TFO Platform           |
| `analytics`     | clickhouse                                                                             | ClickHouse analytics only   |
| `observability` | otel-collector + jaeger + prometheus + grafana                                         | Observability visualization |

```bash
# Development with telemetry
docker-compose --profile dev up -d

# Full observability stack
docker-compose --profile full up -d

# Full TFO Platform
docker-compose --profile platform up -d

# ClickHouse analytics only
docker-compose --profile analytics up -d

# Observability visualization
docker-compose --profile observability up -d
```

### Running Tests

```bash
# All tests (1174 tests)
make test

# With coverage (98%)
make test-cov

# Specific test directory
pytest tests/unit/domain/ -v

# Specific test file
pytest tests/unit/domain/test_aggregates.py -v

# Specific test
pytest tests/unit/domain/test_aggregates.py::TestSession::test_create_session -v
```

### Code Quality

```bash
# Run linters
make lint

# Format code
make format

# Type checking
mypy src
```

## Application Services

The `application/services/` directory contains application-level service classes that encapsulate cross-cutting concerns:

### ContextCollector

Collects and assembles telemetry context from multiple data sources, providing a unified view of observability data for prompt generation.

### PromptBuilderService

Builds system prompts and context prompts for LLM interactions, supporting 40+ specialized context types (metrics, logs, traces, alerts, Kubernetes resources, infrastructure, IAM, tenancy, database monitoring, etc.) with configurable system instructions and insight generation modes (chronology, prediction, recommendation, root-cause, pattern).

## Adding a New Tool

### 1. Define the Handler

```python
# src/tfo_mcp/presentation/tools/builtin_tools.py

async def _my_tool_handler(input_data: dict[str, Any]) -> ToolResult:
    """My tool handler."""
    param = input_data.get("param")
    if not param:
        return ToolResult.error("param is required")

    # Do something
    result = f"Processed: {param}"
    return ToolResult.text(result)
```

### 2. Register with the MCP Server

```python
# src/tfo_mcp/presentation/server/tool_registration.py

server.register_tool(
    name="my_tool",
    description="Description of my tool",
    input_schema={
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "The parameter",
            }
        },
        "required": ["param"],
    },
    handler=_my_tool_handler,
)
```

### 3. Add Tests

```python
# tests/unit/presentation/test_my_tool.py

class TestMyTool:
    @pytest.mark.asyncio
    async def test_my_tool_success(self):
        result = await _my_tool_handler({"param": "test"})
        assert not result.is_error
        assert "test" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_my_tool_missing_param(self):
        result = await _my_tool_handler({})
        assert result.is_error
```

## Adding a New Resource

### 1. Define the Reader

```python
# src/tfo_mcp/presentation/resources/builtin_resources.py

async def _my_resource_reader(uri: str, params: dict[str, str]) -> ResourceContent:
    """Read my resource."""
    data = {"key": "value"}
    return ResourceContent(
        uri=uri,
        mime_type=MimeType.APPLICATION_JSON,
        text=json.dumps(data, indent=2),
    )
```

### 2. Register with the MCP Server

```python
# src/tfo_mcp/presentation/server/resource_registration.py

server.register_resource(
    uri="my://resource",
    name="My Resource",
    description="Description",
    mime_type="application/json",
    reader=_my_resource_reader,
)
```

## Adding a New Prompt

### 1. Define the Generator

```python
# src/tfo_mcp/presentation/prompts/builtin_prompts.py

async def _my_prompt_generator(args: dict[str, str]) -> list[PromptMessage]:
    """Generate my prompt messages."""
    topic = args.get("topic", "")

    return [
        PromptMessage(
            role=Role.USER,
            content=f"Help me with {topic}",
        )
    ]
```

### 2. Register with the MCP Server

```python
# src/tfo_mcp/presentation/server/prompt_registration.py

server.register_prompt(
    name="my_prompt",
    description="My prompt description",
    arguments=[
        {
            "name": "topic",
            "description": "The topic",
            "required": True,
        },
    ],
    generator=_my_prompt_generator,
)
```

## Architecture Guidelines

### Domain Layer Rules

1. **No framework dependencies** - Domain should be pure Python
2. **Value objects are immutable** - Use `frozen=True` dataclasses
3. **Aggregates protect invariants** - Use methods to modify state
4. **Domain events for side effects** - Emit events, don't call services

### Application Layer Rules

1. **Commands change state** - One command, one change
2. **Queries are read-only** - No side effects
3. **Handlers are thin** - Orchestrate, don't implement logic
4. **Services encapsulate cross-cutting concerns** - ContextCollector and PromptBuilder coordinate across domain boundaries

### Infrastructure Layer Rules

1. **Implement domain interfaces** - Repository implementations here
2. **Handle external concerns** - HTTP, database, caching
3. **Configuration here** - Environment, files, defaults

### Presentation Layer Rules

1. **Use official MCP SDK** - `mcp>=1.27.0` for protocol handling
2. **Delegate to application layer** - Don't implement business logic
3. **Tools are self-contained** - Each tool is independent

## Testing Guidelines

### Test Organization (DDD-Aligned)

Tests are organized to mirror the domain structure:

```
tests/
├── unit/                          # Unit tests (isolated)
│   ├── domain/                    # Domain layer
│   ├── application/               # Application layer (including services/)
│   ├── infrastructure/            # Infrastructure layer
│   └── presentation/              # Presentation layer
├── integration/                   # Integration tests
│   ├── datasource/                # PostgreSQL & ClickHouse
│   ├── handlers/                  # Handler integration
│   └── server/                    # Server integration
└── e2e/                           # End-to-end tests
    ├── protocol/                  # MCP protocol
    └── flow/                      # Full flow
```

### Unit Tests

- Test domain entities and value objects
- Test tool handlers in isolation
- Test application services (ContextCollector, PromptBuilder)
- Mock external dependencies

### Integration Tests

- Test handler integration
- Test server request handling
- Test PostgreSQL and ClickHouse datasource tools
- Use in-memory repositories

### End-to-End Tests

- Test full JSON-RPC flow
- Test with real stdio
- Test error scenarios

## Release Process

1. Update version in `pyproject.toml` and `src/tfo_mcp/__init__.py` (current: 1.2.0)
2. Update CHANGELOG.md
3. Create release commit
4. Tag release
5. Build and publish

```bash
# Build
make build

# Publish (with credentials)
twine upload dist/*
```

## Troubleshooting

### Common Issues

**Import errors after changes:**

```bash
pip install -e .
```

**Type checking failures:**

```bash
mypy src --show-error-codes
```

**Test failures:**

```bash
pytest -v --tb=long
```

### Debug Mode

Enable debug logging:

```bash
tfo-mcp serve --debug
```

Or set environment:

```bash
TELEMETRYFLOW_MCP_LOG_LEVEL=debug tfo-mcp serve
```
