"""Unit tests for built-in tools."""

import os
import tempfile
from pathlib import Path

import pytest

from tfo_mcp.presentation.tools.builtin_tools import (
    _echo_handler,
    _list_directory_handler,
    _read_file_handler,
    _search_files_handler,
    _system_info_handler,
    _write_file_handler,
)


class TestEchoTool:
    """Test echo tool."""

    @pytest.mark.asyncio
    async def test_echo_message(self):
        """Test echoing a message."""
        result = await _echo_handler({"message": "Hello"})
        assert not result.is_error
        assert "Hello" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_echo_empty(self):
        """Test echoing empty message."""
        result = await _echo_handler({})
        assert not result.is_error


class TestReadFileTool:
    """Test read_file tool."""

    @pytest.mark.asyncio
    async def test_read_existing_file(self):
        """Test reading existing file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            f.flush()
            result = await _read_file_handler({"path": f.name})
            assert not result.is_error
            assert "test content" in result.content[0]["text"]
            os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_read_missing_file(self):
        """Test reading missing file."""
        result = await _read_file_handler({"path": "/nonexistent/file.txt"})
        assert result.is_error

    @pytest.mark.asyncio
    async def test_read_no_path(self):
        """Test reading without path."""
        result = await _read_file_handler({})
        assert result.is_error


class TestWriteFileTool:
    """Test write_file tool."""

    @pytest.mark.asyncio
    async def test_write_file(self):
        """Test writing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            result = await _write_file_handler(
                {
                    "path": str(path),
                    "content": "test content",
                }
            )
            assert not result.is_error
            assert path.read_text() == "test content"

    @pytest.mark.asyncio
    async def test_write_file_create_dirs(self):
        """Test writing file with create_dirs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "test.txt"
            result = await _write_file_handler(
                {
                    "path": str(path),
                    "content": "test",
                    "create_dirs": True,
                }
            )
            assert not result.is_error
            assert path.exists()


class TestListDirectoryTool:
    """Test list_directory tool."""

    @pytest.mark.asyncio
    async def test_list_directory(self):
        """Test listing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.txt").touch()
            (Path(tmpdir) / "file2.txt").touch()
            result = await _list_directory_handler({"path": tmpdir})
            assert not result.is_error

    @pytest.mark.asyncio
    async def test_list_missing_directory(self):
        """Test listing missing directory."""
        result = await _list_directory_handler({"path": "/nonexistent"})
        assert result.is_error


class TestSearchFilesTool:
    """Test search_files tool."""

    @pytest.mark.asyncio
    async def test_search_files(self):
        """Test searching files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test1.py").touch()
            (Path(tmpdir) / "test2.py").touch()
            (Path(tmpdir) / "readme.md").touch()
            result = await _search_files_handler(
                {
                    "path": tmpdir,
                    "pattern": "*.py",
                }
            )
            assert not result.is_error


class TestSystemInfoTool:
    """Test system_info tool."""

    @pytest.mark.asyncio
    async def test_system_info(self):
        """Test getting system info."""
        result = await _system_info_handler({})
        assert not result.is_error
        content = result.content[0]["text"]
        assert "platform" in content
