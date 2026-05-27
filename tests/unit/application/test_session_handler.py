from __future__ import annotations

import pytest

from tfo_mcp.application.commands.commands import (
    CloseSessionCommand,
    InitializeSessionCommand,
    SetLogLevelCommand,
)
from tfo_mcp.application.handlers.session_handler import SessionHandler
from tfo_mcp.application.queries.queries import (
    GetSessionQuery,
    GetSessionStatsQuery,
    ListSessionsQuery,
)
from tfo_mcp.domain.aggregates import Session, SessionCapabilities
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.valueobjects import MCPLogLevel
from tfo_mcp.infrastructure.persistence.memory_repositories import InMemorySessionRepository


@pytest.fixture
def session_repo():
    return InMemorySessionRepository()


@pytest.fixture
def handler(session_repo):
    return SessionHandler(session_repo)


@pytest.fixture
def initialized_session(session_repo):
    session = Session.create()
    session.initialize(ClientInfo(name="test-client", version="1.0.0"))
    session_repo._sessions[str(session.id)] = session
    return session


class TestInit:
    def test_default_values(self, session_repo):
        h = SessionHandler(session_repo)
        assert h._server_name == "TelemetryFlow-MCP"
        assert h._server_version == "1.1.2"
        assert h._current_session is None

    def test_custom_values(self, session_repo):
        caps = SessionCapabilities(tools=False)
        h = SessionHandler(
            session_repo, server_name="Custom", server_version="2.0.0", capabilities=caps
        )
        assert h._server_name == "Custom"
        assert h._server_version == "2.0.0"
        assert h._capabilities.tools is False


class TestCurrentSession:
    def test_none_initially(self, handler):
        assert handler.current_session is None

    def test_returns_session_after_init(self, handler):
        handler._current_session = Session.create()
        assert handler.current_session is not None


class TestHandleInitialize:
    async def test_initializes_session(self, handler, session_repo):
        cmd = InitializeSessionCommand(
            client_name="test-client",
            client_version="1.0.0",
            protocol_version="2024-11-05",
        )
        result = await handler.handle_initialize(cmd)

        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert handler.current_session is not None

        sessions = await session_repo.list_all()
        assert len(sessions) == 1

    async def test_initializes_with_client_capabilities(self, handler):
        cmd = InitializeSessionCommand(
            client_name="test-client",
            client_version="2.0.0",
            protocol_version="2024-11-05",
            client_capabilities={"tools": {}},
        )
        result = await handler.handle_initialize(cmd)
        assert result is not None

    async def test_sets_current_session(self, handler):
        cmd = InitializeSessionCommand(
            client_name="test-client",
            client_version="1.0.0",
            protocol_version="2024-11-05",
        )
        await handler.handle_initialize(cmd)
        assert handler.current_session is not None
        assert handler.current_session.state.value == "ready"


class TestHandleClose:
    async def test_closes_session(self, handler, session_repo, initialized_session):
        handler._current_session = initialized_session

        cmd = CloseSessionCommand(session_id=str(initialized_session.id))
        await handler.handle_close(cmd)

        saved = await session_repo.get_by_id(str(initialized_session.id))
        assert saved.state.value == "closed"

    async def test_clears_current_session(
        self, handler, session_repo, initialized_session  # noqa: ARG002
    ):
        handler._current_session = initialized_session

        cmd = CloseSessionCommand(session_id=str(initialized_session.id))
        await handler.handle_close(cmd)
        assert handler.current_session is None

    async def test_handles_nonexistent_session(self, handler):
        cmd = CloseSessionCommand(session_id="nonexistent")
        await handler.handle_close(cmd)

    async def test_does_not_clear_if_different_session(
        self, handler, session_repo, initialized_session  # noqa: ARG002
    ):
        other_session = Session.create()
        other_session.initialize(ClientInfo(name="other", version="1.0.0"))
        handler._current_session = other_session

        cmd = CloseSessionCommand(session_id=str(initialized_session.id))
        await handler.handle_close(cmd)
        assert handler.current_session is other_session


class TestHandleSetLogLevel:
    async def test_sets_log_level(self, handler, initialized_session):
        handler._current_session = initialized_session
        cmd = SetLogLevelCommand(level=MCPLogLevel.DEBUG)
        await handler.handle_set_log_level(cmd)
        assert initialized_session.log_level == MCPLogLevel.DEBUG

    async def test_noop_when_no_session(self, handler):
        cmd = SetLogLevelCommand(level=MCPLogLevel.DEBUG)
        await handler.handle_set_log_level(cmd)


class TestGetSession:
    async def test_gets_existing(self, handler, session_repo, initialized_session):  # noqa: ARG002
        query = GetSessionQuery(session_id=str(initialized_session.id))
        result = await handler.get_session(query)
        assert result is not None
        assert str(result.id) == str(initialized_session.id)

    async def test_returns_none_for_missing(self, handler):
        query = GetSessionQuery(session_id="nonexistent")
        result = await handler.get_session(query)
        assert result is None


class TestListSessions:
    async def test_lists_all(self, handler, session_repo):
        for i in range(5):
            s = Session.create()
            s.initialize(ClientInfo(name=f"c-{i}", version="1.0.0"))
            await session_repo.save(s)

        query = ListSessionsQuery(limit=100, offset=0)
        result = await handler.list_sessions(query)
        assert len(result) == 5

    async def test_pagination(self, handler, session_repo):
        for _i in range(10):
            s = Session.create()
            await session_repo.save(s)

        query = ListSessionsQuery(limit=3, offset=5)
        result = await handler.list_sessions(query)
        assert len(result) == 3


class TestGetSessionStats:
    async def test_returns_stats(self, handler, initialized_session):
        query = GetSessionStatsQuery(session_id=str(initialized_session.id))
        result = await handler.get_session_stats(query)

        assert result is not None
        assert result["id"] == str(initialized_session.id)
        assert result["state"] == "ready"
        assert "toolCount" in result
        assert "resourceCount" in result
        assert "promptCount" in result
        assert "createdAt" in result
        assert result["initializedAt"] is not None

    async def test_returns_none_for_missing(self, handler):
        query = GetSessionStatsQuery(session_id="nonexistent")
        result = await handler.get_session_stats(query)
        assert result is None
