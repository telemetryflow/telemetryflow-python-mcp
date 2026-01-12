"""Resource entity."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from tfo_mcp.domain.valueobjects import MimeType, ResourceURI


@dataclass
class ResourceContent:
    """Content returned from reading a resource."""

    uri: str
    mime_type: MimeType
    text: str | None = None
    blob: bytes | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP resources/read format."""
        result: dict[str, Any] = {
            "uri": self.uri,
            "mimeType": self.mime_type.value,
        }
        if self.text is not None:
            result["text"] = self.text
        if self.blob is not None:
            import base64

            result["blob"] = base64.b64encode(self.blob).decode("utf-8")
        return result


# Type alias for resource reader function
ResourceReader = Callable[[str, dict[str, str]], Awaitable[ResourceContent]]


@dataclass
class Resource:
    """Resource entity representing an MCP resource."""

    uri: ResourceURI
    name: str
    description: str = ""
    mime_type: MimeType = MimeType.TEXT_PLAIN
    reader: ResourceReader | None = None
    is_template: bool = False
    uri_template: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        uri: str,
        name: str,
        description: str = "",
        mime_type: MimeType | str = MimeType.TEXT_PLAIN,
        reader: ResourceReader | None = None,
    ) -> Resource:
        """Create a new resource."""
        if isinstance(mime_type, str):
            mime_type = MimeType.from_string(mime_type)
        resource_uri = ResourceURI(value=uri)
        return cls(
            uri=resource_uri,
            name=name,
            description=description,
            mime_type=mime_type,
            reader=reader,
            is_template=resource_uri.is_template,
            uri_template=uri if resource_uri.is_template else None,
        )

    @classmethod
    def template(
        cls,
        uri_template: str,
        name: str,
        description: str = "",
        mime_type: MimeType | str = MimeType.TEXT_PLAIN,
        reader: ResourceReader | None = None,
    ) -> Resource:
        """Create a template resource."""
        if isinstance(mime_type, str):
            mime_type = MimeType.from_string(mime_type)
        return cls(
            uri=ResourceURI(value=uri_template),
            name=name,
            description=description,
            mime_type=mime_type,
            reader=reader,
            is_template=True,
            uri_template=uri_template,
        )

    async def read(self, params: dict[str, str] | None = None) -> ResourceContent:
        """Read the resource content."""
        if self.reader is None:
            return ResourceContent(
                uri=str(self.uri),
                mime_type=self.mime_type,
                text=f"No reader configured for resource: {self.uri}",
            )
        return await self.reader(str(self.uri), params or {})

    def matches_uri(self, uri: str) -> bool:
        """Check if the given URI matches this resource."""
        if not self.is_template:
            return str(self.uri) == uri
        # Simple template matching - check prefix
        template_prefix = str(self.uri).split("{")[0]
        return uri.startswith(template_prefix)

    def to_mcp_format(self) -> dict[str, Any]:
        """Convert to MCP resources/list format."""
        result: dict[str, Any] = {
            "uri": str(self.uri),
            "name": self.name,
            "mimeType": self.mime_type.value,
        }
        if self.description:
            result["description"] = self.description
        return result

    def to_template_format(self) -> dict[str, Any] | None:
        """Convert to MCP resources/templates/list format."""
        if not self.is_template or not self.uri_template:
            return None
        result: dict[str, Any] = {
            "uriTemplate": self.uri_template,
            "name": self.name,
            "mimeType": self.mime_type.value,
        }
        if self.description:
            result["description"] = self.description
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "uri": str(self.uri),
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type.value,
            "isTemplate": self.is_template,
            "uriTemplate": self.uri_template,
        }
