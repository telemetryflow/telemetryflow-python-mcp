"""Content-related value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Self


class Role(str, Enum):
    """Message role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Model(str, Enum):
    """Claude model variants."""

    # Claude 4 models
    CLAUDE_4_OPUS = "claude-opus-4-20250514"
    CLAUDE_4_SONNET = "claude-sonnet-4-20250514"

    # Claude 3.5 models
    CLAUDE_35_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_35_HAIKU = "claude-3-5-haiku-20241022"

    # Claude 3 models
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

    @classmethod
    def default(cls) -> Model:
        """Get the default model."""
        return cls.CLAUDE_4_SONNET

    @classmethod
    def from_string(cls, value: str) -> Model:
        """Create model from string value."""
        for model in cls:
            if model.value == value:
                return model
        raise ValueError(f"Unknown model: {value}")


class ContentType(str, Enum):
    """Content block types."""

    TEXT = "text"
    IMAGE = "image"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class MimeType(str, Enum):
    """Common MIME types."""

    # Text types
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_CSS = "text/css"
    TEXT_JAVASCRIPT = "text/javascript"
    TEXT_MARKDOWN = "text/markdown"
    TEXT_CSV = "text/csv"

    # Application types
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"
    APPLICATION_YAML = "application/yaml"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
    APPLICATION_PDF = "application/pdf"

    # Image types
    IMAGE_PNG = "image/png"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_GIF = "image/gif"
    IMAGE_WEBP = "image/webp"
    IMAGE_SVG = "image/svg+xml"

    @classmethod
    def from_extension(cls, ext: str) -> MimeType:
        """Get MIME type from file extension."""
        ext = ext.lower().lstrip(".")
        extension_map = {
            "txt": cls.TEXT_PLAIN,
            "html": cls.TEXT_HTML,
            "htm": cls.TEXT_HTML,
            "css": cls.TEXT_CSS,
            "js": cls.TEXT_JAVASCRIPT,
            "mjs": cls.TEXT_JAVASCRIPT,
            "md": cls.TEXT_MARKDOWN,
            "markdown": cls.TEXT_MARKDOWN,
            "csv": cls.TEXT_CSV,
            "json": cls.APPLICATION_JSON,
            "xml": cls.APPLICATION_XML,
            "yaml": cls.APPLICATION_YAML,
            "yml": cls.APPLICATION_YAML,
            "pdf": cls.APPLICATION_PDF,
            "png": cls.IMAGE_PNG,
            "jpg": cls.IMAGE_JPEG,
            "jpeg": cls.IMAGE_JPEG,
            "gif": cls.IMAGE_GIF,
            "webp": cls.IMAGE_WEBP,
            "svg": cls.IMAGE_SVG,
        }
        return extension_map.get(ext, cls.APPLICATION_OCTET_STREAM)

    @classmethod
    def from_string(cls, value: str) -> MimeType:
        """Create from string value."""
        for mime_type in cls:
            if mime_type.value == value:
                return mime_type
        return cls.APPLICATION_OCTET_STREAM


@dataclass(frozen=True, slots=True)
class SystemPrompt:
    """System prompt value object."""

    value: str

    MAX_LENGTH = 100000

    def __post_init__(self) -> None:
        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(f"SystemPrompt cannot exceed {self.MAX_LENGTH} characters")

    @classmethod
    def empty(cls) -> Self:
        """Create an empty system prompt."""
        return cls(value="")

    @property
    def is_empty(self) -> bool:
        """Check if the system prompt is empty."""
        return not self.value.strip()

    def __str__(self) -> str:
        return self.value

    def __bool__(self) -> bool:
        return not self.is_empty
