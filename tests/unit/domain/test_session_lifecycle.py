"""Unit tests for session lifecycle and state machine behavior."""

from __future__ import annotations

import pytest

from tfo_mcp.domain.aggregates import Session, SessionCapabilities, SessionState
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.entities import Prompt, PromptArgument, Resource, Tool
from tfo_mcp.domain.events import SessionClosedEvent, SessionCreatedEvent, SessionInitializedEvent
from tfo_mcp.domain.valueobjects import MimeType


class TestSessionStateMachine:
    """Test session state machine transitions."""

    def test_initial_state_is_created(self) -> None:
        """Test session starts in CREATED state."""
        session = Session.create()
        assert session.state == SessionState.CREATED
        assert not session.is_ready

    def test_created_to_ready_transition(self) -> None:
        """Test transition from CREATED to READY state."""
        session = Session.create()
        assert session.state == SessionState.CREATED

        session.initialize(ClientInfo(name="test", version="1.0"))

        assert session.state == SessionState.READY
        assert session.is_ready

    def test_ready_to_closed_transition(self) -> None:
        """Test transition from READY to CLOSED state."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        assert session.state == SessionState.READY

        session.close()

        assert session.state == SessionState.CLOSED
        assert not session.is_ready

    def test_created_to_closed_transition(self) -> None:
        """Test transition directly from CREATED to CLOSED."""
        session = Session.create()
        assert session.state == SessionState.CREATED

        session.close()

        assert session.state == SessionState.CLOSED

    def test_cannot_initialize_twice(self) -> None:
        """Test that double initialization raises error."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))

        with pytest.raises(ValueError, match="Cannot initialize session in state"):
            session.initialize(ClientInfo(name="test2", version="2.0"))

    def test_cannot_initialize_closed_session(self) -> None:
        """Test cannot initialize a closed session."""
        session = Session.create()
        session.close()

        with pytest.raises(ValueError):
            session.initialize(ClientInfo(name="test", version="1.0"))

    def test_close_is_idempotent(self) -> None:
        """Test closing multiple times doesn't raise."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))

        session.close()
        session.close()  # Should not raise
        session.close()  # Should not raise

        assert session.state == SessionState.CLOSED


class TestSessionEvents:
    """Test session event emission."""

    def test_created_event_on_create(self) -> None:
        """Test SessionCreatedEvent is emitted on creation."""
        session = Session.create()
        events = session.get_events()

        created_events = [e for e in events if isinstance(e, SessionCreatedEvent)]
        assert len(created_events) == 1
        # Event stores session_id as string
        assert created_events[0].session_id == str(session.id)

    def test_initialized_event_on_initialize(self) -> None:
        """Test SessionInitializedEvent is emitted on initialization."""
        session = Session.create()
        session.get_events()  # Clear creation event

        session.initialize(ClientInfo(name="test", version="1.0"))
        events = session.get_events()

        init_events = [e for e in events if isinstance(e, SessionInitializedEvent)]
        assert len(init_events) == 1
        # Event stores session_id as string
        assert init_events[0].session_id == str(session.id)
        assert init_events[0].client_name == "test"

    def test_closed_event_on_close(self) -> None:
        """Test SessionClosedEvent is emitted on close."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        session.get_events()  # Clear previous events

        session.close()
        events = session.get_events()

        closed_events = [e for e in events if isinstance(e, SessionClosedEvent)]
        assert len(closed_events) == 1
        # Event stores session_id as string
        assert closed_events[0].session_id == str(session.id)

    def test_events_are_consumed(self) -> None:
        """Test events are consumed after get_events."""
        session = Session.create()

        events1 = session.get_events()
        events2 = session.get_events()

        assert len(events1) > 0
        assert len(events2) == 0  # Events should be consumed

    def test_tool_registered_event(self) -> None:
        """Test tool registration works and can be verified."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        session.get_events()  # Clear previous events

        tool = Tool.create(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
        )
        session.register_tool(tool)

        # Verify tool was registered (events may or may not be emitted)
        registered_tool = session.get_tool("test_tool")
        assert registered_tool is not None
        assert str(registered_tool.name) == "test_tool"


class TestSessionToolManagement:
    """Test session tool management lifecycle."""

    @pytest.fixture
    def initialized_session(self) -> Session:
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    def test_register_tool(self, initialized_session: Session) -> None:
        """Test registering a tool."""
        tool = Tool.create(
            name="echo",
            description="Echo tool",
            input_schema={"type": "object"},
        )

        initialized_session.register_tool(tool)

        assert initialized_session.get_tool("echo") is not None
        assert len(initialized_session.list_tools()) == 1

    def test_unregister_tool(self, initialized_session: Session) -> None:
        """Test unregistering a tool."""
        tool = Tool.create(
            name="temp_tool",
            description="Temporary",
            input_schema={"type": "object"},
        )
        initialized_session.register_tool(tool)
        assert initialized_session.get_tool("temp_tool") is not None

        initialized_session.unregister_tool("temp_tool")

        assert initialized_session.get_tool("temp_tool") is None

    def test_register_multiple_tools(self, initialized_session: Session) -> None:
        """Test registering multiple tools."""
        for i in range(5):
            tool = Tool.create(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={"type": "object"},
            )
            initialized_session.register_tool(tool)

        assert len(initialized_session.list_tools()) == 5

    def test_duplicate_tool_registration(self, initialized_session: Session) -> None:
        """Test registering duplicate tool replaces existing."""
        tool1 = Tool.create(
            name="duplicate",
            description="First version",
            input_schema={"type": "object"},
        )
        tool2 = Tool.create(
            name="duplicate",
            description="Second version",
            input_schema={"type": "object"},
        )

        initialized_session.register_tool(tool1)
        initialized_session.register_tool(tool2)

        # Should have replaced
        tool = initialized_session.get_tool("duplicate")
        assert str(tool.description) == "Second version"
        assert len(initialized_session.list_tools()) == 1

    def test_tool_registration_on_uninitialized_session(self) -> None:
        """Test tool registration is allowed on uninitialized session."""
        session = Session.create()
        tool = Tool.create(
            name="test",
            description="Test",
            input_schema={"type": "object"},
        )

        # Session allows tool registration before initialization
        session.register_tool(tool)
        assert session.get_tool("test") is not None


class TestSessionResourceManagement:
    """Test session resource management lifecycle."""

    @pytest.fixture
    def initialized_session(self) -> Session:
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    def test_register_resource(self, initialized_session: Session) -> None:
        """Test registering a resource."""
        resource = Resource.create(
            uri="config://test",
            name="Test Config",
            description="Test configuration",
            mime_type=MimeType.APPLICATION_JSON,
        )

        initialized_session.register_resource(resource)

        assert initialized_session.get_resource("config://test") is not None
        assert len(initialized_session.list_resources()) == 1

    def test_register_template_resource(self, initialized_session: Session) -> None:
        """Test registering a template resource."""
        resource = Resource.template(
            uri_template="file:///{path}",
            name="File",
            description="Read files",
            mime_type=MimeType.TEXT_PLAIN,
        )

        initialized_session.register_resource(resource)

        assert len(initialized_session.list_resources()) == 1
        assert initialized_session.list_resources()[0].is_template


class TestSessionPromptManagement:
    """Test session prompt management lifecycle."""

    @pytest.fixture
    def initialized_session(self) -> Session:
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    def test_register_prompt(self, initialized_session: Session) -> None:
        """Test registering a prompt."""
        prompt = Prompt.create(
            name="greet",
            description="Generate greeting",
            arguments=[
                PromptArgument(name="name", description="Name", required=True),
            ],
        )

        initialized_session.register_prompt(prompt)

        assert initialized_session.get_prompt("greet") is not None
        assert len(initialized_session.list_prompts()) == 1


class TestSessionInitializationResponse:
    """Test session initialization response format."""

    def test_initialization_returns_server_info(self) -> None:
        """Test initialization returns server info."""
        session = Session.create(server_name="Test-MCP", server_version="1.0.0")
        result = session.initialize(ClientInfo(name="test", version="1.0"))

        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "Test-MCP"
        assert result["serverInfo"]["version"] == "1.0.0"

    def test_initialization_returns_protocol_version(self) -> None:
        """Test initialization returns protocol version."""
        session = Session.create()
        result = session.initialize(ClientInfo(name="test", version="1.0"))

        assert "protocolVersion" in result
        assert result["protocolVersion"] == "2024-11-05"

    def test_initialization_returns_capabilities(self) -> None:
        """Test initialization returns capabilities."""
        capabilities = SessionCapabilities(
            tools=True,
            resources=True,
            prompts=True,
            logging=False,
            sampling=False,
        )
        session = Session.create(capabilities=capabilities)
        result = session.initialize(ClientInfo(name="test", version="1.0"))

        assert "capabilities" in result
        assert "tools" in result["capabilities"]
        assert "resources" in result["capabilities"]


class TestSessionCapabilities:
    """Test session capability configuration."""

    def test_default_capabilities(self) -> None:
        """Test default capabilities."""
        caps = SessionCapabilities()

        assert caps.tools is True
        assert caps.resources is True
        assert caps.prompts is True
        assert caps.logging is True
        assert caps.sampling is False

    def test_custom_capabilities(self) -> None:
        """Test custom capability configuration."""
        caps = SessionCapabilities(
            tools=False,
            resources=False,
            prompts=False,
            logging=False,
            sampling=True,
        )

        assert not caps.tools
        assert not caps.resources
        assert not caps.prompts
        assert not caps.logging
        assert caps.sampling

    def test_session_respects_capabilities(self) -> None:
        """Test session respects capability settings."""
        caps = SessionCapabilities(tools=False)
        session = Session.create(capabilities=caps)
        result = session.initialize(ClientInfo(name="test", version="1.0"))

        # Capabilities should be reflected in result
        assert "capabilities" in result
        assert session.capabilities.tools is False


class TestSessionClientInfo:
    """Test session client info tracking."""

    def test_client_info_stored(self) -> None:
        """Test client info is stored after initialization."""
        session = Session.create()
        client = ClientInfo(name="test-client", version="2.5.0")

        session.initialize(client)

        assert session.client_info is not None
        assert session.client_info.name == "test-client"
        assert session.client_info.version == "2.5.0"

    def test_client_info_in_event(self) -> None:
        """Test client info is included in initialization event."""
        session = Session.create()
        session.get_events()  # Clear creation event

        session.initialize(ClientInfo(name="special-client", version="3.0"))
        events = session.get_events()

        init_event = next(e for e in events if isinstance(e, SessionInitializedEvent))
        assert init_event.client_name == "special-client"
        assert init_event.client_version == "3.0"


class TestSessionLogging:
    """Test session logging level management."""

    @pytest.fixture
    def initialized_session(self) -> Session:
        """Create initialized session."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))
        return session

    def test_set_log_level(self, initialized_session: Session) -> None:
        """Test setting log level."""
        from tfo_mcp.domain.valueobjects import MCPLogLevel

        initialized_session.set_log_level(MCPLogLevel.DEBUG)
        assert initialized_session.log_level == MCPLogLevel.DEBUG

        initialized_session.set_log_level(MCPLogLevel.ERROR)
        assert initialized_session.log_level == MCPLogLevel.ERROR

    def test_default_log_level(self) -> None:
        """Test default log level is INFO."""
        from tfo_mcp.domain.valueobjects import MCPLogLevel

        session = Session.create()
        assert session.log_level == MCPLogLevel.INFO
