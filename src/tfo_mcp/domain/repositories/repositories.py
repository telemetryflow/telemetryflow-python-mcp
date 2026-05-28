"""Repository interfaces for domain aggregates and entities.

TelemetryFlow Python MCP Server - Community Enterprise Observability Platform
Copyright (c) 2024-2026 Telemetri Data Indonesia. All rights reserved.
Open Source Software built by Telemetri Data Indonesia.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tfo_mcp.domain.aggregates import Conversation, Session
    from tfo_mcp.domain.entities import Prompt, Resource, Tool
    from tfo_mcp.domain.valueobjects import ConversationID, SessionID


class ISessionRepository(ABC):
    """Repository interface for Session aggregate."""

    @abstractmethod
    async def save(self, session: Session) -> None:
        """Save a session."""
        ...

    @abstractmethod
    async def get(self, session_id: SessionID) -> Session | None:
        """Get a session by ID."""
        ...

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Session | None:
        """Get a session by string ID."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Session]:
        """List all sessions."""
        ...

    @abstractmethod
    async def delete(self, session_id: SessionID) -> bool:
        """Delete a session."""
        ...


class IConversationRepository(ABC):
    """Repository interface for Conversation aggregate."""

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        """Save a conversation."""
        ...

    @abstractmethod
    async def get(self, conversation_id: ConversationID) -> Conversation | None:
        """Get a conversation by ID."""
        ...

    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by string ID."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Conversation]:
        """List all conversations."""
        ...

    @abstractmethod
    async def list_by_session(self, session_id: str) -> list[Conversation]:
        """List conversations by session ID."""
        ...

    @abstractmethod
    async def delete(self, conversation_id: ConversationID) -> bool:
        """Delete a conversation."""
        ...


class IToolRepository(ABC):
    """Repository interface for Tool entity."""

    @abstractmethod
    async def save(self, tool: Tool) -> None:
        """Save a tool."""
        ...

    @abstractmethod
    async def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Tool]:
        """List all tools."""
        ...

    @abstractmethod
    async def list_enabled(self) -> list[Tool]:
        """List only enabled tools."""
        ...

    @abstractmethod
    async def list_by_category(self, category: str) -> list[Tool]:
        """List tools by category."""
        ...

    @abstractmethod
    async def delete(self, name: str) -> bool:
        """Delete a tool."""
        ...


class IResourceRepository(ABC):
    """Repository interface for Resource entity."""

    @abstractmethod
    async def save(self, resource: Resource) -> None:
        """Save a resource."""
        ...

    @abstractmethod
    async def get(self, uri: str) -> Resource | None:
        """Get a resource by URI."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Resource]:
        """List all resources."""
        ...

    @abstractmethod
    async def list_templates(self) -> list[Resource]:
        """List template resources."""
        ...

    @abstractmethod
    async def delete(self, uri: str) -> bool:
        """Delete a resource."""
        ...


class IPromptRepository(ABC):
    """Repository interface for Prompt entity."""

    @abstractmethod
    async def save(self, prompt: Prompt) -> None:
        """Save a prompt."""
        ...

    @abstractmethod
    async def get(self, name: str) -> Prompt | None:
        """Get a prompt by name."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Prompt]:
        """List all prompts."""
        ...

    @abstractmethod
    async def delete(self, name: str) -> bool:
        """Delete a prompt."""
        ...
