"""Integration tests for MCPServer registration and handler setup."""

from __future__ import annotations

import json

import mcp.types as types
import pytest

from tfo_mcp.domain.entities import ResourceContent, ToolResult
from tfo_mcp.infrastructure.config import Config
from tfo_mcp.presentation.prompts.builtin_prompts import register_builtin_prompts
from tfo_mcp.presentation.resources.builtin_resources import register_builtin_resources
from tfo_mcp.presentation.server import MCPServer
from tfo_mcp.presentation.tools.builtin_tools import BUILTIN_TOOLS, register_builtin_tools


class TestMCPServerCreation:
    """Test MCPServer instantiation."""

    def test_server_creation(self):
        config = Config()
        server = MCPServer(config)
        assert server.server is not None

    def test_server_internal_dicts_initialized(self):
        config = Config()
        server = MCPServer(config)
        assert isinstance(server._tool_definitions, dict)
        assert isinstance(server._resource_definitions, list)
        assert isinstance(server._template_definitions, list)
        assert isinstance(server._prompt_definitions, dict)
        assert isinstance(server._tool_handlers, dict)
        assert isinstance(server._resource_readers, dict)
        assert isinstance(server._prompt_generators, dict)
        assert len(server._tool_definitions) == 0
        assert len(server._resource_definitions) == 0
        assert len(server._template_definitions) == 0
        assert len(server._prompt_definitions) == 0

    def test_server_property_returns_mcp_server(self):
        config = Config()
        server = MCPServer(config)
        from mcp.server import Server

        assert isinstance(server.server, Server)


class TestToolRegistration:
    """Test tool registration on MCPServer."""

    @pytest.fixture
    def server(self):
        config = Config()
        return MCPServer(config)

    def test_register_single_tool(self, server):
        async def handler(_args):
            return ToolResult.text("ok")

        server.register_tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}, "required": []},
            handler=handler,
        )
        assert "test_tool" in server._tool_definitions
        assert "test_tool" in server._tool_handlers
        assert server._tool_definitions["test_tool"].name == "test_tool"
        assert server._tool_definitions["test_tool"].description == "A test tool"

    def test_register_multiple_tools(self, server):
        for i in range(5):

            async def handler(_args, idx=i):
                return ToolResult.text(f"tool {idx}")

            server.register_tool(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={"type": "object", "properties": {}, "required": []},
                handler=handler,
            )
        assert len(server._tool_definitions) == 5

    def test_register_builtin_tools(self, server):
        register_builtin_tools(server, None)
        assert len(server._tool_definitions) == len(BUILTIN_TOOLS)
        for tool_def in BUILTIN_TOOLS:
            assert tool_def["name"] in server._tool_definitions
            assert tool_def["name"] in server._tool_handlers

    def test_builtin_tool_definitions_structure(self, server):
        register_builtin_tools(server, None)
        for name, tool in server._tool_definitions.items():
            assert isinstance(tool, types.Tool)
            assert tool.name == name
            assert isinstance(tool.description, str)
            assert isinstance(tool.inputSchema, dict)
            assert "type" in tool.inputSchema

    def test_register_tool_overwrites_existing(self, server):
        async def handler_v1(_args):
            return ToolResult.text("v1")

        async def handler_v2(_args):
            return ToolResult.text("v2")

        server.register_tool("dup", "v1", {"type": "object", "properties": {}}, handler_v1)
        server.register_tool("dup", "v2", {"type": "object", "properties": {}}, handler_v2)
        assert server._tool_definitions["dup"].description == "v2"
        assert server._tool_handlers["dup"] is handler_v2

    def test_tool_input_schema_stored(self, server):
        async def handler(_args):
            return ToolResult.text("ok")

        schema = {
            "type": "object",
            "properties": {"msg": {"type": "string", "description": "A message"}},
            "required": ["msg"],
        }
        server.register_tool("schema_test", "Schema test", schema, handler)
        assert server._tool_definitions["schema_test"].inputSchema == schema


class TestResourceRegistration:
    """Test resource registration on MCPServer."""

    @pytest.fixture
    def server(self):
        config = Config()
        return MCPServer(config)

    def test_register_static_resource(self, server):
        async def reader(uri, _params):
            return ResourceContent(uri=uri, mime_type="text/plain", text="hello")

        server.register_resource(
            uri="config://test",
            name="Test Config",
            description="A test config resource",
            mime_type="text/plain",
            reader=reader,
        )
        assert len(server._resource_definitions) == 1
        assert len(server._template_definitions) == 0
        assert "config://test" in server._resource_readers
        assert server._resource_definitions[0].name == "Test Config"

    def test_register_template_resource(self, server):
        async def reader(uri, _params):
            return ResourceContent(uri=uri, mime_type="text/plain", text="file")

        server.register_resource(
            uri="file:///{path}",
            name="File",
            description="Read a file",
            mime_type="text/plain",
            reader=reader,
        )
        assert len(server._resource_definitions) == 0
        assert len(server._template_definitions) == 1
        assert "file:///{path}" in server._resource_readers

    def test_register_builtin_resources(self, server):
        register_builtin_resources(server, Config())
        assert len(server._resource_definitions) >= 2
        assert len(server._template_definitions) >= 1

    def test_builtin_resource_definitions_structure(self, server):
        register_builtin_resources(server, Config())
        for resource in server._resource_definitions:
            assert isinstance(resource, types.Resource)
            assert resource.uri is not None
            assert resource.name is not None

    def test_builtin_template_definitions_structure(self, server):
        register_builtin_resources(server, Config())
        for template in server._template_definitions:
            assert isinstance(template, types.ResourceTemplate)
            assert template.uriTemplate is not None
            assert template.name is not None

    def test_static_and_template_mixed(self, server):
        async def reader(uri, _params):
            return ResourceContent(uri=uri, mime_type="text/plain", text="data")

        server.register_resource("a://b", "Static", "desc", "text/plain", reader)
        server.register_resource("c://{id}/d", "Template", "desc", "text/plain", reader)
        assert len(server._resource_definitions) == 1
        assert len(server._template_definitions) == 1


class TestPromptRegistration:
    """Test prompt registration on MCPServer."""

    @pytest.fixture
    def server(self):
        config = Config()
        return MCPServer(config)

    def test_register_single_prompt(self, server):
        async def generator(_args):
            from tfo_mcp.domain.entities import PromptMessage
            from tfo_mcp.domain.valueobjects import Role

            return [PromptMessage(role=Role.USER, content="hello")]

        server.register_prompt(
            name="test_prompt",
            description="A test prompt",
            arguments=[types.PromptArgument(name="input", description="test input", required=True)],
            generator=generator,
        )
        assert "test_prompt" in server._prompt_definitions
        assert "test_prompt" in server._prompt_generators
        prompt = server._prompt_definitions["test_prompt"]
        assert prompt.name == "test_prompt"
        assert len(prompt.arguments) == 1
        assert prompt.arguments[0].name == "input"

    def test_register_builtin_prompts(self, server):
        register_builtin_prompts(server)
        assert len(server._prompt_definitions) >= 3
        assert "code_review" in server._prompt_definitions
        assert "explain_code" in server._prompt_definitions
        assert "debug_help" in server._prompt_definitions

    def test_builtin_prompt_definitions_structure(self, server):
        register_builtin_prompts(server)
        for name, prompt in server._prompt_definitions.items():
            assert isinstance(prompt, types.Prompt)
            assert prompt.name == name
            assert isinstance(prompt.description, str)
            if prompt.arguments:
                for arg in prompt.arguments:
                    assert isinstance(arg, types.PromptArgument)
                    assert arg.name is not None

    def test_register_prompt_no_arguments(self, server):
        async def generator(_args):
            from tfo_mcp.domain.entities import PromptMessage
            from tfo_mcp.domain.valueobjects import Role

            return [PromptMessage(role=Role.USER, content="no args")]

        server.register_prompt("no_args_prompt", "No args", None, generator)
        assert "no_args_prompt" in server._prompt_definitions
        assert server._prompt_definitions["no_args_prompt"].arguments is None


class TestSetupHandlers:
    """Test _setup_handlers() method."""

    @pytest.fixture
    def server_with_builtins(self):
        config = Config()
        server = MCPServer(config)
        register_builtin_tools(server, None)
        register_builtin_resources(server, config)
        register_builtin_prompts(server)
        server._setup_handlers()
        return server

    def test_setup_handlers_creates_decorators(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler_keys = set(mcp_server.request_handlers.keys())
        assert types.ListToolsRequest in handler_keys
        assert types.CallToolRequest in handler_keys
        assert types.ListResourcesRequest in handler_keys
        assert types.ListResourceTemplatesRequest in handler_keys
        assert types.ReadResourceRequest in handler_keys
        assert types.ListPromptsRequest in handler_keys
        assert types.GetPromptRequest in handler_keys

    @pytest.mark.asyncio
    async def test_list_tools_handler(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.ListToolsRequest]
        req = types.ListToolsRequest(method="tools/list")
        result = await handler(req)
        tools = result.root.tools
        assert isinstance(tools, list)
        assert len(tools) >= 7
        tool_names = [t.name for t in tools]
        assert "echo" in tool_names
        assert "system_info" in tool_names

    @pytest.mark.asyncio
    async def test_list_resources_handler(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.ListResourcesRequest]
        req = types.ListResourcesRequest(method="resources/list")
        result = await handler(req)
        resources = result.root.resources
        assert isinstance(resources, list)
        assert len(resources) >= 2

    @pytest.mark.asyncio
    async def test_list_resource_templates_handler(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.ListResourceTemplatesRequest]
        req = types.ListResourceTemplatesRequest(method="resources/templates/list")
        result = await handler(req)
        templates = result.root.resourceTemplates
        assert isinstance(templates, list)
        assert len(templates) >= 1

    @pytest.mark.asyncio
    async def test_list_prompts_handler(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.ListPromptsRequest]
        req = types.ListPromptsRequest(method="prompts/list")
        result = await handler(req)
        prompts = result.root.prompts
        assert isinstance(prompts, list)
        assert len(prompts) >= 3
        prompt_names = [p.name for p in prompts]
        assert "code_review" in prompt_names

    @pytest.mark.asyncio
    async def test_call_tool_handler_echo(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.CallToolRequest]
        req = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="echo", arguments={"message": "hello"}),
        )
        result = await handler(req)
        content = result.root.content
        assert isinstance(content, list)
        assert len(content) >= 1
        assert "hello" in content[0].text

    @pytest.mark.asyncio
    async def test_call_tool_handler_not_found(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.CallToolRequest]
        req = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name="nonexistent_tool", arguments={}),
        )
        result = await handler(req)
        content = result.root.content
        assert isinstance(content, list)
        assert "not found" in content[0].text.lower() or "nonexistent_tool" in content[0].text

    @pytest.mark.asyncio
    async def test_read_resource_handler_config(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.ReadResourceRequest]
        req = types.ReadResourceRequest(
            method="resources/read",
            params=types.ReadResourceRequestParams(uri="config://server"),
        )
        result = await handler(req)
        contents = result.root.contents
        assert len(contents) > 0
        text = contents[0].text
        parsed = json.loads(text)
        assert "server" in parsed

    @pytest.mark.asyncio
    async def test_read_resource_handler_not_found(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.ReadResourceRequest]
        req = types.ReadResourceRequest(
            method="resources/read",
            params=types.ReadResourceRequestParams(uri="nonexistent://resource"),
        )
        result = await handler(req)
        contents = result.root.contents
        assert len(contents) > 0
        assert "not found" in contents[0].text.lower()

    @pytest.mark.asyncio
    async def test_get_prompt_handler(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.GetPromptRequest]
        req = types.GetPromptRequest(
            method="prompts/get",
            params=types.GetPromptRequestParams(
                name="code_review",
                arguments={"code": "print('hello')", "language": "python"},
            ),
        )
        result = await handler(req)
        assert isinstance(result.root, types.GetPromptResult)
        assert len(result.root.messages) > 0
        assert result.root.messages[0].role == "user"

    @pytest.mark.asyncio
    async def test_get_prompt_handler_not_found(self, server_with_builtins):
        mcp_server = server_with_builtins.server
        handler = mcp_server.request_handlers[types.GetPromptRequest]
        req = types.GetPromptRequest(
            method="prompts/get",
            params=types.GetPromptRequestParams(name="nonexistent_prompt", arguments={}),
        )
        with pytest.raises(ValueError):
            await handler(req)


class TestFullRegistration:
    """Test registering all builtin components together."""

    @pytest.fixture
    def full_server(self):
        config = Config()
        server = MCPServer(config)
        register_builtin_tools(server, None)
        register_builtin_resources(server, config)
        register_builtin_prompts(server)
        return server

    def test_all_tools_registered(self, full_server):
        assert len(full_server._tool_definitions) >= 7
        expected_tools = {
            "echo",
            "read_file",
            "write_file",
            "list_directory",
            "search_files",
            "execute_command",
            "system_info",
        }
        assert expected_tools.issubset(set(full_server._tool_definitions.keys()))

    def test_all_resources_registered(self, full_server):
        resource_uris = [str(r.uri) for r in full_server._resource_definitions]
        assert "config://server" in resource_uris
        assert "status://health" in resource_uris

    def test_all_templates_registered(self, full_server):
        template_uris = [t.uriTemplate for t in full_server._template_definitions]
        assert "file:///{path}" in template_uris

    def test_all_prompts_registered(self, full_server):
        expected_prompts = {"code_review", "explain_code", "debug_help"}
        assert expected_prompts.issubset(set(full_server._prompt_definitions.keys()))

    def test_all_handlers_present(self, full_server):
        for name in full_server._tool_definitions:
            assert name in full_server._tool_handlers
        for resource in full_server._resource_definitions:
            assert str(resource.uri) in full_server._resource_readers
        for template in full_server._template_definitions:
            assert template.uriTemplate in full_server._resource_readers
        for name in full_server._prompt_definitions:
            assert name in full_server._prompt_generators
