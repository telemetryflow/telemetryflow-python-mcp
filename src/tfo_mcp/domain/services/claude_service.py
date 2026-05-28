"""Claude service interface.

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
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tfo_mcp.domain.entities import Message, Tool
    from tfo_mcp.domain.valueobjects import Model, SystemPrompt


class IClaudeService(ABC):
    """Interface for Claude API communication."""

    @abstractmethod
    async def create_message(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: list[Tool] | None = None,
    ) -> Message:
        """Create a message using Claude API."""
        ...

    @abstractmethod
    def create_message_stream(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        tools: list[Tool] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Create a streaming message using Claude API.

        Returns an async generator that yields streaming events.
        """
        ...

    @abstractmethod
    async def count_tokens(
        self,
        messages: list[Message],
        model: Model,
        system_prompt: SystemPrompt | None = None,
    ) -> int:
        """Count tokens for messages."""
        ...
