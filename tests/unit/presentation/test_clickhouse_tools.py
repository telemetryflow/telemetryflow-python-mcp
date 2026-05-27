from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tfo_mcp.domain.entities import ToolResult
from tfo_mcp.infrastructure.config import Config
from tfo_mcp.infrastructure.config.config import AnalyticsConfig
from tfo_mcp.presentation.tools.tfo_clickhouse_tools import (
    TFO_CLICKHOUSE_TOOLS,
    _ch_api_usage_handler,
    _ch_error_analytics_handler,
    _ch_query_handler,
    _ch_session_analytics_handler,
    _ch_tool_analytics_handler,
    register_clickhouse_tools,
)


@pytest.fixture
def mock_config():
    config = Config()
    config.analytics = AnalyticsConfig(
        clickhouse_url="clickhouse://localhost:9000/tfo_mcp_analytics"
    )
    return config


class TestChQueryHandler:
    async def test_missing_query(self):
        result = await _ch_query_handler({})
        assert result.is_error
        assert "Query is required" in result.content[0]["text"]

    async def test_non_select_in_readonly(self):
        result = await _ch_query_handler({"query": "DROP TABLE t", "read_only": True})
        assert result.is_error
        assert "Only SELECT" in result.content[0]["text"]

    async def test_insert_blocked(self):
        result = await _ch_query_handler({"query": "INSERT INTO t VALUES (1)", "read_only": True})
        assert result.is_error

    async def test_update_blocked(self):
        result = await _ch_query_handler(
            {"query": "ALTER TABLE t DROP COLUMN x", "read_only": True}
        )
        assert result.is_error

    async def test_select_allowed(self, mock_config):
        mock_result = MagicMock()
        mock_result.column_names = ["id", "name"]
        mock_result.result_rows = [(1, "test")]

        mock_ch_client = MagicMock()
        mock_ch_client.query.return_value = mock_result

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict(
                "sys.modules",
                {
                    "clickhouse_connect": MagicMock(
                        get_client=MagicMock(return_value=mock_ch_client)
                    )
                },
            ),
        ):
            result = await _ch_query_handler({"query": "SELECT 1", "read_only": True})
            assert not result.is_error

    async def test_describe_allowed(self, mock_config):
        mock_result = MagicMock()
        mock_result.column_names = ["name", "type"]
        mock_result.result_rows = [("id", "UInt64")]

        mock_ch_client = MagicMock()
        mock_ch_client.query.return_value = mock_result

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict(
                "sys.modules",
                {
                    "clickhouse_connect": MagicMock(
                        get_client=MagicMock(return_value=mock_ch_client)
                    )
                },
            ),
        ):
            result = await _ch_query_handler({"query": "DESCRIBE TABLE t", "read_only": True})
            assert not result.is_error

    async def test_with_datetime_values(self, mock_config):
        from datetime import datetime

        mock_result = MagicMock()
        mock_result.column_names = ["ts"]
        mock_result.result_rows = [(datetime(2024, 1, 1),)]

        mock_ch_client = MagicMock()
        mock_ch_client.query.return_value = mock_result

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict(
                "sys.modules",
                {
                    "clickhouse_connect": MagicMock(
                        get_client=MagicMock(return_value=mock_ch_client)
                    )
                },
            ),
        ):
            result = await _ch_query_handler({"query": "SELECT now()"})
            assert not result.is_error

    async def test_with_bytes_values(self, mock_config):
        mock_result = MagicMock()
        mock_result.column_names = ["data"]
        mock_result.result_rows = [(b"binary",)]

        mock_ch_client = MagicMock()
        mock_ch_client.query.return_value = mock_result

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict(
                "sys.modules",
                {
                    "clickhouse_connect": MagicMock(
                        get_client=MagicMock(return_value=mock_ch_client)
                    )
                },
            ),
        ):
            result = await _ch_query_handler({"query": "SELECT data FROM t"})
            assert not result.is_error

    async def test_import_error(self):
        with patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config):
            import builtins

            real_import = builtins.__import__

            def custom_import(name, *args, **kwargs):
                if name == "clickhouse_connect":
                    raise ImportError("no ch")
                return real_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=custom_import):
                result = await _ch_query_handler({"query": "SELECT 1"})
                assert result.is_error
                assert "clickhouse-connect not installed" in result.content[0]["text"]

    async def test_generic_exception(self, mock_config):
        mock_ch = MagicMock()
        mock_ch.get_client.side_effect = Exception("connection failed")

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"clickhouse_connect": mock_ch}),
        ):
            result = await _ch_query_handler({"query": "SELECT 1"})
            assert result.is_error
            assert "ClickHouse error" in result.content[0]["text"]

    async def test_truncation(self, mock_config):
        rows = [(i,) for i in range(200)]
        mock_result = MagicMock()
        mock_result.column_names = ["id"]
        mock_result.result_rows = rows

        mock_ch_client = MagicMock()
        mock_ch_client.query.return_value = mock_result

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict(
                "sys.modules",
                {
                    "clickhouse_connect": MagicMock(
                        get_client=MagicMock(return_value=mock_ch_client)
                    )
                },
            ),
        ):
            result = await _ch_query_handler({"query": "SELECT * FROM t", "max_rows": 50})
            assert not result.is_error

    async def test_url_parsing_with_port(self, mock_config):
        mock_config.analytics = AnalyticsConfig(clickhouse_url="clickhouse://ch-host:8123/my_db")
        mock_result = MagicMock()
        mock_result.column_names = ["x"]
        mock_result.result_rows = [(1,)]

        mock_ch_client = MagicMock()
        mock_ch_client.query.return_value = mock_result

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict(
                "sys.modules",
                {
                    "clickhouse_connect": MagicMock(
                        get_client=MagicMock(return_value=mock_ch_client)
                    )
                },
            ),
        ):
            result = await _ch_query_handler({"query": "SELECT 1"})
            assert not result.is_error

    async def test_url_parsing_no_port(self, mock_config):
        mock_config.analytics = AnalyticsConfig(clickhouse_url="clickhouse://ch-host/my_db")
        mock_result = MagicMock()
        mock_result.column_names = ["x"]
        mock_result.result_rows = [(1,)]

        mock_ch_client = MagicMock()
        mock_ch_client.query.return_value = mock_result

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict(
                "sys.modules",
                {
                    "clickhouse_connect": MagicMock(
                        get_client=MagicMock(return_value=mock_ch_client)
                    )
                },
            ),
        ):
            result = await _ch_query_handler({"query": "SELECT 1"})
            assert not result.is_error


class TestChToolAnalyticsHandler:
    async def test_without_tool_name(self):
        mock_result = ToolResult.json({"rows": [], "count": 0})
        with patch(
            "tfo_mcp.presentation.tools.tfo_clickhouse_tools._ch_query_handler",
            AsyncMock(return_value=mock_result),
        ):
            result = await _ch_tool_analytics_handler({"hours": 24, "limit": 10})
            assert result is not None
            assert not result.is_error

    async def test_with_tool_name(self):
        mock_result = ToolResult.json({"rows": [], "count": 0})
        with patch(
            "tfo_mcp.presentation.tools.tfo_clickhouse_tools._ch_query_handler",
            AsyncMock(return_value=mock_result),
        ):
            result = await _ch_tool_analytics_handler({"tool_name": "echo", "hours": 12})
            assert result is not None


class TestChSessionAnalyticsHandler:
    async def test_session_analytics(self):
        mock_result = ToolResult.json({"rows": [], "count": 0})
        with patch(
            "tfo_mcp.presentation.tools.tfo_clickhouse_tools._ch_query_handler",
            AsyncMock(return_value=mock_result),
        ):
            result = await _ch_session_analytics_handler({"hours": 168, "limit": 50})
            assert result is not None


class TestChErrorAnalyticsHandler:
    async def test_error_analytics(self):
        mock_result = ToolResult.json({"rows": [], "count": 0})
        with patch(
            "tfo_mcp.presentation.tools.tfo_clickhouse_tools._ch_query_handler",
            AsyncMock(return_value=mock_result),
        ):
            result = await _ch_error_analytics_handler({"hours": 72, "limit": 50})
            assert result is not None


class TestChApiUsageHandler:
    async def test_without_model(self):
        mock_result = ToolResult.json({"rows": [], "count": 0})
        with patch(
            "tfo_mcp.presentation.tools.tfo_clickhouse_tools._ch_query_handler",
            AsyncMock(return_value=mock_result),
        ):
            result = await _ch_api_usage_handler({"hours": 168})
            assert result is not None

    async def test_with_model(self):
        mock_result = ToolResult.json({"rows": [], "count": 0})
        with patch(
            "tfo_mcp.presentation.tools.tfo_clickhouse_tools._ch_query_handler",
            AsyncMock(return_value=mock_result),
        ):
            result = await _ch_api_usage_handler({"hours": 24, "model": "claude-sonnet-4-20250514"})
            assert result is not None


class TestRegisterClickhouseTools:
    def test_registers_all_tools(self):
        mock_server = MagicMock()
        register_clickhouse_tools(mock_server)
        assert mock_server.register_tool.call_count == len(TFO_CLICKHOUSE_TOOLS)

    def test_tool_names(self):
        names = [t["name"] for t in TFO_CLICKHOUSE_TOOLS]
        assert "ch_query" in names
        assert "ch_tool_analytics" in names
        assert "ch_session_analytics" in names
        assert "ch_error_analytics" in names
        assert "ch_api_usage" in names

    def test_all_have_required_fields(self):
        for tool_def in TFO_CLICKHOUSE_TOOLS:
            assert "name" in tool_def
            assert "description" in tool_def
            assert "input_schema" in tool_def
            assert "handler" in tool_def
            assert "category" in tool_def
