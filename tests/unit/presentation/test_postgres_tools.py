from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tfo_mcp.infrastructure.config import Config
from tfo_mcp.infrastructure.config.config import DatabaseConfig
from tfo_mcp.presentation.tools.tfo_postgres_tools import (
    TFO_POSTGRES_TOOLS,
    _pg_describe_table_handler,
    _pg_list_tables_handler,
    _pg_query_handler,
    _pg_sessions_handler,
    register_postgres_tools,
)


@pytest.fixture
def mock_config():
    config = Config()
    config.database = DatabaseConfig(postgres_url="postgres://test:test@localhost:5432/testdb")
    return config


class TestPgQueryHandler:
    async def test_missing_query(self):
        result = await _pg_query_handler({})
        assert result.is_error
        assert "Query is required" in result.content[0]["text"]

    async def test_non_select_in_readonly(self):
        result = await _pg_query_handler({"query": "DROP TABLE users", "read_only": True})
        assert result.is_error
        assert "Only SELECT" in result.content[0]["text"]

    async def test_insert_blocked_in_readonly(self):
        result = await _pg_query_handler({"query": "INSERT INTO t VALUES (1)", "read_only": True})
        assert result.is_error

    async def test_update_blocked_in_readonly(self):
        result = await _pg_query_handler({"query": "UPDATE t SET x=1", "read_only": True})
        assert result.is_error

    async def test_delete_blocked_in_readonly(self):
        result = await _pg_query_handler({"query": "DELETE FROM t", "read_only": True})
        assert result.is_error

    async def test_select_allowed_in_readonly(self):
        with patch("tfo_mcp.presentation.tools.tfo_postgres_tools._pg_query_handler"):
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_conn.close = AsyncMock()

            with (
                patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
                patch.dict(
                    "sys.modules", {"asyncpg": MagicMock(connect=AsyncMock(return_value=mock_conn))}
                ),
            ):
                pass

    async def test_generic_exception(self, mock_config):
        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(side_effect=Exception("connection failed"))

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_query_handler({"query": "SELECT 1"})
            assert result.is_error
            assert "PostgreSQL error" in result.content[0]["text"]

    async def test_with_mock_asyncpg(self, mock_config):
        mock_conn = AsyncMock()
        from datetime import datetime

        mock_conn.fetch = AsyncMock(
            return_value=[{"id": 1, "name": "test", "created_at": datetime(2024, 1, 1)}]
        )
        mock_conn.close = AsyncMock()

        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_query_handler({"query": "SELECT * FROM t", "max_rows": 100})
            assert not result.is_error
            assert "rows" in result.content[0]["text"]

    async def test_with_bytes_values(self, mock_config):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"id": 1, "data": b"binary_data"}])
        mock_conn.close = AsyncMock()

        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_query_handler({"query": "SELECT * FROM t"})
            assert not result.is_error

    async def test_truncation(self, mock_config):
        rows = [{"id": i} for i in range(200)]
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=rows)
        mock_conn.close = AsyncMock()

        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_query_handler({"query": "SELECT * FROM t", "max_rows": 50})
            assert not result.is_error
            assert (
                "truncated" in result.content[0]["text"].lower()
                or "true" in result.content[0]["text"].lower()
            )

    async def test_with_params(self, mock_config):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"id": 1}])
        mock_conn.close = AsyncMock()

        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_query_handler({"query": "SELECT $1", "params": [42]})
            assert not result.is_error


class TestPgListTablesHandler:
    async def test_list_tables(self, mock_config):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(
            return_value=[
                {"table_name": "sessions", "table_type": "BASE TABLE"},
                {"table_name": "events", "table_type": "BASE TABLE"},
            ]
        )
        mock_conn.close = AsyncMock()

        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_list_tables_handler({"schema": "public"})
            assert not result.is_error
            assert "sessions" in result.content[0]["text"]

    async def test_list_tables_error(self, mock_config):
        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(side_effect=Exception("err"))

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_list_tables_handler({})
            assert result.is_error


class TestPgDescribeTableHandler:
    async def test_missing_table(self):
        result = await _pg_describe_table_handler({})
        assert result.is_error
        assert "Table name is required" in result.content[0]["text"]

    async def test_describe_table(self, mock_config):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(
            side_effect=[
                [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "is_nullable": "NO",
                        "column_default": None,
                    }
                ],
                [{"indexname": "idx_id", "indexdef": "CREATE INDEX idx_id ON t (id)"}],
            ]
        )
        mock_conn.close = AsyncMock()

        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_describe_table_handler({"table": "sessions", "schema": "public"})
            assert not result.is_error
            assert "columns" in result.content[0]["text"]

    async def test_describe_table_error(self, mock_config):
        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(side_effect=Exception("err"))

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_describe_table_handler({"table": "sessions"})
            assert result.is_error


class TestPgSessionsHandler:
    async def test_list_sessions(self, mock_config):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(
            return_value=[
                {
                    "id": "s1",
                    "state": "ready",
                    "client_name": "test",
                    "server_name": "MCP",
                    "created_at": None,
                    "initialized_at": None,
                    "closed_at": None,
                }
            ]
        )
        mock_conn.close = AsyncMock()

        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_sessions_handler({"limit": 20})
            assert not result.is_error

    async def test_list_sessions_with_state(self, mock_config):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.close = AsyncMock()

        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_sessions_handler({"state": "ready", "limit": 10})
            assert not result.is_error

    async def test_list_sessions_error(self, mock_config):
        mock_asyncpg = MagicMock()
        mock_asyncpg.connect = AsyncMock(side_effect=Exception("err"))

        with (
            patch("tfo_mcp.infrastructure.config.load_config", return_value=mock_config),
            patch.dict("sys.modules", {"asyncpg": mock_asyncpg}),
        ):
            result = await _pg_sessions_handler({})
            assert result.is_error


class TestRegisterPostgresTools:
    def test_registers_all_tools(self):
        mock_server = MagicMock()
        register_postgres_tools(mock_server)
        assert mock_server.register_tool.call_count == len(TFO_POSTGRES_TOOLS)

    def test_tool_names(self):
        names = [t["name"] for t in TFO_POSTGRES_TOOLS]
        assert "pg_query" in names
        assert "pg_list_tables" in names
        assert "pg_describe_table" in names
        assert "pg_sessions" in names
