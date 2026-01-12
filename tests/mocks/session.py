"""Mock objects for session testing."""

from typing import Any

from tfo_mcp.domain.aggregates import Session, SessionCapabilities, SessionState
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.entities import Tool


def mock_client_info(
    name: str = "test-client",
    version: str = "1.0.0",
) -> ClientInfo:
    """Create a mock client info."""
    return ClientInfo(name=name, version=version)


def mock_session(
    server_name: str = "Test-MCP",
    server_version: str = "1.0.0",
    capabilities: SessionCapabilities | None = None,
) -> Session:
    """Create a mock session."""
    return Session.create(
        server_name=server_name,
        server_version=server_version,
        capabilities=capabilities or SessionCapabilities(),
    )


def mock_session_with_tools(
    tools: list[Tool] | None = None,
    initialized: bool = True,
) -> Session:
    """Create a mock session with pre-registered tools."""
    session = mock_session()

    if tools is None:
        tools = [
            Tool.create(
                name="echo",
                description="Echo a message",
                input_schema={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                },
            ),
            Tool.create(
                name="read_file",
                description="Read a file",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            ),
        ]

    for tool in tools:
        session.register_tool(tool)

    if initialized:
        session.initialize(mock_client_info())

    return session


def mock_initialized_session() -> Session:
    """Create an initialized mock session."""
    session = mock_session()
    session.initialize(mock_client_info())
    return session


def mock_session_stats() -> dict[str, Any]:
    """Create mock session statistics."""
    return {
        "session_id": "test-session-id",
        "state": SessionState.READY.value,
        "tool_count": 8,
        "resource_count": 3,
        "prompt_count": 3,
        "conversation_count": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "initialized_at": "2024-01-01T00:00:01Z",
    }


def mock_session_capabilities(
    tools: bool = True,
    resources: bool = True,
    prompts: bool = True,
    logging: bool = True,
    sampling: bool = False,
) -> dict[str, Any]:
    """Create mock session capabilities."""
    caps: dict[str, Any] = {}

    if tools:
        caps["tools"] = {"listChanged": True}
    if resources:
        caps["resources"] = {"subscribe": True, "listChanged": True}
    if prompts:
        caps["prompts"] = {"listChanged": True}
    if logging:
        caps["logging"] = {}
    if sampling:
        caps["sampling"] = {}

    return caps


class MockSessionFactory:
    """Factory for creating mock sessions with various configurations."""

    @staticmethod
    def create_new() -> Session:
        """Create a new session in CREATED state."""
        return mock_session()

    @staticmethod
    def create_initialized() -> Session:
        """Create an initialized session in READY state."""
        return mock_initialized_session()

    @staticmethod
    def create_with_tools(tool_count: int = 3) -> Session:
        """Create a session with a specified number of tools."""
        tools = [
            Tool.create(
                name=f"tool_{i}",
                description=f"Test tool {i}",
                input_schema={"type": "object"},
            )
            for i in range(tool_count)
        ]
        return mock_session_with_tools(tools=tools)

    @staticmethod
    def create_closed() -> Session:
        """Create a closed session."""
        session = mock_initialized_session()
        session.close()
        return session
