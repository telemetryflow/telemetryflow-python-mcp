"""TFO PostgreSQL datasource tools for querying telemetry data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tfo_mcp.domain.entities import ToolResult

if TYPE_CHECKING:
    from tfo_mcp.presentation.server import MCPServer


async def _pg_query_handler(input_data: dict[str, Any]) -> ToolResult:

    from tfo_mcp.infrastructure.config import load_config

    config = load_config()
    dsn = config.database.postgres_url

    query = input_data.get("query")
    params = input_data.get("params", [])
    max_rows = input_data.get("max_rows", 100)
    read_only = input_data.get("read_only", True)

    if not query:
        return ToolResult.error("Query is required")

    query_stripped = query.strip().upper()
    if read_only and not query_stripped.startswith(("SELECT", "WITH", "EXPLAIN", "SHOW")):
        return ToolResult.error("Only SELECT queries allowed in read-only mode")

    try:
        import asyncpg

        conn = await asyncpg.connect(dsn)
        try:
            rows = await conn.fetch(query, *params)
            results = [dict(row) for row in rows[:max_rows]]
            for row in results:
                for key, value in row.items():
                    if hasattr(value, "isoformat"):
                        row[key] = value.isoformat()
                    elif isinstance(value, (bytes, bytearray)):
                        row[key] = value.decode("utf-8", errors="replace")
            return ToolResult.json(
                {
                    "rows": results,
                    "count": len(results),
                    "truncated": len(rows) > max_rows,
                }
            )
        finally:
            await conn.close()
    except ImportError:
        return ToolResult.error("asyncpg not installed. Run: pip install tfo-mcp[postgres]")
    except Exception as e:
        return ToolResult.error(f"PostgreSQL error: {e}")


async def _pg_list_tables_handler(input_data: dict[str, Any]) -> ToolResult:

    from tfo_mcp.infrastructure.config import load_config

    config = load_config()
    dsn = config.database.postgres_url

    schema = input_data.get("schema", "public")

    try:
        import asyncpg

        conn = await asyncpg.connect(dsn)
        try:
            rows = await conn.fetch(
                """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = $1
                ORDER BY table_name
                """,
                schema,
            )
            tables = [{"name": r["table_name"], "type": r["table_type"]} for r in rows]
            return ToolResult.json({"schema": schema, "tables": tables, "count": len(tables)})
        finally:
            await conn.close()
    except ImportError:
        return ToolResult.error("asyncpg not installed. Run: pip install tfo-mcp[postgres]")
    except Exception as e:
        return ToolResult.error(f"PostgreSQL error: {e}")


async def _pg_describe_table_handler(input_data: dict[str, Any]) -> ToolResult:
    from tfo_mcp.infrastructure.config import load_config

    config = load_config()
    dsn = config.database.postgres_url

    table_name = input_data.get("table")
    schema = input_data.get("schema", "public")

    if not table_name:
        return ToolResult.error("Table name is required")

    try:
        import asyncpg

        conn = await asyncpg.connect(dsn)
        try:
            columns = await conn.fetch(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
                """,
                schema,
                table_name,
            )
            indexes = await conn.fetch(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = $1 AND tablename = $2
                """,
                schema,
                table_name,
            )
            result = {
                "table": table_name,
                "schema": schema,
                "columns": [dict(c) for c in columns],
                "indexes": [{"name": i["indexname"], "definition": i["indexdef"]} for i in indexes],
            }
            return ToolResult.json(result)
        finally:
            await conn.close()
    except ImportError:
        return ToolResult.error("asyncpg not installed. Run: pip install tfo-mcp[postgres]")
    except Exception as e:
        return ToolResult.error(f"PostgreSQL error: {e}")


async def _pg_sessions_handler(input_data: dict[str, Any]) -> ToolResult:
    from tfo_mcp.infrastructure.config import load_config

    config = load_config()
    dsn = config.database.postgres_url

    limit = input_data.get("limit", 20)
    state = input_data.get("state")

    try:
        import asyncpg

        conn = await asyncpg.connect(dsn)
        try:
            if state:
                rows = await conn.fetch(
                    """
                    SELECT id, state, client_name, server_name, created_at, initialized_at, closed_at
                    FROM sessions WHERE state = $1
                    ORDER BY created_at DESC LIMIT $2
                    """,
                    state,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, state, client_name, server_name, created_at, initialized_at, closed_at
                    FROM sessions
                    ORDER BY created_at DESC LIMIT $1
                    """,
                    limit,
                )
            results = []
            for r in rows:
                row_dict = dict(r)
                for key, value in row_dict.items():
                    if hasattr(value, "isoformat"):
                        row_dict[key] = value.isoformat()
                    elif isinstance(value, bytes):
                        row_dict[key] = str(value)
                results.append(row_dict)
            return ToolResult.json({"sessions": results, "count": len(results)})
        finally:
            await conn.close()
    except ImportError:
        return ToolResult.error("asyncpg not installed. Run: pip install tfo-mcp[postgres]")
    except Exception as e:
        return ToolResult.error(f"PostgreSQL error: {e}")


TFO_POSTGRES_TOOLS: list[dict[str, Any]] = [
    {
        "name": "pg_query",
        "description": "Execute a read-only SQL query against TFO PostgreSQL datasource (sessions, conversations, tools, events)",
        "category": "datasource",
        "tags": ["postgresql", "sql", "query", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query (SELECT only in read-only mode)",
                },
                "params": {
                    "type": "array",
                    "description": "Query parameters",
                    "default": [],
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows to return (default: 100)",
                    "default": 100,
                },
                "read_only": {
                    "type": "boolean",
                    "description": "Enforce read-only mode (default: true)",
                    "default": True,
                },
            },
            "required": ["query"],
        },
        "handler": _pg_query_handler,
    },
    {
        "name": "pg_list_tables",
        "description": "List tables in TFO PostgreSQL datasource",
        "category": "datasource",
        "tags": ["postgresql", "metadata", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "schema": {
                    "type": "string",
                    "description": "Schema name (default: public)",
                    "default": "public",
                },
            },
            "required": [],
        },
        "handler": _pg_list_tables_handler,
    },
    {
        "name": "pg_describe_table",
        "description": "Describe a table schema in TFO PostgreSQL datasource",
        "category": "datasource",
        "tags": ["postgresql", "metadata", "schema", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "description": "Table name",
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name (default: public)",
                    "default": "public",
                },
            },
            "required": ["table"],
        },
        "handler": _pg_describe_table_handler,
    },
    {
        "name": "pg_sessions",
        "description": "Query MCP session history from TFO PostgreSQL datasource",
        "category": "datasource",
        "tags": ["postgresql", "sessions", "history", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum sessions to return (default: 20)",
                    "default": 20,
                },
                "state": {
                    "type": "string",
                    "description": "Filter by session state (created, initializing, ready, closing, closed)",
                },
            },
            "required": [],
        },
        "handler": _pg_sessions_handler,
    },
]


def register_postgres_tools(server: MCPServer) -> None:
    """Register TFO PostgreSQL datasource tools."""
    for tool_def in TFO_POSTGRES_TOOLS:
        server.register_tool(
            name=tool_def["name"],
            description=tool_def["description"],
            input_schema=tool_def["input_schema"],
            handler=tool_def["handler"],
        )
