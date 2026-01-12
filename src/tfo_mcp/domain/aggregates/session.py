"""Session aggregate root."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from tfo_mcp.domain.entities import Prompt, Resource, Tool
from tfo_mcp.domain.events import (
    DomainEvent,
    SessionClosedEvent,
    SessionCreatedEvent,
    SessionInitializedEvent,
)
from tfo_mcp.domain.valueobjects import (
    MCPCapability,
    MCPLogLevel,
    MCPProtocolVersion,
    SessionID,
)


class SessionState(str, Enum):
    """Session lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class ClientInfo:
    """MCP client information."""

    name: str
    version: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {"name": self.name, "version": self.version}


@dataclass
class ServerInfo:
    """MCP server information."""

    name: str
    version: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {"name": self.name, "version": self.version}


@dataclass
class SessionCapabilities:
    """Session capabilities configuration."""

    tools: bool = True
    resources: bool = True
    prompts: bool = True
    logging: bool = True
    sampling: bool = False
    experimental: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP capabilities format."""
        caps: dict[str, Any] = {}
        if self.tools:
            caps["tools"] = {}
        if self.resources:
            caps["resources"] = {"subscribe": True, "listChanged": True}
        if self.prompts:
            caps["prompts"] = {"listChanged": True}
        if self.logging:
            caps["logging"] = {}
        if self.sampling:
            caps["sampling"] = {}
        if self.experimental:
            caps["experimental"] = self.experimental
        return caps

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionCapabilities:
        """Create from dictionary."""
        return cls(
            tools=MCPCapability.TOOLS.value in data,
            resources=MCPCapability.RESOURCES.value in data,
            prompts=MCPCapability.PROMPTS.value in data,
            logging=MCPCapability.LOGGING.value in data,
            sampling=MCPCapability.SAMPLING.value in data,
            experimental=data.get(MCPCapability.EXPERIMENTAL.value, {}),
        )


@dataclass
class Session:
    """Session aggregate root - manages MCP session lifecycle."""

    id: SessionID
    protocol_version: MCPProtocolVersion
    state: SessionState = SessionState.CREATED
    client_info: ClientInfo | None = None
    server_info: ServerInfo | None = None
    capabilities: SessionCapabilities = field(default_factory=SessionCapabilities)
    log_level: MCPLogLevel = MCPLogLevel.INFO
    tools: dict[str, Tool] = field(default_factory=dict)
    resources: dict[str, Resource] = field(default_factory=dict)
    prompts: dict[str, Prompt] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    initialized_at: datetime | None = None
    closed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @classmethod
    def create(
        cls,
        server_name: str = "TelemetryFlow-MCP",
        server_version: str = "1.1.2",
        capabilities: SessionCapabilities | None = None,
    ) -> Session:
        """Create a new session."""
        session = cls(
            id=SessionID.generate(),
            protocol_version=MCPProtocolVersion.latest(),
            server_info=ServerInfo(name=server_name, version=server_version),
            capabilities=capabilities or SessionCapabilities(),
        )
        session._add_event(SessionCreatedEvent(session_id=str(session.id)))
        return session

    def _add_event(self, event: DomainEvent) -> None:
        """Add a domain event."""
        self._events.append(event)

    def get_events(self) -> list[DomainEvent]:
        """Get and clear pending domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    def initialize(
        self,
        client_info: ClientInfo,
        client_capabilities: dict[str, Any] | None = None,  # noqa: ARG002 - reserved for future use
    ) -> dict[str, Any]:
        """Initialize the session with client info."""
        with self._lock:
            if self.state not in (SessionState.CREATED, SessionState.INITIALIZING):
                raise ValueError(f"Cannot initialize session in state: {self.state}")

            self.state = SessionState.INITIALIZING
            self.client_info = client_info
            self.initialized_at = datetime.now(UTC)
            self.state = SessionState.READY

            self._add_event(
                SessionInitializedEvent(
                    session_id=str(self.id),
                    client_name=client_info.name,
                    client_version=client_info.version,
                )
            )

            return self._build_initialize_response()

    def _build_initialize_response(self) -> dict[str, Any]:
        """Build the initialize response."""
        return {
            "protocolVersion": str(self.protocol_version),
            "capabilities": self.capabilities.to_dict(),
            "serverInfo": self.server_info.to_dict() if self.server_info else {},
        }

    def close(self) -> None:
        """Close the session."""
        with self._lock:
            if self.state == SessionState.CLOSED:
                return

            self.state = SessionState.CLOSING
            self.closed_at = datetime.now(UTC)
            self.state = SessionState.CLOSED

            self._add_event(SessionClosedEvent(session_id=str(self.id)))

    def set_log_level(self, level: MCPLogLevel) -> None:
        """Set the session log level."""
        with self._lock:
            self.log_level = level

    def register_tool(self, tool: Tool) -> None:
        """Register a tool with the session."""
        with self._lock:
            self.tools[str(tool.name)] = tool

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool from the session."""
        with self._lock:
            if name in self.tools:
                del self.tools[name]
                return True
            return False

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name."""
        with self._lock:
            return self.tools.get(name)

    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        with self._lock:
            return list(self.tools.values())

    def register_resource(self, resource: Resource) -> None:
        """Register a resource with the session."""
        with self._lock:
            self.resources[str(resource.uri)] = resource

    def get_resource(self, uri: str) -> Resource | None:
        """Get a resource by URI."""
        with self._lock:
            # Direct match
            if uri in self.resources:
                return self.resources[uri]
            # Template match
            for resource in self.resources.values():
                if resource.matches_uri(uri):
                    return resource
            return None

    def list_resources(self) -> list[Resource]:
        """List all registered resources."""
        with self._lock:
            return list(self.resources.values())

    def register_prompt(self, prompt: Prompt) -> None:
        """Register a prompt with the session."""
        with self._lock:
            self.prompts[prompt.name] = prompt

    def get_prompt(self, name: str) -> Prompt | None:
        """Get a prompt by name."""
        with self._lock:
            return self.prompts.get(name)

    def list_prompts(self) -> list[Prompt]:
        """List all registered prompts."""
        with self._lock:
            return list(self.prompts.values())

    @property
    def is_ready(self) -> bool:
        """Check if session is ready for operations."""
        return self.state == SessionState.READY

    @property
    def is_closed(self) -> bool:
        """Check if session is closed."""
        return self.state == SessionState.CLOSED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "protocolVersion": str(self.protocol_version),
            "state": self.state.value,
            "clientInfo": self.client_info.to_dict() if self.client_info else None,
            "serverInfo": self.server_info.to_dict() if self.server_info else None,
            "capabilities": self.capabilities.to_dict(),
            "logLevel": self.log_level.value,
            "toolCount": len(self.tools),
            "resourceCount": len(self.resources),
            "promptCount": len(self.prompts),
            "createdAt": self.created_at.isoformat(),
            "initializedAt": self.initialized_at.isoformat() if self.initialized_at else None,
            "closedAt": self.closed_at.isoformat() if self.closed_at else None,
        }
