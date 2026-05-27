import mcp.types as types
import pytest

from tfo_mcp.infrastructure.config import Config
from tfo_mcp.presentation.server.server import MCPServer


def _make_config():
    return Config()


class TestMCPServerInit:
    def test_session_property_none(self):
        config = _make_config()
        server = MCPServer(config)
        assert server.session is None

    def test_server_property(self):
        config = _make_config()
        server = MCPServer(config)
        assert server.server is not None


class TestMCPServerRegisterTool:
    def test_register_tool(self):
        config = _make_config()
        server = MCPServer(config)
        server.register_tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            handler=None,
        )
        assert "test_tool" in server._tool_definitions


class TestMCPServerRegisterResource:
    def test_register_template_resource(self):
        config = _make_config()
        server = MCPServer(config)
        server.register_resource(
            uri="config://app/{key}",
            name="App Config",
            description="App config template",
            mime_type="application/json",
            reader=None,
        )
        assert len(server._template_definitions) == 1

    def test_register_regular_resource(self):
        config = _make_config()
        server = MCPServer(config)
        server.register_resource(
            uri="config://server",
            name="Server Config",
            description="Server config",
            mime_type="application/json",
            reader=None,
        )
        assert len(server._resource_definitions) == 1


class TestMCPServerRegisterPrompt:
    def test_register_prompt(self):
        config = _make_config()
        server = MCPServer(config)
        server.register_prompt(
            name="test_prompt",
            description="A test prompt",
            arguments=None,
            generator=None,
        )
        assert "test_prompt" in server._prompt_definitions


class TestMCPServerStop:
    def test_stop(self):
        config = _make_config()
        server = MCPServer(config)
        server._running = True
        server.stop()
        assert server._running is False


class TestMCPServerCallToolHandler:
    @pytest.mark.asyncio
    async def test_call_tool_not_found(self):
        config = _make_config()
        server = MCPServer(config)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.CallToolRequest)
        assert handler is not None
        result = await handler(
            types.CallToolRequest(
                method="tools/call",
                params=types.CallToolRequestParams(name="nonexistent", arguments={}),
            )
        )
        texts = [c.text for c in result.root.content]
        assert any("Tool not found" in t for t in texts)

    @pytest.mark.asyncio
    async def test_call_tool_with_tool_result(self):
        from tfo_mcp.domain.entities import ToolResult

        config = _make_config()
        server = MCPServer(config)

        async def mock_handler(_args):
            return ToolResult.text("mocked result")

        server.register_tool("mock_tool", "Mock", {"type": "object"}, handler=mock_handler)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.CallToolRequest)
        assert handler is not None
        result = await handler(
            types.CallToolRequest(
                method="tools/call",
                params=types.CallToolRequestParams(name="mock_tool", arguments={}),
            )
        )
        texts = [c.text for c in result.root.content]
        assert any("mocked result" in t for t in texts)

    @pytest.mark.asyncio
    async def test_call_tool_exception(self):
        config = _make_config()
        server = MCPServer(config)

        async def failing_handler(_args):
            raise RuntimeError("boom")

        server.register_tool("fail_tool", "Fail", {"type": "object"}, handler=failing_handler)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.CallToolRequest)
        assert handler is not None
        result = await handler(
            types.CallToolRequest(
                method="tools/call",
                params=types.CallToolRequestParams(name="fail_tool", arguments={}),
            )
        )
        texts = [c.text for c in result.root.content]
        assert any("Error" in t for t in texts)

    @pytest.mark.asyncio
    async def test_call_tool_returns_string(self):
        config = _make_config()
        server = MCPServer(config)

        async def str_handler(_args):
            return "plain string"

        server.register_tool("str_tool", "Str", {"type": "object"}, handler=str_handler)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.CallToolRequest)
        assert handler is not None
        result = await handler(
            types.CallToolRequest(
                method="tools/call",
                params=types.CallToolRequestParams(name="str_tool", arguments={}),
            )
        )
        texts = [c.text for c in result.root.content]
        assert any("plain string" in t for t in texts)


class TestMCPServerReadResourceHandler:
    @pytest.mark.asyncio
    async def test_read_resource_with_text(self):
        from tfo_mcp.domain.entities import ResourceContent

        config = _make_config()
        server = MCPServer(config)

        async def mock_reader(uri, _params):
            return ResourceContent(uri=uri, mime_type="text/plain", text="hello world")

        server.register_resource("config://test", "Test", "desc", reader=mock_reader)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.ReadResourceRequest)
        assert handler is not None
        result = await handler(
            types.ReadResourceRequest(
                method="resources/read",
                params=types.ReadResourceRequestParams(uri="config://test"),
            )
        )
        assert "hello world" in str(result)

    @pytest.mark.asyncio
    async def test_read_resource_with_blob(self):
        from tfo_mcp.domain.entities import ResourceContent

        config = _make_config()
        server = MCPServer(config)

        async def mock_reader(uri, _params):
            return ResourceContent(uri=uri, mime_type="application/octet-stream", blob=b"\x00\x01")

        server.register_resource("config://binary", "Binary", "desc", reader=mock_reader)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.ReadResourceRequest)
        assert handler is not None
        result = await handler(
            types.ReadResourceRequest(
                method="resources/read",
                params=types.ReadResourceRequestParams(uri="config://binary"),
            )
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_read_resource_template_match(self):
        from tfo_mcp.domain.entities import ResourceContent

        config = _make_config()
        server = MCPServer(config)

        async def mock_reader(uri, _params):
            return ResourceContent(uri=uri, mime_type="application/json", text='{"ok": true}')

        server.register_resource("config://app/{key}", "App", "desc", reader=mock_reader)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.ReadResourceRequest)
        assert handler is not None
        result = await handler(
            types.ReadResourceRequest(
                method="resources/read",
                params=types.ReadResourceRequestParams(uri="config://app/theme"),
            )
        )
        assert '"ok"' in str(result)

    @pytest.mark.asyncio
    async def test_read_resource_not_found(self):
        config = _make_config()
        server = MCPServer(config)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.ReadResourceRequest)
        assert handler is not None
        result = await handler(
            types.ReadResourceRequest(
                method="resources/read",
                params=types.ReadResourceRequestParams(uri="config://nonexistent"),
            )
        )
        assert "Resource not found" in str(result)

    @pytest.mark.asyncio
    async def test_read_resource_fallback_str(self):
        config = _make_config()
        server = MCPServer(config)

        async def mock_reader(_uri, _params):
            return "plain string result"

        server.register_resource("config://strtest", "StrTest", "desc", reader=mock_reader)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.ReadResourceRequest)
        assert handler is not None
        result = await handler(
            types.ReadResourceRequest(
                method="resources/read",
                params=types.ReadResourceRequestParams(uri="config://strtest"),
            )
        )
        assert "plain string result" in str(result)


class TestMCPServerGetPromptHandler:
    @pytest.mark.asyncio
    async def test_get_prompt_handler(self):
        from tfo_mcp.domain.entities import PromptMessage
        from tfo_mcp.domain.valueobjects import Role

        config = _make_config()
        server = MCPServer(config)

        async def mock_generator(_args):
            return [PromptMessage(role=Role.USER, content="hello")]

        server.register_prompt("test_prompt", "Test", arguments=None, generator=mock_generator)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.GetPromptRequest)
        assert handler is not None
        result = await handler(
            types.GetPromptRequest(
                method="prompts/get",
                params=types.GetPromptRequestParams(name="test_prompt", arguments={}),
            )
        )
        assert result.root.messages[0].content.text == "hello"

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(self):
        config = _make_config()
        server = MCPServer(config)
        server._setup_handlers()
        handler = server.server.request_handlers.get(types.GetPromptRequest)
        assert handler is not None
        with pytest.raises(ValueError, match="Prompt not found"):
            await handler(
                types.GetPromptRequest(
                    method="prompts/get",
                    params=types.GetPromptRequestParams(name="nonexistent", arguments={}),
                )
            )
