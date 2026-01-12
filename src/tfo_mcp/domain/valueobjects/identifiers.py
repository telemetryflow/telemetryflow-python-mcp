"""Identifier value objects."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class SessionID:
    """Unique identifier for a session."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("SessionID cannot be empty")

    @classmethod
    def generate(cls) -> Self:
        """Generate a new unique session ID."""
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create from string value."""
        return cls(value=value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ConversationID:
    """Unique identifier for a conversation."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ConversationID cannot be empty")

    @classmethod
    def generate(cls) -> Self:
        """Generate a new unique conversation ID."""
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create from string value."""
        return cls(value=value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MessageID:
    """Unique identifier for a message."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("MessageID cannot be empty")

    @classmethod
    def generate(cls) -> Self:
        """Generate a new unique message ID."""
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Create from string value."""
        return cls(value=value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ToolName:
    """Tool name value object with validation."""

    value: str

    # Valid tool name pattern: lowercase letters, numbers, underscores
    PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
    MAX_LENGTH = 64

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ToolName cannot be empty")
        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(f"ToolName cannot exceed {self.MAX_LENGTH} characters")
        if not self.PATTERN.match(self.value):
            raise ValueError(f"ToolName must match pattern {self.PATTERN.pattern}: {self.value}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ToolDescription:
    """Tool description value object with validation."""

    value: str

    MAX_LENGTH = 1024

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ToolDescription cannot be empty")
        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(f"ToolDescription cannot exceed {self.MAX_LENGTH} characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ResourceURI:
    """Resource URI value object with validation."""

    value: str

    # Supported URI schemes
    VALID_SCHEMES = {"file", "config", "status", "http", "https"}

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ResourceURI cannot be empty")
        self._validate_scheme()

    def _validate_scheme(self) -> None:
        """Validate that the URI has a valid scheme."""
        if "://" not in self.value:
            raise ValueError(f"ResourceURI must contain a scheme: {self.value}")
        scheme = self.value.split("://")[0].lower()
        if scheme not in self.VALID_SCHEMES:
            raise ValueError(f"ResourceURI scheme '{scheme}' not in {self.VALID_SCHEMES}")

    @property
    def scheme(self) -> str:
        """Get the URI scheme."""
        return self.value.split("://")[0].lower()

    @property
    def path(self) -> str:
        """Get the URI path."""
        return self.value.split("://", 1)[1] if "://" in self.value else self.value

    @property
    def is_template(self) -> bool:
        """Check if this is a template URI (contains {})."""
        return "{" in self.value and "}" in self.value

    def __str__(self) -> str:
        return self.value
