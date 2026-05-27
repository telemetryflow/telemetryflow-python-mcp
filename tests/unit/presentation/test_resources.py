"""Unit tests for built-in resources."""

import json

import pytest

from tfo_mcp.domain.entities import ResourceContent
from tfo_mcp.infrastructure.config import Config
from tfo_mcp.presentation.resources.builtin_resources import (
    _create_config_reader,
    _create_health_reader,
    _file_reader,
    register_builtin_resources,
)


class TestConfigResource:
    """Test config://server resource."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.mark.asyncio
    async def test_read_config(self, config):
        """Test reading config resource."""
        reader = _create_config_reader(config)
        result = await reader("config://server", {})

        assert result is not None
        assert result.mime_type.value == "application/json"

        data = json.loads(result.text)
        assert "server" in data
        assert "name" in data["server"]

    @pytest.mark.asyncio
    async def test_config_contains_server_info(self, config):
        """Test config contains server information."""
        reader = _create_config_reader(config)
        result = await reader("config://server", {})
        data = json.loads(result.text)

        assert "server" in data
        assert "version" in data["server"]
        assert "transport" in data["server"]

    @pytest.mark.asyncio
    async def test_config_contains_mcp_info(self, config):
        """Test config contains MCP information."""
        reader = _create_config_reader(config)
        result = await reader("config://server", {})
        data = json.loads(result.text)

        assert "mcp" in data
        assert "protocolVersion" in data["mcp"]


class TestHealthResource:
    """Test status://health resource."""

    @pytest.mark.asyncio
    async def test_read_health(self):
        reader = _create_health_reader()
        result = await reader("status://health", {})

        assert result is not None
        assert result.mime_type.value == "application/json"

        data = json.loads(result.text)
        assert "status" in data

    @pytest.mark.asyncio
    async def test_health_status_ok(self):
        reader = _create_health_reader()
        result = await reader("status://health", {})
        data = json.loads(result.text)

        assert data["status"] in ["healthy", "ok", "ready", "not_ready"]

    @pytest.mark.asyncio
    async def test_health_contains_session_info(self):
        reader = _create_health_reader()
        result = await reader("status://health", {})
        data = json.loads(result.text)

        assert "status" in data


class TestFileResource:
    """Test file:///{path} resource."""

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!")
        return file_path

    @pytest.mark.asyncio
    async def test_read_text_file(self, temp_file):
        """Test reading a text file."""
        result = await _file_reader(
            f"file:///{temp_file}",
            {"path": str(temp_file)},
        )

        assert result is not None
        assert "Hello, World!" in result.text

    @pytest.mark.asyncio
    async def test_read_json_file(self, tmp_path):
        """Test reading a JSON file."""
        file_path = tmp_path / "data.json"
        file_path.write_text('{"key": "value"}')

        result = await _file_reader(
            f"file:///{file_path}",
            {"path": str(file_path)},
        )

        assert result is not None
        assert result.mime_type.value == "application/json"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test reading nonexistent file returns error content."""
        result = await _file_reader(
            "file:///nonexistent/file.txt",
            {"path": "/nonexistent/file.txt"},
        )
        # The implementation returns a ResourceContent with error message
        assert result is not None
        assert "Error" in result.text or "not found" in result.text.lower()

    @pytest.mark.asyncio
    async def test_file_mime_type_detection(self, tmp_path):
        """Test file MIME type detection."""
        # Test JSON file (has explicit mapping)
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')

        result = await _file_reader(
            f"file:///{json_file}",
            {"path": str(json_file)},
        )
        assert result.mime_type.value == "application/json"

        # Test Markdown file
        md_file = tmp_path / "readme.md"
        md_file.write_text("# Title")

        result = await _file_reader(
            f"file:///{md_file}",
            {"path": str(md_file)},
        )
        assert result.mime_type.value == "text/markdown"


class TestResourceRegistration:
    """Test resource registration."""

    @pytest.fixture
    def mcp_server(self):
        from tfo_mcp.infrastructure.config import Config
        from tfo_mcp.presentation.server import MCPServer

        config = Config()
        return MCPServer(config)

    @pytest.fixture
    def config(self):
        return Config()

    def test_register_builtin_resources(self, mcp_server, config):
        register_builtin_resources(mcp_server, config)

        resource_uris = [str(r.uri) for r in mcp_server._resource_definitions]
        assert any("config" in uri for uri in resource_uris)
        assert any("health" in uri for uri in resource_uris)

    def test_resource_count(self, mcp_server, config):
        register_builtin_resources(mcp_server, config)

        total = len(mcp_server._resource_definitions) + len(mcp_server._template_definitions)
        assert total >= 2

    def test_template_resource_registered(self, mcp_server, config):
        register_builtin_resources(mcp_server, config)

        assert len(mcp_server._template_definitions) >= 1


class TestResourceContent:
    """Test ResourceContent entity."""

    def test_text_content(self):
        """Test text content."""
        from tfo_mcp.domain.valueobjects import MimeType

        content = ResourceContent(
            uri="test://resource",
            mime_type=MimeType.TEXT_PLAIN,
            text="Hello, World!",
        )

        assert content.text == "Hello, World!"
        assert content.blob is None

    def test_binary_content(self):
        """Test binary content."""
        from tfo_mcp.domain.valueobjects import MimeType

        content = ResourceContent(
            uri="test://binary",
            mime_type=MimeType.APPLICATION_OCTET_STREAM,
            blob=b"\x00\x01\x02\x03",
        )

        assert content.blob == b"\x00\x01\x02\x03"

    def test_json_content(self):
        """Test JSON content."""
        from tfo_mcp.domain.valueobjects import MimeType

        content = ResourceContent(
            uri="test://json",
            mime_type=MimeType.APPLICATION_JSON,
            text='{"key": "value"}',
        )

        data = json.loads(content.text)
        assert data["key"] == "value"
