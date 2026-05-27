"""End-to-end tests for MCP protocol flow.

These tests verify the complete MCP protocol flow by testing:
- MCPServer registration of builtin tools/resources/prompts
- Direct handler invocation for tools, resources, and prompts
- Tool execution, resource reading, prompt generation
- Error handling
- _setup_handlers() decorator creation
- Concurrent tool calls via handlers
"""

from __future__ import annotations

import asyncio
import json

import mcp.types as types
import pytest

from tfo_mcp.domain.entities import ResourceContent, ToolResult
from tfo_mcp.infrastructure.config import Config
from tfo_mcp.presentation.prompts.builtin_prompts import register_builtin_prompts
from tfo_mcp.presentation.resources.builtin_resources import register_builtin_resources
from tfo_mcp.presentation.server import MCPServer
from tfo_mcp.presentation.tools.builtin_tools import register_builtin_tools


def _create_full_server() -> MCPServer:
    config = Config()
    server = MCPServer(config)
    register_builtin_tools(server, None)
    register_builtin_resources(server, config)
    register_builtin_prompts(server)
    return server


def _create_full_server_with_handlers() -> MCPServer:
    server = _create_full_server()
    server._setup_handlers()
    return server


class TestServerCreation:
    """Test MCPServer creation and component registration."""

    def test_server_created_successfully(self):
        server = _create_full_server()
        assert server is not None
        assert server.server is not None

    def test_server_wraps_mcp_sdk_server(self):
        server = _create_full_server()
        from mcp.server import Server

        assert isinstance(server.server, Server)

    def test_all_builtins_registered(self):
        server = _create_full_server()
        assert len(server._tool_definitions) >= 7
        assert len(server._resource_definitions) >= 2
        assert len(server._template_definitions) >= 1
        assert len(server._prompt_definitions) >= 3

    def test_setup_handlers_registers_all_request_types(self):
        server = _create_full_server()
        server._setup_handlers()
        handler_keys = set(server.server.request_handlers.keys())
        assert types.ListToolsRequest in handler_keys
        assert types.CallToolRequest in handler_keys
        assert types.ListResourcesRequest in handler_keys
        assert types.ListResourceTemplatesRequest in handler_keys
        assert types.ReadResourceRequest in handler_keys
        assert types.ListPromptsRequest in handler_keys
        assert types.GetPromptRequest in handler_keys


class TestToolExecution:
    """Test tool handler invocation directly."""

    @pytest.fixture
    def server(self):
        return _create_full_server()

    @pytest.mark.asyncio
    async def test_echo_tool(self, server):
        handler = server._tool_handlers["echo"]
        result = await handler({"message": "Hello, World!"})
        assert isinstance(result, ToolResult)
        assert not result.is_error
        assert "Hello, World!" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_echo_tool_empty_message(self, server):
        handler = server._tool_handlers["echo"]
        result = await handler({"message": ""})
        assert isinstance(result, ToolResult)
        assert not result.is_error

    @pytest.mark.asyncio
    async def test_system_info_tool(self, server):
        handler = server._tool_handlers["system_info"]
        result = await handler({})
        assert isinstance(result, ToolResult)
        assert not result.is_error
        info = json.loads(result.content[0]["text"])
        assert "platform" in info
        assert "python_version" in info

    @pytest.mark.asyncio
    async def test_read_file_tool_not_found(self, server):
        handler = server._tool_handlers["read_file"]
        result = await handler({"path": "/nonexistent/path/file.txt"})
        assert isinstance(result, ToolResult)
        assert result.is_error

    @pytest.mark.asyncio
    async def test_read_file_tool_missing_path(self, server):
        handler = server._tool_handlers["read_file"]
        result = await handler({})
        assert isinstance(result, ToolResult)
        assert result.is_error

    @pytest.mark.asyncio
    async def test_list_directory_tool_current(self, server):
        handler = server._tool_handlers["list_directory"]
        result = await handler({"path": "."})
        assert isinstance(result, ToolResult)
        assert not result.is_error

    @pytest.mark.asyncio
    async def test_search_files_tool(self, server):
        handler = server._tool_handlers["search_files"]
        result = await handler({"path": ".", "pattern": "*.py"})
        assert isinstance(result, ToolResult)
        assert not result.is_error

    @pytest.mark.asyncio
    async def test_execute_command_tool(self, server):
        handler = server._tool_handlers["execute_command"]
        result = await handler({"command": "echo test123"})
        assert isinstance(result, ToolResult)
        assert not result.is_error
        info = json.loads(result.content[0]["text"])
        assert info["exit_code"] == 0
        assert "test123" in info["stdout"]

    @pytest.mark.asyncio
    async def test_execute_command_tool_timeout(self, server):
        handler = server._tool_handlers["execute_command"]
        result = await handler({"command": "sleep 60", "timeout": 1})
        assert isinstance(result, ToolResult)
        assert result.is_error
        assert "timed out" in result.content[0]["text"].lower()

    @pytest.mark.asyncio
    async def test_write_then_read_file(self, server, tmp_path):
        test_file = tmp_path / "test_write.txt"
        write_handler = server._tool_handlers["write_file"]
        read_handler = server._tool_handlers["read_file"]

        write_result = await write_handler({"path": str(test_file), "content": "test content"})
        assert isinstance(write_result, ToolResult)
        assert not write_result.is_error

        read_result = await read_handler({"path": str(test_file)})
        assert isinstance(read_result, ToolResult)
        assert not read_result.is_error
        assert "test content" in read_result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_write_file_creates_directories(self, server, tmp_path):
        test_file = tmp_path / "subdir" / "nested" / "file.txt"
        handler = server._tool_handlers["write_file"]
        result = await handler({"path": str(test_file), "content": "nested", "create_dirs": True})
        assert isinstance(result, ToolResult)
        assert not result.is_error

    @pytest.mark.asyncio
    async def test_tool_handler_returns_tool_result(self, server):
        handler = server._tool_handlers["echo"]
        result = await handler({"message": "test"})
        assert hasattr(result, "content")
        assert hasattr(result, "is_error")


class TestResourceReading:
    """Test resource reader invocation directly."""

    @pytest.fixture
    def server(self):
        return _create_full_server()

    @pytest.mark.asyncio
    async def test_config_resource(self, server):
        reader = server._resource_readers["config://server"]
        result = await reader("config://server", {})
        assert isinstance(result, ResourceContent)
        assert result.text is not None
        config_data = json.loads(result.text)
        assert "server" in config_data
        assert "mcp" in config_data

    @pytest.mark.asyncio
    async def test_health_resource(self, server):
        reader = server._resource_readers["status://health"]
        result = await reader("status://health", {})
        assert isinstance(result, ResourceContent)
        assert result.text is not None
        health_data = json.loads(result.text)
        assert health_data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_file_template_resource(self, server):
        reader = server._resource_readers["file:///{path}"]
        result = await reader("file:///tmp", {})
        assert isinstance(result, ResourceContent)

    @pytest.mark.asyncio
    async def test_resource_reader_not_found(self, server):
        reader = server._resource_readers.get("nonexistent://resource")
        assert reader is None

    @pytest.mark.asyncio
    async def test_all_resource_readers_are_callable(self, server):
        for _uri, reader in server._resource_readers.items():
            assert callable(reader)

    @pytest.mark.asyncio
    async def test_config_resource_returns_json(self, server):
        reader = server._resource_readers["config://server"]
        result = await reader("config://server", {})
        json.loads(result.text)


class TestPromptGeneration:
    """Test prompt generator invocation directly."""

    @pytest.fixture
    def server(self):
        return _create_full_server()

    @pytest.mark.asyncio
    async def test_code_review_prompt(self, server):
        generator = server._prompt_generators["code_review"]
        messages = await generator({"code": "print('hello')", "language": "python"})
        assert isinstance(messages, list)
        assert len(messages) > 0
        assert messages[0].content is not None
        assert "print('hello')" in messages[0].content
        assert "review" in messages[0].content.lower()

    @pytest.mark.asyncio
    async def test_explain_code_prompt(self, server):
        generator = server._prompt_generators["explain_code"]
        messages = await generator({"code": "def foo(): pass", "language": "python"})
        assert isinstance(messages, list)
        assert len(messages) > 0
        assert "def foo(): pass" in messages[0].content
        assert "explain" in messages[0].content.lower()

    @pytest.mark.asyncio
    async def test_debug_help_prompt(self, server):
        generator = server._prompt_generators["debug_help"]
        messages = await generator(
            {"code": "x = 1/0", "error": "ZeroDivisionError", "language": "python"}
        )
        assert isinstance(messages, list)
        assert len(messages) > 0
        assert "x = 1/0" in messages[0].content
        assert "ZeroDivisionError" in messages[0].content

    @pytest.mark.asyncio
    async def test_explain_code_prompt_detail_levels(self, server):
        generator = server._prompt_generators["explain_code"]
        for level in ("brief", "medium", "detailed"):
            messages = await generator({"code": "x=1", "language": "python", "detail_level": level})
            assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_prompt_with_empty_args(self, server):
        generator = server._prompt_generators["code_review"]
        messages = await generator({})
        assert isinstance(messages, list)
        assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_prompt_not_found(self, server):
        generator = server._prompt_generators.get("nonexistent_prompt")
        assert generator is None


class TestHandlerSetup:
    """Test _setup_handlers() creates proper decorators on the MCP server."""

    @pytest.fixture
    def server(self):
        return _create_full_server_with_handlers()

    def test_tools_list_handler_registered(self, server):
        assert types.ListToolsRequest in server.server.request_handlers

    def test_tools_call_handler_registered(self, server):
        assert types.CallToolRequest in server.server.request_handlers

    def test_resources_list_handler_registered(self, server):
        assert types.ListResourcesRequest in server.server.request_handlers

    def test_resource_templates_handler_registered(self, server):
        assert types.ListResourceTemplatesRequest in server.server.request_handlers

    def test_resources_read_handler_registered(self, server):
        assert types.ReadResourceRequest in server.server.request_handlers

    def test_prompts_list_handler_registered(self, server):
        assert types.ListPromptsRequest in server.server.request_handlers

    def test_prompts_get_handler_registered(self, server):
        assert types.GetPromptRequest in server.server.request_handlers

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self, server):
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.ListToolsRequest]
        req = types.ListToolsRequest(method="tools/list")
        result = await handler(req)
        tools = result.root.tools
        assert len(tools) == len(server._tool_definitions)
        for tool in tools:
            assert isinstance(tool, types.Tool)

    @pytest.mark.asyncio
    async def test_list_resources_returns_all(self, server):
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.ListResourcesRequest]
        req = types.ListResourcesRequest(method="resources/list")
        result = await handler(req)
        resources = result.root.resources
        assert len(resources) == len(server._resource_definitions)

    @pytest.mark.asyncio
    async def test_list_templates_returns_all(self, server):
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.ListResourceTemplatesRequest]
        req = types.ListResourceTemplatesRequest(method="resources/templates/list")
        result = await handler(req)
        templates = result.root.resourceTemplates
        assert len(templates) == len(server._template_definitions)

    @pytest.mark.asyncio
    async def test_list_prompts_returns_all(self, server):
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.ListPromptsRequest]
        req = types.ListPromptsRequest(method="prompts/list")
        result = await handler(req)
        prompts = result.root.prompts
        assert len(prompts) == len(server._prompt_definitions)

    @pytest.mark.asyncio
    async def test_call_tool_via_handler(self, server):
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.CallToolRequest]
        req = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="echo", arguments={"message": "handler test"}),
        )
        result = await handler(req)
        content = result.root.content
        assert isinstance(content, list)
        assert any("handler test" in c.text for c in content if isinstance(c, types.TextContent))

    @pytest.mark.asyncio
    async def test_read_resource_via_handler(self, server):
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.ReadResourceRequest]
        req = types.ReadResourceRequest(
            method="resources/read",
            params=types.ReadResourceRequestParams(uri="config://server"),
        )
        result = await handler(req)
        contents = result.root.contents
        assert len(contents) > 0
        text = contents[0].text
        config_data = json.loads(text)
        assert "server" in config_data

    @pytest.mark.asyncio
    async def test_get_prompt_via_handler(self, server):
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.GetPromptRequest]
        req = types.GetPromptRequest(
            method="prompts/get",
            params=types.GetPromptRequestParams(name="code_review", arguments={"code": "x=1"}),
        )
        result = await handler(req)
        prompt_result = result.root
        assert isinstance(prompt_result, types.GetPromptResult)
        assert len(prompt_result.messages) > 0


class TestErrorHandling:
    """Test error handling via handler invocation."""

    @pytest.fixture
    def server(self):
        return _create_full_server()

    def test_tool_not_found_in_registry(self, server):
        handler = server._tool_handlers.get("nonexistent_tool")
        assert handler is None

    @pytest.mark.asyncio
    async def test_tool_not_found_via_call_tool_handler(self):
        server = _create_full_server_with_handlers()
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.CallToolRequest]
        req = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="nonexistent_tool", arguments={}),
        )
        result = await handler(req)
        content = result.root.content
        assert isinstance(content, list)
        assert len(content) > 0
        assert "not found" in content[0].text.lower()

    @pytest.mark.asyncio
    async def test_prompt_not_found_via_handler(self):
        server = _create_full_server_with_handlers()
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.GetPromptRequest]
        req = types.GetPromptRequest(
            method="prompts/get",
            params=types.GetPromptRequestParams(name="nonexistent_prompt", arguments={}),
        )
        with pytest.raises(ValueError):
            await handler(req)

    @pytest.mark.asyncio
    async def test_resource_not_found_via_handler(self):
        server = _create_full_server_with_handlers()
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.ReadResourceRequest]
        req = types.ReadResourceRequest(
            method="resources/read",
            params=types.ReadResourceRequestParams(uri="nonexistent://nothing"),
        )
        result = await handler(req)
        contents = result.root.contents
        assert len(contents) > 0
        assert "not found" in contents[0].text.lower()

    @pytest.mark.asyncio
    async def test_tool_handler_exception_caught(self):
        server = _create_full_server_with_handlers()

        async def bad_handler(_args):
            raise RuntimeError("something broke")

        server.register_tool(
            "bad_tool", "Breaks", {"type": "object", "properties": {}}, bad_handler
        )
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.CallToolRequest]
        req = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="bad_tool", arguments={}),
        )
        result = await handler(req)
        content = result.root.content
        assert isinstance(content, list)
        assert len(content) > 0
        assert "error" in content[0].text.lower() or "something broke" in content[0].text.lower()

    @pytest.mark.asyncio
    async def test_resource_template_matching(self):
        server = _create_full_server_with_handlers()
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.ReadResourceRequest]
        req = types.ReadResourceRequest(
            method="resources/read",
            params=types.ReadResourceRequestParams(uri="file:///some/test/path.txt"),
        )
        result = await handler(req)
        contents = result.root.contents
        assert len(contents) > 0


class TestConcurrentToolCalls:
    """Test concurrent tool calls via handlers directly."""

    @pytest.mark.asyncio
    async def test_concurrent_echo_calls(self):
        server = _create_full_server()
        handler = server._tool_handlers["echo"]

        async def call_echo(i):
            return await handler({"message": f"Message {i}"})

        results = await asyncio.gather(*[call_echo(i) for i in range(20)])

        for i, result in enumerate(results):
            assert isinstance(result, ToolResult)
            assert not result.is_error
            assert f"Message {i}" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_concurrent_mixed_tool_calls(self):
        server = _create_full_server()
        echo_handler = server._tool_handlers["echo"]
        sys_handler = server._tool_handlers["system_info"]

        async def call_echo(i):
            return await echo_handler({"message": f"concurrent {i}"})

        async def call_sys():
            return await sys_handler({})

        tasks = [call_echo(i) for i in range(5)] + [call_sys() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        for result in results:
            assert isinstance(result, ToolResult)
            assert not result.is_error

    @pytest.mark.asyncio
    async def test_concurrent_resource_reads(self):
        server = _create_full_server()

        async def read_config():
            reader = server._resource_readers["config://server"]
            return await reader("config://server", {})

        async def read_health():
            reader = server._resource_readers["status://health"]
            return await reader("status://health", {})

        results = await asyncio.gather(
            *[read_config() for _ in range(5)] + [read_health() for _ in range(5)]
        )

        for result in results:
            assert isinstance(result, ResourceContent)
            assert result.text is not None

    @pytest.mark.asyncio
    async def test_concurrent_prompt_generations(self):
        server = _create_full_server()
        generator = server._prompt_generators["code_review"]

        async def gen_prompt(i):
            return await generator({"code": f"x = {i}", "language": "python"})

        results = await asyncio.gather(*[gen_prompt(i) for i in range(10)])

        for i, messages in enumerate(results):
            assert len(messages) > 0
            assert f"x = {i}" in messages[0].content

    @pytest.mark.asyncio
    async def test_concurrent_via_handler_setup(self):
        server = _create_full_server_with_handlers()
        mcp_server = server.server
        handler = mcp_server.request_handlers[types.CallToolRequest]

        async def call_via_handler(i):
            req = types.CallToolRequest(
                method="tools/call",
                params=types.CallToolRequestParams(
                    name="echo", arguments={"message": f"async {i}"}
                ),
            )
            return await handler(req)

        results = await asyncio.gather(*[call_via_handler(i) for i in range(10)])

        for i, result in enumerate(results):
            content = result.root.content
            assert any(f"async {i}" in c.text for c in content if isinstance(c, types.TextContent))
