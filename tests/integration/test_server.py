"""Integration tests for MCP server."""

from io import StringIO

import pytest

from tfo_mcp.infrastructure.config import Config
from tfo_mcp.presentation.server import MCPServer


class TestMCPServer:
    """Test MCP server integration."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.fixture
    def server(self, config):
        """Create test server."""
        stdin = StringIO()
        stdout = StringIO()
        return MCPServer(config, stdin=stdin, stdout=stdout)

    @pytest.mark.asyncio
    async def test_handle_initialize(self, server):
        """Test initialize request handling."""
        params = {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test", "version": "1.0"},
            "capabilities": {},
        }
        result = await server._handle_initialize(params)
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert server.session is not None
        assert server.session.is_ready

    @pytest.mark.asyncio
    async def test_handle_ping(self, server):
        """Test ping request handling."""
        result = await server._handle_ping({})
        assert result == {}

    @pytest.mark.asyncio
    async def test_make_response(self, server):
        """Test response creation."""
        response = server._make_response(1, result={"key": "value"})
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert response["result"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_make_error_response(self, server):
        """Test error response creation."""
        from tfo_mcp.domain.valueobjects import MCPErrorCode

        response = server._make_response(
            1,
            error=server._make_error(MCPErrorCode.METHOD_NOT_FOUND, "Not found"),
        )
        assert "error" in response
        assert response["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, server):
        """Test tools/list handling."""
        # First initialize
        await server._handle_initialize(
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test", "version": "1.0"},
            }
        )

        result = await server._handle_tools_list({})
        assert "tools" in result
        assert isinstance(result["tools"], list)

    @pytest.mark.asyncio
    async def test_handle_resources_list(self, server):
        """Test resources/list handling."""
        await server._handle_initialize(
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test", "version": "1.0"},
            }
        )

        result = await server._handle_resources_list({})
        assert "resources" in result

    @pytest.mark.asyncio
    async def test_handle_prompts_list(self, server):
        """Test prompts/list handling."""
        await server._handle_initialize(
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test", "version": "1.0"},
            }
        )

        result = await server._handle_prompts_list({})
        assert "prompts" in result


class TestServerRequestHandling:
    """Test full request/response cycle."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config()

    @pytest.mark.asyncio
    async def test_handle_full_request(self, config):
        """Test handling a complete JSON-RPC request."""
        stdin = StringIO()
        stdout = StringIO()
        server = MCPServer(config, stdin=stdin, stdout=stdout)

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        }

        response = await server._handle_request(request)
        assert response is not None
        assert response["id"] == 1
        assert "result" in response

    @pytest.mark.asyncio
    async def test_handle_notification(self, config):
        """Test handling notification (no id)."""
        stdin = StringIO()
        stdout = StringIO()
        server = MCPServer(config, stdin=stdin, stdout=stdout)

        # First initialize
        await server._handle_initialize(
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test", "version": "1.0"},
            }
        )

        request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }

        response = await server._handle_request(request)
        assert response is None  # Notifications don't get responses
