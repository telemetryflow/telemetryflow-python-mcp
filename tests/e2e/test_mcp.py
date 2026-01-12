"""End-to-end tests for MCP protocol.

These tests verify the complete MCP protocol flow including:
- JSON-RPC 2.0 message handling
- Full initialization handshake
- Tools workflow (list, call)
- Resources workflow (list, read)
- Prompts workflow (list, get)
- Session lifecycle management
"""

import asyncio
from io import StringIO

import pytest

from tfo_mcp.domain.valueobjects import MCPErrorCode
from tfo_mcp.infrastructure.config import Config
from tfo_mcp.presentation.prompts.builtin_prompts import register_builtin_prompts
from tfo_mcp.presentation.resources.builtin_resources import register_builtin_resources
from tfo_mcp.presentation.server import MCPServer
from tfo_mcp.presentation.tools.builtin_tools import register_builtin_tools


class TestMCPInitialization:
    """Test MCP initialization handshake."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    def server(self, config):
        """Create test server."""
        return MCPServer(config, stdin=StringIO(), stdout=StringIO())

    @pytest.mark.asyncio
    async def test_initialize_handshake(self, server):
        """Test complete initialize handshake."""
        # Send initialize request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0",
                },
                "capabilities": {},
            },
        }

        response = await server._handle_request(request)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response

        result = response["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert "serverInfo" in result
        assert "capabilities" in result

    @pytest.mark.asyncio
    async def test_initialized_notification(self, server):
        """Test notifications/initialized handling."""
        # First initialize
        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )

        # Send initialized notification
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }

        response = await server._handle_request(notification)

        # Notifications should not return a response
        assert response is None

    @pytest.mark.asyncio
    async def test_ping(self, server):
        """Test ping method."""
        response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "ping",
                "params": {},
            }
        )

        assert response is not None
        assert response["result"] == {}


class TestMCPTools:
    """Test MCP tools workflow."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    async def initialized_server(self, config):
        """Create and initialize server."""
        server = MCPServer(config, stdin=StringIO(), stdout=StringIO())

        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )

        # Register builtins
        register_builtin_tools(server.session, None)
        register_builtin_resources(server.session, config)
        register_builtin_prompts(server.session)

        return server

    @pytest.mark.asyncio
    async def test_tools_list(self, initialized_server):
        """Test tools/list method."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
        )

        assert response is not None
        assert "result" in response
        assert "tools" in response["result"]

        tools = response["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Verify tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    @pytest.mark.asyncio
    async def test_tools_call_echo(self, initialized_server):
        """Test tools/call with echo tool."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "echo",
                    "arguments": {"message": "Hello, World!"},
                },
            }
        )

        assert response is not None
        assert "result" in response
        assert "content" in response["result"]
        # isError is only present when True, absent means success
        assert response["result"].get("isError", False) is False

        content = response["result"]["content"]
        assert len(content) > 0
        assert "Hello, World!" in content[0]["text"]

    @pytest.mark.asyncio
    async def test_tools_call_system_info(self, initialized_server):
        """Test tools/call with system_info tool."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "system_info",
                    "arguments": {},
                },
            }
        )

        assert response is not None
        assert "result" in response
        # isError is only present when True, absent means success
        assert response["result"].get("isError", False) is False

        content = response["result"]["content"]
        text = content[0]["text"]
        assert "platform" in text.lower() or "system" in text.lower()

    @pytest.mark.asyncio
    async def test_tools_call_not_found(self, initialized_server):
        """Test tools/call with nonexistent tool."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {},
                },
            }
        )

        assert response is not None
        # Tool not found returns result with isError: True per MCP spec
        assert "result" in response
        assert response["result"]["isError"] is True
        assert "nonexistent_tool" in response["result"]["content"][0]["text"]


class TestMCPResources:
    """Test MCP resources workflow."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    async def initialized_server(self, config):
        """Create and initialize server."""
        server = MCPServer(config, stdin=StringIO(), stdout=StringIO())

        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )

        # Register builtins
        register_builtin_tools(server.session, None)
        register_builtin_resources(server.session, config)
        register_builtin_prompts(server.session)

        return server

    @pytest.mark.asyncio
    async def test_resources_list(self, initialized_server):
        """Test resources/list method."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/list",
                "params": {},
            }
        )

        assert response is not None
        assert "result" in response
        assert "resources" in response["result"]

        resources = response["result"]["resources"]
        assert isinstance(resources, list)

        # Verify resource structure
        for resource in resources:
            assert "uri" in resource
            assert "name" in resource

    @pytest.mark.asyncio
    async def test_resources_read_config(self, initialized_server):
        """Test resources/read with config resource."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/read",
                "params": {"uri": "config://server"},
            }
        )

        assert response is not None
        assert "result" in response
        assert "contents" in response["result"]

        contents = response["result"]["contents"]
        assert len(contents) > 0

        # Content should be JSON
        content = contents[0]
        assert content["mimeType"] == "application/json"

    @pytest.mark.asyncio
    async def test_resources_read_health(self, initialized_server):
        """Test resources/read with health resource."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "status://health"},
            }
        )

        assert response is not None
        assert "result" in response
        assert "contents" in response["result"]

    @pytest.mark.asyncio
    async def test_resources_read_not_found(self, initialized_server):
        """Test resources/read with nonexistent resource."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "resources/read",
                "params": {"uri": "nonexistent://resource"},
            }
        )

        assert response is not None
        assert "error" in response

    @pytest.mark.asyncio
    async def test_resources_templates_list(self, initialized_server):
        """Test resources/templates/list method."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "resources/templates/list",
                "params": {},
            }
        )

        assert response is not None
        assert "result" in response
        assert "resourceTemplates" in response["result"]


class TestMCPPrompts:
    """Test MCP prompts workflow."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    async def initialized_server(self, config):
        """Create and initialize server."""
        server = MCPServer(config, stdin=StringIO(), stdout=StringIO())

        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )

        # Register builtins
        register_builtin_tools(server.session, None)
        register_builtin_resources(server.session, config)
        register_builtin_prompts(server.session)

        return server

    @pytest.mark.asyncio
    async def test_prompts_list(self, initialized_server):
        """Test prompts/list method."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "prompts/list",
                "params": {},
            }
        )

        assert response is not None
        assert "result" in response
        assert "prompts" in response["result"]

        prompts = response["result"]["prompts"]
        assert isinstance(prompts, list)
        assert len(prompts) >= 3  # At least 3 built-in prompts

        # Verify prompt structure
        for prompt in prompts:
            assert "name" in prompt
            assert "description" in prompt

    @pytest.mark.asyncio
    async def test_prompts_get_code_review(self, initialized_server):
        """Test prompts/get with code_review prompt."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "prompts/get",
                "params": {
                    "name": "code_review",
                    "arguments": {
                        "code": "def hello(): print('world')",
                        "language": "python",
                    },
                },
            }
        )

        assert response is not None
        assert "result" in response
        assert "messages" in response["result"]

        messages = response["result"]["messages"]
        assert len(messages) > 0
        assert messages[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_prompts_get_not_found(self, initialized_server):
        """Test prompts/get with nonexistent prompt."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "prompts/get",
                "params": {
                    "name": "nonexistent_prompt",
                    "arguments": {},
                },
            }
        )

        assert response is not None
        assert "error" in response


class TestMCPLogging:
    """Test MCP logging capability."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    async def initialized_server(self, config):
        """Create and initialize server."""
        server = MCPServer(config, stdin=StringIO(), stdout=StringIO())

        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )

        # Register builtins
        register_builtin_tools(server.session, None)
        register_builtin_resources(server.session, config)
        register_builtin_prompts(server.session)

        return server

    @pytest.mark.asyncio
    async def test_logging_set_level(self, initialized_server):
        """Test logging/setLevel method."""
        response = await initialized_server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "logging/setLevel",
                "params": {"level": "debug"},
            }
        )

        assert response is not None
        assert "result" in response


class TestMCPErrorHandling:
    """Test MCP error handling."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    def server(self, config):
        """Create test server."""
        return MCPServer(config, stdin=StringIO(), stdout=StringIO())

    @pytest.mark.asyncio
    async def test_invalid_json(self, server):
        """Test handling of invalid JSON."""
        # This would be tested at the transport level
        pass

    @pytest.mark.asyncio
    async def test_method_not_found(self, server):
        """Test method not found error."""
        response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "nonexistent/method",
                "params": {},
            }
        )

        assert response is not None
        assert "error" in response
        assert response["error"]["code"] == MCPErrorCode.METHOD_NOT_FOUND.value

    @pytest.mark.asyncio
    async def test_invalid_params(self, server):
        """Test invalid params error."""
        # First initialize
        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )

        # Call tool with missing required params
        response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {},  # Missing name
            }
        )

        assert response is not None
        assert "error" in response


class TestMCPSessionLifecycle:
    """Test MCP session lifecycle."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    def server(self, config):
        """Create test server."""
        return MCPServer(config, stdin=StringIO(), stdout=StringIO())

    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self, server, config):
        """Test complete session lifecycle."""
        # 1. Initialize
        init_response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "lifecycle-test", "version": "1.0"},
                    "capabilities": {},
                },
            }
        )
        assert "result" in init_response
        assert server.session.is_ready

        # Register builtins after initialization
        register_builtin_tools(server.session, None)
        register_builtin_resources(server.session, config)
        register_builtin_prompts(server.session)

        # 2. Send initialized notification
        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
        )

        # 3. List tools
        tools_response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
        )
        assert "result" in tools_response
        assert len(tools_response["result"]["tools"]) > 0

        # 4. Call a tool
        call_response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "echo",
                    "arguments": {"message": "lifecycle test"},
                },
            }
        )
        assert "result" in call_response

        # 5. List resources
        resources_response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/list",
                "params": {},
            }
        )
        assert "result" in resources_response

        # 6. List prompts
        prompts_response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "prompts/list",
                "params": {},
            }
        )
        assert "result" in prompts_response

    @pytest.mark.asyncio
    async def test_operations_before_initialize(self, server):
        """Test operations before initialize should fail or return empty."""
        response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }
        )

        # Should either error or return empty tools
        assert response is not None


class TestMCPConcurrency:
    """Test MCP concurrent operations."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, config):
        """Test concurrent tool calls."""
        server = MCPServer(config, stdin=StringIO(), stdout=StringIO())

        # Initialize
        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "concurrent-test", "version": "1.0"},
                },
            }
        )

        # Register builtins
        register_builtin_tools(server.session, None)
        register_builtin_resources(server.session, config)
        register_builtin_prompts(server.session)

        # Make concurrent tool calls
        async def call_echo(i):
            return await server._handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 100 + i,
                    "method": "tools/call",
                    "params": {
                        "name": "echo",
                        "arguments": {"message": f"Message {i}"},
                    },
                }
            )

        responses = await asyncio.gather(*[call_echo(i) for i in range(10)])

        # All should succeed
        for i, response in enumerate(responses):
            assert "result" in response
            assert f"Message {i}" in response["result"]["content"][0]["text"]


class TestJSONRPCCompliance:
    """Test JSON-RPC 2.0 compliance."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    def server(self, config):
        """Create test server."""
        return MCPServer(config, stdin=StringIO(), stdout=StringIO())

    @pytest.mark.asyncio
    async def test_response_format(self, server):
        """Test response follows JSON-RPC 2.0 format."""
        response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "ping",
                "params": {},
            }
        )

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response or "error" in response

    @pytest.mark.asyncio
    async def test_error_format(self, server):
        """Test error follows JSON-RPC 2.0 format."""
        response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "unknown/method",
                "params": {},
            }
        )

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response

        error = response["error"]
        assert "code" in error
        assert "message" in error
        assert isinstance(error["code"], int)

    @pytest.mark.asyncio
    async def test_notification_no_response(self, server):
        """Test notifications don't return responses."""
        # Initialize first
        await server._handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            }
        )

        # Notification (no id)
        response = await server._handle_request(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
        )

        assert response is None

    @pytest.mark.asyncio
    async def test_id_preservation(self, server):
        """Test request ID is preserved in response."""
        test_ids = [1, "string-id", 999, "uuid-like-123"]

        for test_id in test_ids:
            response = await server._handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": test_id,
                    "method": "ping",
                    "params": {},
                }
            )

            assert response["id"] == test_id
