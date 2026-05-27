from __future__ import annotations

import platform
from unittest.mock import AsyncMock, MagicMock, patch

from tfo_mcp.presentation.tools.builtin_tools import (
    BUILTIN_TOOLS,
    _create_claude_conversation_handler,
    _echo_handler,
    _execute_command_handler,
    _list_directory_handler,
    _read_file_handler,
    _search_files_handler,
    _system_info_handler,
    _write_file_handler,
    register_builtin_tools,
)


class TestEchoHandler:
    async def test_echo_message(self):
        result = await _echo_handler({"message": "hello"})
        assert not result.is_error
        assert "hello" in result.content[0]["text"]

    async def test_echo_empty(self):
        result = await _echo_handler({"message": ""})
        assert "Echo: " in result.content[0]["text"]

    async def test_echo_missing_message(self):
        result = await _echo_handler({})
        assert "Echo: " in result.content[0]["text"]


class TestReadFileHandler:
    async def test_read_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = await _read_file_handler({"path": str(f)})
        assert not result.is_error
        assert "hello world" in result.content[0]["text"]

    async def test_read_file_missing_path(self):
        result = await _read_file_handler({})
        assert result.is_error
        assert "Path is required" in result.content[0]["text"]

    async def test_read_file_not_found(self):
        result = await _read_file_handler({"path": "/nonexistent/file.txt"})
        assert result.is_error
        assert "File not found" in result.content[0]["text"]

    async def test_read_directory_not_file(self, tmp_path):
        d = tmp_path / "subdir"
        d.mkdir()
        result = await _read_file_handler({"path": str(d)})
        assert result.is_error
        assert "Not a file" in result.content[0]["text"]

    async def test_read_file_with_encoding(self, tmp_path):
        f = tmp_path / "encoded.txt"
        f.write_text("content", encoding="utf-8")
        result = await _read_file_handler({"path": str(f), "encoding": "utf-8"})
        assert not result.is_error

    async def test_read_file_unicode_error(self, tmp_path):
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\xff\xfe\x80\x81")
        result = await _read_file_handler({"path": str(f), "encoding": "ascii"})
        assert result.is_error
        assert "Cannot decode" in result.content[0]["text"]

    async def test_read_file_permission_error(self):
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("aiofiles.open", side_effect=PermissionError("denied")),
        ):
            result = await _read_file_handler({"path": "/root/secret"})
            assert result.is_error
            assert "Permission denied" in result.content[0]["text"]

    async def test_read_file_generic_error(self):
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("aiofiles.open", side_effect=OSError("io error")),
        ):
            result = await _read_file_handler({"path": "/some/path"})
            assert result.is_error


class TestWriteFileHandler:
    async def test_write_file(self, tmp_path):
        f = tmp_path / "output.txt"
        result = await _write_file_handler({"path": str(f), "content": "test content"})
        assert not result.is_error
        assert f.read_text() == "test content"

    async def test_write_file_missing_path(self):
        result = await _write_file_handler({})
        assert result.is_error
        assert "Path is required" in result.content[0]["text"]

    async def test_write_file_create_dirs(self, tmp_path):
        f = tmp_path / "sub" / "dir" / "file.txt"
        result = await _write_file_handler(
            {"path": str(f), "content": "nested", "create_dirs": True}
        )
        assert not result.is_error
        assert f.read_text() == "nested"

    async def test_write_file_no_parent_dir(self, tmp_path):
        f = tmp_path / "nonexistent" / "file.txt"
        result = await _write_file_handler({"path": str(f), "content": "test"})
        assert result.is_error
        assert "Directory does not exist" in result.content[0]["text"]

    async def test_write_file_permission_error(self):
        with patch("pathlib.Path.expanduser", side_effect=PermissionError("denied")):
            result = await _write_file_handler({"path": "/root/file", "content": "x"})
            assert result.is_error

    async def test_write_file_empty_content(self, tmp_path):
        f = tmp_path / "empty.txt"
        result = await _write_file_handler({"path": str(f), "content": ""})
        assert not result.is_error
        assert f.read_text() == ""


class TestListDirectoryHandler:
    async def test_list_directory(self, tmp_path):
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "file2.txt").write_text("b")
        result = await _list_directory_handler({"path": str(tmp_path)})
        assert not result.is_error
        assert "file1.txt" in result.content[0]["text"]

    async def test_list_directory_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.txt").write_text("x")
        result = await _list_directory_handler({"path": str(tmp_path), "recursive": True})
        assert not result.is_error
        assert "nested.txt" in result.content[0]["text"]

    async def test_list_directory_not_found(self):
        result = await _list_directory_handler({"path": "/nonexistent"})
        assert result.is_error

    async def test_list_directory_not_a_dir(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        result = await _list_directory_handler({"path": str(f)})
        assert result.is_error
        assert "Not a directory" in result.content[0]["text"]

    async def test_list_directory_permission_error(self):
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.iterdir", side_effect=PermissionError("denied")),
        ):
            result = await _list_directory_handler({"path": "/root"})
            assert result.is_error

    async def test_list_directory_default_path(self, tmp_path):
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            (tmp_path / "a.txt").write_text("a")
            result = await _list_directory_handler({})
            assert not result.is_error


class TestSearchFilesHandler:
    async def test_search_files(self, tmp_path):
        (tmp_path / "test.py").write_text("code")
        (tmp_path / "test.txt").write_text("text")
        result = await _search_files_handler({"path": str(tmp_path), "pattern": "*.py"})
        assert not result.is_error
        assert "test.py" in result.content[0]["text"]

    async def test_search_directory_not_found(self):
        result = await _search_files_handler({"path": "/nonexistent"})
        assert result.is_error

    async def test_search_error(self):
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.rglob", side_effect=OSError("err")),
        ):
            result = await _search_files_handler({"path": "/some"})
            assert result.is_error


class TestExecuteCommandHandler:
    async def test_execute_command(self):
        result = await _execute_command_handler({"command": "echo hello"})
        assert not result.is_error
        assert "hello" in result.content[0]["text"]

    async def test_execute_command_missing(self):
        result = await _execute_command_handler({})
        assert result.is_error
        assert "Command is required" in result.content[0]["text"]

    async def test_execute_command_nonzero_exit(self):
        result = await _execute_command_handler({"command": "exit 1"})
        assert result.is_error

    async def test_execute_command_timeout(self):
        result = await _execute_command_handler({"command": "sleep 10", "timeout": 0.1})
        assert result.is_error
        assert "timed out" in result.content[0]["text"].lower()

    async def test_execute_command_with_working_dir(self, tmp_path):
        result = await _execute_command_handler({"command": "pwd", "working_dir": str(tmp_path)})
        assert not result.is_error

    async def test_execute_command_error(self):
        with patch("asyncio.create_subprocess_shell", side_effect=OSError("err")):
            result = await _execute_command_handler({"command": "test"})
            assert result.is_error


class TestSystemInfoHandler:
    async def test_system_info(self):
        result = await _system_info_handler({})
        assert not result.is_error
        assert platform.system() in result.content[0]["text"]

    async def test_system_info_error(self):
        with patch("platform.system", side_effect=Exception("err")):
            result = await _system_info_handler({})
            assert result.is_error


class TestCreateClaudeConversationHandler:
    async def test_missing_message(self):
        handler = _create_claude_conversation_handler(MagicMock())
        result = await handler({})
        assert result.is_error
        assert "Message is required" in result.content[0]["text"]

    async def test_successful_conversation(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Claude response"
        mock_client.create_message = AsyncMock(return_value=mock_response)

        handler = _create_claude_conversation_handler(mock_client)
        result = await handler({"message": "Hello", "model": "claude-sonnet-4-20250514"})
        assert not result.is_error
        assert "Claude response" in result.content[0]["text"]

    async def test_invalid_model(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_client.create_message = AsyncMock(return_value=mock_response)

        handler = _create_claude_conversation_handler(mock_client)
        result = await handler({"message": "Hello", "model": "invalid-model-name"})
        assert not result.is_error

    async def test_claude_api_error(self):
        mock_client = MagicMock()
        mock_client.create_message = AsyncMock(side_effect=Exception("API error"))

        handler = _create_claude_conversation_handler(mock_client)
        result = await handler({"message": "Hello"})
        assert result.is_error
        assert "Error calling Claude API" in result.content[0]["text"]

    async def test_with_system_prompt(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_client.create_message = AsyncMock(return_value=mock_response)

        handler = _create_claude_conversation_handler(mock_client)
        result = await handler({"message": "Hello", "system_prompt": "Be helpful"})
        assert not result.is_error


class TestRegisterBuiltinTools:
    def test_registers_all_tools(self):
        mock_server = MagicMock()
        register_builtin_tools(mock_server)
        assert mock_server.register_tool.call_count == len(BUILTIN_TOOLS)

    def test_registers_claude_conversation(self):
        mock_server = MagicMock()
        mock_client = MagicMock()
        register_builtin_tools(mock_server, mock_client)
        assert mock_server.register_tool.call_count == len(BUILTIN_TOOLS) + 1
        last_call = mock_server.register_tool.call_args
        assert (
            last_call.kwargs.get("name") == "claude_conversation"
            or last_call[1].get("name") == "claude_conversation"
        )

    def test_without_claude_client(self):
        mock_server = MagicMock()
        register_builtin_tools(mock_server, None)
        assert mock_server.register_tool.call_count == len(BUILTIN_TOOLS)


class TestBuiltinToolsDefinitions:
    def test_all_have_required_fields(self):
        for tool_def in BUILTIN_TOOLS:
            assert "name" in tool_def
            assert "description" in tool_def
            assert "input_schema" in tool_def
            assert "handler" in tool_def
            assert "category" in tool_def

    def test_expected_tool_names(self):
        names = [t["name"] for t in BUILTIN_TOOLS]
        assert "echo" in names
        assert "read_file" in names
        assert "write_file" in names
        assert "list_directory" in names
        assert "search_files" in names
        assert "execute_command" in names
        assert "system_info" in names
