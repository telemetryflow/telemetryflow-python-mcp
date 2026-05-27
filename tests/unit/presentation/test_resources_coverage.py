from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from tfo_mcp.domain.valueobjects import MimeType
from tfo_mcp.infrastructure.config import Config
from tfo_mcp.presentation.resources.builtin_resources import (
    _create_config_reader,
    _create_health_reader,
    _file_reader,
    register_builtin_resources,
)


@pytest.fixture
def config():
    return Config()


class TestConfigReader:
    async def test_reads_config(self, config):
        reader = _create_config_reader(config)
        result = await reader("config://server", {})

        assert result.uri == "config://server"
        assert result.mime_type == MimeType.APPLICATION_JSON
        data = json.loads(result.text)
        assert "server" in data
        assert "mcp" in data
        assert data["server"]["name"] == config.server.name

    async def test_config_reader_ignores_params(self, config):
        reader = _create_config_reader(config)
        result = await reader("config://server", {"extra": "ignored"})
        assert result is not None


class TestHealthReader:
    async def test_reads_health(self):
        reader = _create_health_reader()
        result = await reader("status://health", {})

        assert result.uri == "status://health"
        assert result.mime_type == MimeType.APPLICATION_JSON
        data = json.loads(result.text)
        assert data["status"] == "healthy"

    async def test_health_reader_ignores_params(self):
        reader = _create_health_reader()
        result = await reader("status://health", {"x": "y"})
        assert result is not None


class TestFileReader:
    async def test_reads_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")

        result = await _file_reader(f"file:///{f}", {})
        assert result.text == "hello world"
        assert result.mime_type == MimeType.TEXT_PLAIN

    async def test_reads_file_with_path_prefix(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("content")

        result = await _file_reader(f"file:///{f}", {})
        assert "content" in result.text

    async def test_empty_path(self):
        result = await _file_reader("file:///", {})
        assert result.mime_type == MimeType.TEXT_PLAIN
        assert "Error" in result.text or "No file path" in result.text

    async def test_file_not_found(self):
        result = await _file_reader("file:///nonexistent/path.txt", {})
        assert "not found" in result.text.lower() or "Error" in result.text

    async def test_binary_file_fallback(self, tmp_path):
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x01\x02\xff\xfe")

        result = await _file_reader(f"file:///{f}", {})
        assert result.uri == f"file:///{f}"

    async def test_json_file_mime_type(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}')

        result = await _file_reader(f"file:///{f}", {})
        assert result.mime_type == MimeType.APPLICATION_JSON

    async def test_file_with_params(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("param content")

        result = await _file_reader(f"file:///{f}", {"path": str(f)})
        assert "param content" in result.text

    async def test_file_reader_error(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("data")

        with patch("aiofiles.open", side_effect=OSError("io error")):
            result = await _file_reader(f"file:///{f}", {})
            assert "Error" in result.text


class TestRegisterBuiltinResources:
    def test_registers_all_resources(self):
        mock_server = MagicMock()
        config = Config()
        register_builtin_resources(mock_server, config)

        assert mock_server.register_resource.call_count == 3

    def test_registers_config_resource(self):
        mock_server = MagicMock()
        config = Config()
        register_builtin_resources(mock_server, config)

        calls = mock_server.register_resource.call_args_list
        uris = [c.kwargs.get("uri") or c[1].get("uri") for c in calls]
        assert "config://server" in uris

    def test_registers_health_resource(self):
        mock_server = MagicMock()
        config = Config()
        register_builtin_resources(mock_server, config)

        calls = mock_server.register_resource.call_args_list
        uris = [c.kwargs.get("uri") or c[1].get("uri") for c in calls]
        assert "status://health" in uris

    def test_registers_file_resource(self):
        mock_server = MagicMock()
        config = Config()
        register_builtin_resources(mock_server, config)

        calls = mock_server.register_resource.call_args_list
        uris = [c.kwargs.get("uri") or c[1].get("uri") for c in calls]
        assert "file:///{path}" in uris
