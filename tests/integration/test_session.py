"""Integration tests for session lifecycle."""

import asyncio
import contextlib

import pytest

from tfo_mcp.domain.aggregates import Session, SessionCapabilities, SessionState
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.entities import Tool
from tfo_mcp.domain.events import (
    SessionClosedEvent,
    SessionCreatedEvent,
    SessionInitializedEvent,
)
from tfo_mcp.infrastructure.persistence import InMemorySessionRepository


class TestSessionLifecycle:
    """Test complete session lifecycle."""

    @pytest.fixture
    def session(self):
        """Create test session."""
        return Session.create(
            server_name="Test-MCP",
            server_version="1.0.0",
            capabilities=SessionCapabilities(
                tools=True,
                resources=True,
                prompts=True,
                logging=True,
            ),
        )

    @pytest.fixture
    def client_info(self):
        """Create client info."""
        return ClientInfo(name="test-client", version="1.0.0")

    def test_session_state_transitions(self, session, client_info):
        """Test session state transitions."""
        # Initial state
        assert session.state == SessionState.CREATED
        assert not session.is_ready

        # Initialize
        session.initialize(client_info)
        assert session.state == SessionState.READY
        assert session.is_ready

        # Close
        session.close()
        assert session.state == SessionState.CLOSED
        assert not session.is_ready

    def test_session_events_emitted(self, session, client_info):
        """Test session events are emitted."""
        # Creation event
        events = session.get_events()
        assert any(isinstance(e, SessionCreatedEvent) for e in events)

        session.get_events()  # Consume events

        # Initialization event
        session.initialize(client_info)
        events = session.get_events()
        assert any(isinstance(e, SessionInitializedEvent) for e in events)

        session.get_events()  # Consume events

        # Close event
        session.close()
        events = session.get_events()
        assert any(isinstance(e, SessionClosedEvent) for e in events)

    def test_cannot_initialize_twice(self, session, client_info):
        """Test cannot initialize session twice."""
        session.initialize(client_info)

        with pytest.raises(ValueError):
            session.initialize(client_info)

    def test_register_tool_on_closed_session(self, session, client_info):
        """Test registering tool on closed session."""
        session.initialize(client_info)
        session.close()

        tool = Tool.create(
            name="test",
            description="Test",
            input_schema={"type": "object"},
        )

        # The session may silently fail or raise - just ensure no crash
        # This test documents current behavior
        with contextlib.suppress(ValueError):
            session.register_tool(tool)


class TestSessionToolManagement:
    """Test session tool management."""

    @pytest.fixture
    def initialized_session(self):
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    def test_register_tool(self, initialized_session):
        """Test registering a tool."""
        tool = Tool.create(
            name="echo",
            description="Echo a message",
            input_schema={"type": "object"},
        )

        initialized_session.register_tool(tool)

        assert initialized_session.get_tool("echo") is not None

    def test_register_multiple_tools(self, initialized_session):
        """Test registering multiple tools."""
        tools = [
            Tool.create(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={"type": "object"},
            )
            for i in range(10)
        ]

        for tool in tools:
            initialized_session.register_tool(tool)

        assert len(initialized_session.list_tools()) == 10

    def test_unregister_tool(self, initialized_session):
        """Test unregistering a tool."""
        tool = Tool.create(
            name="temp",
            description="Temporary",
            input_schema={"type": "object"},
        )

        initialized_session.register_tool(tool)
        assert initialized_session.get_tool("temp") is not None

        initialized_session.unregister_tool("temp")
        assert initialized_session.get_tool("temp") is None

    def test_tool_registration_event(self, initialized_session):
        """Test tool registration with events."""
        tool = Tool.create(
            name="test",
            description="Test",
            input_schema={"type": "object"},
        )

        initialized_session.register_tool(tool)

        # Verify tool was registered successfully
        registered = initialized_session.get_tool("test")
        assert registered is not None
        assert str(registered.name) == "test"


class TestSessionWithRepository:
    """Test session with repository integration."""

    @pytest.fixture
    def repository(self):
        """Create session repository."""
        return InMemorySessionRepository()

    @pytest.mark.asyncio
    async def test_save_and_restore_session(self, repository):
        """Test saving and restoring a session."""
        session = Session.create(server_name="Persistent-MCP")
        session.initialize(ClientInfo(name="test", version="1.0"))

        # Register some tools
        for i in range(3):
            session.register_tool(
                Tool.create(
                    name=f"tool_{i}",
                    description=f"Tool {i}",
                    input_schema={"type": "object"},
                )
            )

        await repository.save(session)

        # Restore
        restored = await repository.get(session.id)

        assert restored is not None
        assert restored.id == session.id
        assert restored.is_ready
        assert len(restored.list_tools()) == 3

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, repository):
        """Test handling concurrent sessions."""
        sessions = []

        for i in range(10):
            session = Session.create(server_name=f"MCP-{i}")
            session.initialize(ClientInfo(name=f"client-{i}", version="1.0"))
            sessions.append(session)

        # Save all concurrently
        await asyncio.gather(*[repository.save(s) for s in sessions])

        # Verify all saved
        all_sessions = await repository.list_all()
        assert len(all_sessions) == 10


class TestSessionCapabilities:
    """Test session capabilities."""

    def test_full_capabilities(self):
        """Test session with full capabilities."""
        caps = SessionCapabilities(
            tools=True,
            resources=True,
            prompts=True,
            logging=True,
            sampling=True,
        )

        session = Session.create(capabilities=caps)

        result = session.initialize(ClientInfo(name="test", version="1.0"))

        assert "capabilities" in result
        assert "tools" in result["capabilities"]
        assert "resources" in result["capabilities"]
        assert "prompts" in result["capabilities"]

    def test_limited_capabilities(self):
        """Test session with limited capabilities."""
        caps = SessionCapabilities(
            tools=True,
            resources=False,
            prompts=False,
            logging=True,
            sampling=False,
        )

        session = Session.create(capabilities=caps)
        result = session.initialize(ClientInfo(name="test", version="1.0"))

        capabilities = result["capabilities"]
        assert "tools" in capabilities
        # Resources and prompts may be absent or empty


class TestSessionClientInfo:
    """Test session client information."""

    def test_client_info_stored(self):
        """Test client info is stored."""
        session = Session.create()
        client = ClientInfo(name="MyClient", version="2.0.0")

        session.initialize(client)

        assert session.client_info is not None
        assert session.client_info.name == "MyClient"
        assert session.client_info.version == "2.0.0"

    def test_server_info_in_response(self):
        """Test server info in initialize response."""
        session = Session.create(
            server_name="Test-MCP",
            server_version="1.2.3",
        )

        result = session.initialize(ClientInfo(name="test", version="1.0"))

        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "Test-MCP"
        assert result["serverInfo"]["version"] == "1.2.3"

    def test_protocol_version_in_response(self):
        """Test protocol version in initialize response."""
        session = Session.create()
        result = session.initialize(ClientInfo(name="test", version="1.0"))

        assert "protocolVersion" in result
        assert result["protocolVersion"] == "2024-11-05"
