"""TFO ClickHouse datasource tools for analytics queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tfo_mcp.domain.entities import ToolResult

if TYPE_CHECKING:
    from tfo_mcp.presentation.server import MCPServer


async def _ch_query_handler(input_data: dict[str, Any]) -> ToolResult:

    query = input_data.get("query")
    max_rows = input_data.get("max_rows", 100)
    read_only = input_data.get("read_only", True)

    if not query:
        return ToolResult.error("Query is required")

    query_stripped = query.strip().upper()
    if read_only and not query_stripped.startswith(
        ("SELECT", "WITH", "EXPLAIN", "SHOW", "DESCRIBE")
    ):
        return ToolResult.error("Only SELECT queries allowed in read-only mode")

    try:
        import clickhouse_connect

        from tfo_mcp.infrastructure.config import load_config

        config = load_config()
        ch_url = config.analytics.clickhouse_url

        url_parts = ch_url.replace("clickhouse://", "").split("/")
        host_port = url_parts[0]
        database = url_parts[1] if len(url_parts) > 1 else "tfo_mcp_analytics"

        host = host_port.split(":")[0]
        port = int(host_port.split(":")[1]) if ":" in host_port else 9000

        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            database=database,
        )

        result = client.query(query)
        columns = result.column_names
        rows = result.result_rows[:max_rows]

        results = [dict(zip(columns, row, strict=False)) for row in rows]
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
                "columns": list(columns),
                "total_rows": result.result_rows.__len__(),
                "truncated": len(result.result_rows) > max_rows,
            }
        )
    except ImportError:
        return ToolResult.error(
            "clickhouse-connect not installed. Run: pip install tfo-mcp[clickhouse]"
        )
    except Exception as e:
        return ToolResult.error(f"ClickHouse error: {e}")


async def _ch_tool_analytics_handler(input_data: dict[str, Any]) -> ToolResult:
    tool_name = input_data.get("tool_name")
    hours = input_data.get("hours", 24)
    limit = input_data.get("limit", 50)

    query = """
        SELECT
            tool_name,
            count() AS total_calls,
            sum(success) AS successes,
            count() - sum(success) AS failures,
            round(avg(duration_ms), 2) AS avg_duration_ms,
            round(max(duration_ms), 2) AS max_duration_ms,
            min(created_at) AS first_call,
            max(created_at) AS last_call
        FROM tool_calls
        WHERE created_at >= now() - INTERVAL {hours:UInt32} HOUR
    """

    params: dict[str, Any] = {"hours": hours}
    if tool_name:
        query += " AND tool_name = {tool_name:String}"
        params["tool_name"] = tool_name

    query += """
        GROUP BY tool_name
        ORDER BY total_calls DESC
        LIMIT {limit:UInt32}
    """
    params["limit"] = limit

    query_with_values = query
    for key, value in params.items():
        if isinstance(value, str):
            query_with_values = query_with_values.replace(f"{{{key}:String}}", f"'{value}'")
        elif isinstance(value, int):
            query_with_values = query_with_values.replace(f"{{{key}:UInt32}}", str(value))

    input_data_copy = {"query": query_with_values, "max_rows": limit, "read_only": True}
    return await _ch_query_handler(input_data_copy)


async def _ch_session_analytics_handler(input_data: dict[str, Any]) -> ToolResult:
    hours = input_data.get("hours", 168)
    limit = input_data.get("limit", 50)

    query = f"""
        SELECT
            session_id,
            client_name,
            duration_seconds,
            tool_calls_count,
            api_calls_count,
            total_input_tokens,
            total_output_tokens,
            errors_count,
            created_at,
            closed_at
        FROM session_analytics
        WHERE created_at >= now() - INTERVAL {int(hours)} HOUR
        ORDER BY created_at DESC
        LIMIT {int(limit)}
    """

    return await _ch_query_handler(
        {
            "query": query,
            "max_rows": limit,
            "read_only": True,
        }
    )


async def _ch_error_analytics_handler(input_data: dict[str, Any]) -> ToolResult:
    hours = input_data.get("hours", 72)
    limit = input_data.get("limit", 50)

    query = f"""
        SELECT
            error_type,
            error_code,
            count() AS error_count,
            any(error_message) AS sample_message,
            min(created_at) AS first_seen,
            max(created_at) AS last_seen
        FROM error_analytics
        WHERE created_at >= now() - INTERVAL {int(hours)} HOUR
        GROUP BY error_type, error_code
        ORDER BY error_count DESC
        LIMIT {int(limit)}
    """

    return await _ch_query_handler(
        {
            "query": query,
            "max_rows": limit,
            "read_only": True,
        }
    )


async def _ch_api_usage_handler(input_data: dict[str, Any]) -> ToolResult:
    hours = input_data.get("hours", 168)
    model = input_data.get("model")
    limit = input_data.get("limit", 50)

    model_filter = f" AND model = '{model}'" if model else ""

    query = f"""
        SELECT
            model,
            count() AS total_calls,
            sum(input_tokens) AS total_input_tokens,
            sum(output_tokens) AS total_output_tokens,
            sum(total_tokens) AS total_tokens,
            round(avg(duration_ms), 2) AS avg_duration_ms,
            sum(success) AS success_count,
            count() - sum(success) AS error_count
        FROM api_usage
        WHERE created_at >= now() - INTERVAL {int(hours)} HOUR
        {model_filter}
        GROUP BY model
        ORDER BY total_calls DESC
        LIMIT {int(limit)}
    """

    return await _ch_query_handler(
        {
            "query": query,
            "max_rows": limit,
            "read_only": True,
        }
    )


TFO_CLICKHOUSE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "ch_query",
        "description": "Execute a read-only SQL query against TFO ClickHouse analytics datasource",
        "category": "analytics",
        "tags": ["clickhouse", "sql", "analytics", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query (SELECT only in read-only mode)",
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
        "handler": _ch_query_handler,
    },
    {
        "name": "ch_tool_analytics",
        "description": "Get MCP tool call analytics from TFO ClickHouse (call counts, durations, success rates)",
        "category": "analytics",
        "tags": ["clickhouse", "analytics", "tools", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Filter by tool name (optional)",
                },
                "hours": {
                    "type": "integer",
                    "description": "Lookback window in hours (default: 24)",
                    "default": 24,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default: 50)",
                    "default": 50,
                },
            },
            "required": [],
        },
        "handler": _ch_tool_analytics_handler,
    },
    {
        "name": "ch_session_analytics",
        "description": "Get MCP session analytics from TFO ClickHouse (duration, token usage, tool/API call counts)",
        "category": "analytics",
        "tags": ["clickhouse", "analytics", "sessions", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "Lookback window in hours (default: 168 = 7 days)",
                    "default": 168,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default: 50)",
                    "default": 50,
                },
            },
            "required": [],
        },
        "handler": _ch_session_analytics_handler,
    },
    {
        "name": "ch_error_analytics",
        "description": "Get MCP error analytics from TFO ClickHouse (error types, counts, trends)",
        "category": "analytics",
        "tags": ["clickhouse", "analytics", "errors", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "Lookback window in hours (default: 72)",
                    "default": 72,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default: 50)",
                    "default": 50,
                },
            },
            "required": [],
        },
        "handler": _ch_error_analytics_handler,
    },
    {
        "name": "ch_api_usage",
        "description": "Get Claude API usage analytics from TFO ClickHouse (token counts, durations, model breakdown)",
        "category": "analytics",
        "tags": ["clickhouse", "analytics", "api", "tokens", "tfo"],
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "Lookback window in hours (default: 168 = 7 days)",
                    "default": 168,
                },
                "model": {
                    "type": "string",
                    "description": "Filter by model name (optional)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default: 50)",
                    "default": 50,
                },
            },
            "required": [],
        },
        "handler": _ch_api_usage_handler,
    },
]


def register_clickhouse_tools(server: MCPServer) -> None:
    """Register TFO ClickHouse datasource tools."""
    for tool_def in TFO_CLICKHOUSE_TOOLS:
        server.register_tool(
            name=tool_def["name"],
            description=tool_def["description"],
            input_schema=tool_def["input_schema"],
            handler=tool_def["handler"],
        )
