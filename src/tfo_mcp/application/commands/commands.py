"""CQRS Command definitions.

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

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tfo_mcp.domain.entities import Prompt, Resource, Tool
    from tfo_mcp.domain.valueobjects import MCPLogLevel, Model


@dataclass
class Command:
    """Base class for commands."""

    pass


@dataclass
class InitializeSessionCommand(Command):
    """Command to initialize a new session."""

    client_name: str
    client_version: str
    protocol_version: str
    client_capabilities: dict[str, Any] = field(default_factory=dict)


@dataclass
class CloseSessionCommand(Command):
    """Command to close a session."""

    session_id: str


@dataclass
class SetLogLevelCommand(Command):
    """Command to set the log level."""

    level: MCPLogLevel


@dataclass
class CreateConversationCommand(Command):
    """Command to create a new conversation."""

    model: Model
    system_prompt: str = ""
    max_tokens: int = 4096
    temperature: float = 1.0


@dataclass
class SendMessageCommand(Command):
    """Command to send a message in a conversation."""

    conversation_id: str
    message: str
    tools: list[Tool] = field(default_factory=list)


@dataclass
class RegisterToolCommand(Command):
    """Command to register a tool."""

    tool: Tool


@dataclass
class ExecuteToolCommand(Command):
    """Command to execute a tool."""

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class RegisterResourceCommand(Command):
    """Command to register a resource."""

    resource: Resource


@dataclass
class RegisterPromptCommand(Command):
    """Command to register a prompt."""

    prompt: Prompt
