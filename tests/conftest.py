"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from io import StringIO
from typing import Any
from unittest import mock

import pytest

from tfo_mcp.domain.aggregates import Conversation, Session, SessionCapabilities
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.entities import Message, Prompt, PromptArgument, Resource, Tool
from tfo_mcp.domain.valueobjects import MimeType
from tfo_mcp.infrastructure.config import (
    ClaudeConfig,
    Config,
    LoggingConfig,
    MCPConfig,
    ServerConfig,
    TelemetryConfig,
)
from tfo_mcp.infrastructure.persistence import (
    InMemoryConversationRepository,
    InMemoryPromptRepository,
    InMemoryResourceRepository,
    InMemorySessionRepository,
    InMemoryToolRepository,
)

# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def config() -> Config:
    """Create a test configuration."""
    return Config()


@pytest.fixture
def debug_config() -> Config:
    """Create a debug-enabled configuration."""
    return Config(
        server=ServerConfig(name="Test-MCP", version="1.0.0", debug=True),
        logging=LoggingConfig(level="debug"),
    )


@pytest.fixture
def minimal_config() -> Config:
    """Create minimal configuration with disabled features."""
    return Config(
        mcp=MCPConfig(
            enable_tools=False,
            enable_resources=False,
            enable_prompts=False,
        )
    )


@pytest.fixture
def claude_config() -> ClaudeConfig:
    """Create Claude API configuration."""
    return ClaudeConfig(
        api_key="test-api-key",
        default_model="claude-sonnet-4-20250514",
        max_tokens=4096,
    )


@pytest.fixture
def telemetry_config() -> TelemetryConfig:
    """Create telemetry configuration."""
    return TelemetryConfig(
        enabled=True,
        service_name="test-mcp",
        service_version="1.0.0",
    )


# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture
def session_repository() -> InMemorySessionRepository:
    """Create an in-memory session repository."""
    return InMemorySessionRepository()


@pytest.fixture
def conversation_repository() -> InMemoryConversationRepository:
    """Create an in-memory conversation repository."""
    return InMemoryConversationRepository()


@pytest.fixture
def tool_repository() -> InMemoryToolRepository:
    """Create an in-memory tool repository."""
    return InMemoryToolRepository()


@pytest.fixture
def resource_repository() -> InMemoryResourceRepository:
    """Create an in-memory resource repository."""
    return InMemoryResourceRepository()


@pytest.fixture
def prompt_repository() -> InMemoryPromptRepository:
    """Create an in-memory prompt repository."""
    return InMemoryPromptRepository()


# =============================================================================
# Session Fixtures
# =============================================================================


@pytest.fixture
def client_info() -> ClientInfo:
    """Create standard client info."""
    return ClientInfo(name="test-client", version="1.0.0")


@pytest.fixture
def session() -> Session:
    """Create a test session."""
    return Session.create(
        server_name="Test-MCP",
        server_version="1.0.0",
        capabilities=SessionCapabilities(),
    )


@pytest.fixture
def initialized_session(session: Session, client_info: ClientInfo) -> Session:
    """Create an initialized test session."""
    session.initialize(client_info)
    return session


@pytest.fixture
def session_with_tools(initialized_session: Session) -> Session:
    """Create session with registered tools."""
    for i in range(3):
        tool = Tool.create(
            name=f"tool_{i}",
            description=f"Test tool {i}",
            input_schema={"type": "object"},
        )
        initialized_session.register_tool(tool)
    return initialized_session


@pytest.fixture
def closed_session(initialized_session: Session) -> Session:
    """Create a closed session."""
    initialized_session.close()
    return initialized_session


# =============================================================================
# Tool Fixtures
# =============================================================================


@pytest.fixture
def simple_tool() -> Tool:
    """Create a simple tool for testing."""
    return Tool.create(
        name="echo",
        description="Echo a message back",
        input_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    )


@pytest.fixture
def complex_tool() -> Tool:
    """Create a complex tool with all options."""

    async def handler(input_data: dict[str, Any]) -> Any:
        from tfo_mcp.domain.entities import ToolResult

        return ToolResult.text(f"Processed: {input_data}")

    return Tool.create(
        name="process_data",
        description="Process data with multiple options",
        input_schema={
            "type": "object",
            "properties": {
                "data": {"type": "string"},
                "format": {"type": "string", "enum": ["json", "yaml", "xml"]},
                "validate": {"type": "boolean", "default": True},
                "timeout": {"type": "integer", "minimum": 1, "maximum": 300},
            },
            "required": ["data"],
        },
        handler=handler,
        category="processing",
        tags=["data", "transform"],
        timeout_seconds=60.0,
    )


@pytest.fixture
def tool_collection() -> list[Tool]:
    """Create a collection of tools for batch testing."""
    return [
        Tool.create(
            name=f"tool_{i}",
            description=f"Test tool {i}",
            input_schema={"type": "object"},
            category=["file", "system", "ai"][i % 3],
        )
        for i in range(10)
    ]


# =============================================================================
# Resource Fixtures
# =============================================================================


@pytest.fixture
def static_resource() -> Resource:
    """Create a static resource."""
    return Resource.create(
        uri="config://test",
        name="Test Config",
        description="Test configuration resource",
        mime_type=MimeType.APPLICATION_JSON,
    )


@pytest.fixture
def template_resource() -> Resource:
    """Create a template resource."""
    return Resource.template(
        uri_template="file:///{path}",
        name="File Reader",
        description="Read files from the filesystem",
        mime_type=MimeType.TEXT_PLAIN,
    )


# =============================================================================
# Prompt Fixtures
# =============================================================================


@pytest.fixture
def simple_prompt() -> Prompt:
    """Create a simple prompt."""
    return Prompt.create(
        name="greet",
        description="Generate a greeting",
        arguments=[
            PromptArgument(name="name", description="Name to greet", required=True),
        ],
    )


@pytest.fixture
def complex_prompt() -> Prompt:
    """Create a complex prompt with multiple arguments."""
    return Prompt.create(
        name="code_review",
        description="Review code for quality and issues",
        arguments=[
            PromptArgument(name="code", description="Code to review", required=True),
            PromptArgument(name="language", description="Programming language", required=False),
            PromptArgument(name="focus", description="Focus areas", required=False),
        ],
    )


# =============================================================================
# Message Fixtures
# =============================================================================


@pytest.fixture
def user_message() -> Message:
    """Create a user message."""
    return Message.user("Hello, how can you help me?")


@pytest.fixture
def assistant_message() -> Message:
    """Create an assistant message."""
    return Message.assistant("I'm here to help! What would you like to know?")


@pytest.fixture
def conversation_messages() -> list[Message]:
    """Create a conversation with multiple messages."""
    return [
        Message.user("What is Python?"),
        Message.assistant("Python is a high-level programming language."),
        Message.user("Can you give an example?"),
        Message.assistant("Sure! Here's a simple example:\n```python\nprint('Hello')\n```"),
    ]


@pytest.fixture
def conversation(conversation_messages: list[Message]) -> Conversation:
    """Create a conversation with messages."""
    conv = Conversation.create()
    for msg in conversation_messages:
        conv.add_message(msg)
    return conv


# =============================================================================
# I/O Fixtures
# =============================================================================


@pytest.fixture
def stdin() -> StringIO:
    """Create a mock stdin."""
    return StringIO()


@pytest.fixture
def stdout() -> StringIO:
    """Create a mock stdout."""
    return StringIO()


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_claude_client() -> mock.MagicMock:
    """Create a mock Claude client."""
    client = mock.MagicMock()
    client.create_message = mock.AsyncMock(return_value=Message.assistant("Mock response"))
    client.create_message_stream = mock.MagicMock()
    client.count_tokens = mock.AsyncMock(return_value=100)
    return client


@pytest.fixture
def mock_telemetry_client() -> mock.MagicMock:
    """Create a mock telemetry client."""
    client = mock.MagicMock()
    client.is_enabled = True
    client.record_tool_execution = mock.MagicMock()
    client.record_resource_read = mock.MagicMock()
    client.record_prompt_get = mock.MagicMock()
    client.record_session_event = mock.MagicMock()
    client.increment_counter = mock.MagicMock()
    client.log_error = mock.MagicMock()
    return client


# =============================================================================
# Async Handler Fixtures
# =============================================================================


@pytest.fixture
def async_tool_handler():
    """Create an async tool handler for testing."""

    async def handler(input_data: dict[str, Any]) -> Any:
        import asyncio

        from tfo_mcp.domain.entities import ToolResult

        await asyncio.sleep(0.01)  # Simulate async work
        return ToolResult.text(f"Async result: {input_data}")

    return handler


@pytest.fixture
def error_tool_handler():
    """Create a tool handler that raises an error."""

    async def handler(_input_data: dict[str, Any]) -> Any:
        raise ValueError("Simulated tool error")

    return handler
