"""Session command and query handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from tfo_mcp.domain.aggregates import Session, SessionCapabilities
from tfo_mcp.domain.aggregates.session import ClientInfo

if TYPE_CHECKING:
    from tfo_mcp.application.commands import (
        CloseSessionCommand,
        InitializeSessionCommand,
        SetLogLevelCommand,
    )
    from tfo_mcp.application.queries import GetSessionQuery, GetSessionStatsQuery, ListSessionsQuery
    from tfo_mcp.domain.repositories import ISessionRepository


logger = structlog.get_logger(__name__)


class SessionHandler:
    """Handler for session commands and queries."""

    def __init__(
        self,
        session_repository: ISessionRepository,
        server_name: str = "TelemetryFlow-MCP",
        server_version: str = "1.1.2",
        capabilities: SessionCapabilities | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._server_name = server_name
        self._server_version = server_version
        self._capabilities = capabilities or SessionCapabilities()
        self._current_session: Session | None = None

    @property
    def current_session(self) -> Session | None:
        """Get the current session."""
        return self._current_session

    async def handle_initialize(
        self,
        command: InitializeSessionCommand,
    ) -> dict[str, Any]:
        """Handle session initialization command."""
        logger.info(
            "Initializing session",
            client_name=command.client_name,
            client_version=command.client_version,
            protocol_version=command.protocol_version,
        )

        # Create new session
        session = Session.create(
            server_name=self._server_name,
            server_version=self._server_version,
            capabilities=self._capabilities,
        )

        # Initialize with client info
        client_info = ClientInfo(
            name=command.client_name,
            version=command.client_version,
        )
        result = session.initialize(
            client_info=client_info,
            client_capabilities=command.client_capabilities,
        )

        # Save session
        await self._session_repository.save(session)
        self._current_session = session

        logger.info(
            "Session initialized",
            session_id=str(session.id),
            protocol_version=str(session.protocol_version),
        )

        return result

    async def handle_close(
        self,
        command: CloseSessionCommand,
    ) -> None:
        """Handle session close command."""
        logger.info("Closing session", session_id=command.session_id)

        session = await self._session_repository.get_by_id(command.session_id)
        if session:
            session.close()
            await self._session_repository.save(session)
            if self._current_session and str(self._current_session.id) == command.session_id:
                self._current_session = None
            logger.info("Session closed", session_id=command.session_id)

    async def handle_set_log_level(
        self,
        command: SetLogLevelCommand,
    ) -> None:
        """Handle set log level command."""
        if self._current_session:
            self._current_session.set_log_level(command.level)
            logger.info("Log level set", level=command.level.value)

    async def get_session(
        self,
        query: GetSessionQuery,
    ) -> Session | None:
        """Handle get session query."""
        return await self._session_repository.get_by_id(query.session_id)

    async def list_sessions(
        self,
        query: ListSessionsQuery,
    ) -> list[Session]:
        """Handle list sessions query."""
        sessions = await self._session_repository.list_all()
        start = query.offset
        end = start + query.limit
        return sessions[start:end]

    async def get_session_stats(
        self,
        query: GetSessionStatsQuery,
    ) -> dict[str, Any] | None:
        """Handle get session stats query."""
        session = await self._session_repository.get_by_id(query.session_id)
        if not session:
            return None
        return {
            "id": str(session.id),
            "state": session.state.value,
            "toolCount": len(session.tools),
            "resourceCount": len(session.resources),
            "promptCount": len(session.prompts),
            "createdAt": session.created_at.isoformat(),
            "initializedAt": session.initialized_at.isoformat() if session.initialized_at else None,
        }
