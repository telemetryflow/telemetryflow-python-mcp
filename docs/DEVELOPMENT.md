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
│   │   └── handlers/     # Command/Query handlers
│   ├── infrastructure/   # Infrastructure Layer
│   │   ├── claude/       # Claude API client
│   │   ├── config/       # Configuration management
│   │   ├── logging/      # Structured logging
│   │   ├── cache/        # Redis cache (optional)
│   │   ├── queue/        # NATS queue (optional)
│   │   └── persistence/  # Repository implementations
│   ├── presentation/     # Presentation Layer
│   │   ├── server/       # MCP JSON-RPC server
│   │   ├── tools/        # Built-in tools
│   │   ├── resources/    # Built-in resources
│   │   └── prompts/      # Built-in prompts
│   └── main.py           # CLI entry point
├── tests/                # Test suite
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

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
pytest tests/unit/test_domain.py -v

# Specific test
pytest tests/unit/test_domain.py::TestSession::test_create_session -v
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

### 2. Add to BUILTIN_TOOLS

```python
BUILTIN_TOOLS.append({
    "name": "my_tool",
    "description": "Description of my tool",
    "category": "utility",
    "tags": ["my", "tool"],
    "input_schema": {
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "The parameter",
            }
        },
        "required": ["param"],
    },
    "handler": _my_tool_handler,
})
```

### 3. Add Tests

```python
# tests/unit/test_tools.py

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

### 2. Register in register_builtin_resources

```python
def register_builtin_resources(session: "Session", config: "Config") -> None:
    # ... existing resources ...

    my_resource = Resource.create(
        uri="my://resource",
        name="My Resource",
        description="Description",
        mime_type=MimeType.APPLICATION_JSON,
        reader=_my_resource_reader,
    )
    session.register_resource(my_resource)
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

### 2. Register in register_builtin_prompts

```python
def register_builtin_prompts(session: "Session") -> None:
    # ... existing prompts ...

    my_prompt = Prompt.create(
        name="my_prompt",
        description="My prompt description",
        arguments=[
            PromptArgument(
                name="topic",
                description="The topic",
                required=True,
            ),
        ],
        generator=_my_prompt_generator,
    )
    session.register_prompt(my_prompt)
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

### Infrastructure Layer Rules

1. **Implement domain interfaces** - Repository implementations here
2. **Handle external concerns** - HTTP, database, caching
3. **Configuration here** - Environment, files, defaults

### Presentation Layer Rules

1. **Protocol handling only** - JSON-RPC parsing, validation
2. **Delegate to application layer** - Don't implement business logic
3. **Tools are self-contained** - Each tool is independent

## Testing Guidelines

### Unit Tests

- Test domain entities and value objects
- Test tool handlers in isolation
- Mock external dependencies

### Integration Tests

- Test handler integration
- Test server request handling
- Use in-memory repositories

### End-to-End Tests

- Test full JSON-RPC flow
- Test with real stdio
- Test error scenarios

## Release Process

1. Update version in `pyproject.toml` and `src/tfo_mcp/__init__.py`
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
