"""MCP protocol value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Self


class MCPMethod(str, Enum):
    """MCP protocol methods."""

    # Lifecycle
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"
    PING = "ping"
    SHUTDOWN = "shutdown"

    # Tools
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

    # Resources
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"
    RESOURCES_TEMPLATES_LIST = "resources/templates/list"

    # Prompts
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"

    # Logging
    LOGGING_SET_LEVEL = "logging/setLevel"

    # Completion
    COMPLETION_COMPLETE = "completion/complete"

    # Sampling
    SAMPLING_CREATE_MESSAGE = "sampling/createMessage"

    # Notifications
    NOTIFICATION_CANCELLED = "notifications/cancelled"
    NOTIFICATION_PROGRESS = "notifications/progress"
    NOTIFICATION_MESSAGE = "notifications/message"
    NOTIFICATION_RESOURCES_UPDATED = "notifications/resources/updated"
    NOTIFICATION_RESOURCES_LIST_CHANGED = "notifications/resources/list_changed"
    NOTIFICATION_TOOLS_LIST_CHANGED = "notifications/tools/list_changed"
    NOTIFICATION_PROMPTS_LIST_CHANGED = "notifications/prompts/list_changed"


class MCPCapability(str, Enum):
    """MCP server capabilities."""

    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"
    LOGGING = "logging"
    SAMPLING = "sampling"
    EXPERIMENTAL = "experimental"


class MCPLogLevel(str, Enum):
    """MCP log levels (RFC 5424)."""

    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"

    @classmethod
    def from_string(cls, level: str) -> MCPLogLevel:
        """Convert string to log level."""
        level_lower = level.lower()
        for log_level in cls:
            if log_level.value == level_lower:
                return log_level
        return cls.INFO


class MCPErrorCode(IntEnum):
    """JSON-RPC and MCP error codes."""

    # JSON-RPC 2.0 standard errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # JSON-RPC reserved for implementation-defined server errors
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000

    # MCP specific errors
    TOOL_NOT_FOUND = -32001
    RESOURCE_NOT_FOUND = -32002
    PROMPT_NOT_FOUND = -32003
    TOOL_EXECUTION_ERROR = -32004
    RESOURCE_READ_ERROR = -32005
    PROMPT_ERROR = -32006
    RATE_LIMITED = -32007
    SESSION_NOT_INITIALIZED = -32008
    SESSION_ALREADY_INITIALIZED = -32009
    UNSUPPORTED_PROTOCOL_VERSION = -32010


@dataclass(frozen=True, slots=True)
class MCPProtocolVersion:
    """MCP protocol version value object."""

    value: str

    # Supported protocol versions
    SUPPORTED_VERSIONS = {"2024-11-05"}
    LATEST_VERSION = "2024-11-05"

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Protocol version cannot be empty")

    @classmethod
    def latest(cls) -> Self:
        """Get the latest protocol version."""
        return cls(value=cls.LATEST_VERSION)

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create from string value."""
        return cls(value=value)

    @property
    def is_supported(self) -> bool:
        """Check if this version is supported."""
        return self.value in self.SUPPORTED_VERSIONS

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class JSONRPCVersion:
    """JSON-RPC version value object."""

    value: str

    SUPPORTED_VERSION = "2.0"

    def __post_init__(self) -> None:
        if self.value != self.SUPPORTED_VERSION:
            raise ValueError(f"Only JSON-RPC {self.SUPPORTED_VERSION} is supported")

    @classmethod
    def default(cls) -> Self:
        """Get the default JSON-RPC version."""
        return cls(value=cls.SUPPORTED_VERSION)

    def __str__(self) -> str:
        return self.value
