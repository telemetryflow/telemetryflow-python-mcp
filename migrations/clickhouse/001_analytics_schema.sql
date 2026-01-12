-- TelemetryFlow Python MCP Server - ClickHouse Analytics Schema
-- Initial migration: Analytics tables for metrics and observability

-- ============================================
-- Tool Calls Analytics
-- ============================================
CREATE TABLE IF NOT EXISTS tool_calls (
    id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    tool_name String,
    category String DEFAULT 'general',
    success UInt8 DEFAULT 1,
    duration_ms Float64 DEFAULT 0,
    error_message Nullable(String),
    input_size UInt32 DEFAULT 0,
    output_size UInt32 DEFAULT 0,
    metadata String DEFAULT '{}',
    created_at DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (session_id, tool_name, created_at)
TTL created_at + INTERVAL 90 DAY;

-- ============================================
-- API Usage Analytics
-- ============================================
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    conversation_id Nullable(UUID),
    model String,
    input_tokens UInt32 DEFAULT 0,
    output_tokens UInt32 DEFAULT 0,
    total_tokens UInt32 DEFAULT 0,
    duration_ms Float64 DEFAULT 0,
    success UInt8 DEFAULT 1,
    error_code Nullable(Int32),
    error_message Nullable(String),
    metadata String DEFAULT '{}',
    created_at DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (session_id, model, created_at)
TTL created_at + INTERVAL 90 DAY;

-- ============================================
-- Session Analytics
-- ============================================
CREATE TABLE IF NOT EXISTS session_analytics (
    id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    client_name String,
    client_version String,
    protocol_version String DEFAULT '2024-11-05',
    duration_seconds Float64 DEFAULT 0,
    tool_calls_count UInt32 DEFAULT 0,
    api_calls_count UInt32 DEFAULT 0,
    total_input_tokens UInt32 DEFAULT 0,
    total_output_tokens UInt32 DEFAULT 0,
    errors_count UInt32 DEFAULT 0,
    metadata String DEFAULT '{}',
    created_at DateTime64(3) DEFAULT now64(3),
    closed_at Nullable(DateTime64(3))
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (session_id, created_at)
TTL created_at + INTERVAL 365 DAY;

-- ============================================
-- Error Analytics
-- ============================================
CREATE TABLE IF NOT EXISTS error_analytics (
    id UUID DEFAULT generateUUIDv4(),
    session_id Nullable(UUID),
    error_type String,
    error_code Int32,
    error_message String,
    stack_trace Nullable(String),
    context String DEFAULT '{}',
    created_at DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (error_type, created_at)
TTL created_at + INTERVAL 90 DAY;

-- ============================================
-- Resource Access Analytics
-- ============================================
CREATE TABLE IF NOT EXISTS resource_access (
    id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    resource_uri String,
    resource_name String,
    mime_type String DEFAULT 'text/plain',
    success UInt8 DEFAULT 1,
    duration_ms Float64 DEFAULT 0,
    response_size UInt32 DEFAULT 0,
    error_message Nullable(String),
    created_at DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (session_id, resource_uri, created_at)
TTL created_at + INTERVAL 90 DAY;

-- ============================================
-- Prompt Usage Analytics
-- ============================================
CREATE TABLE IF NOT EXISTS prompt_usage (
    id UUID DEFAULT generateUUIDv4(),
    session_id UUID,
    prompt_name String,
    arguments_count UInt8 DEFAULT 0,
    success UInt8 DEFAULT 1,
    duration_ms Float64 DEFAULT 0,
    error_message Nullable(String),
    created_at DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (session_id, prompt_name, created_at)
TTL created_at + INTERVAL 90 DAY;

-- ============================================
-- Materialized Views for Aggregations
-- ============================================

-- Hourly tool call statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS tool_calls_hourly_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, tool_name)
AS SELECT
    toStartOfHour(created_at) AS hour,
    tool_name,
    count() AS call_count,
    sum(success) AS success_count,
    count() - sum(success) AS error_count,
    avg(duration_ms) AS avg_duration_ms,
    max(duration_ms) AS max_duration_ms
FROM tool_calls
GROUP BY hour, tool_name;

-- Daily API usage statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS api_usage_daily_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, model)
AS SELECT
    toStartOfDay(created_at) AS day,
    model,
    count() AS call_count,
    sum(input_tokens) AS total_input_tokens,
    sum(output_tokens) AS total_output_tokens,
    sum(total_tokens) AS total_tokens,
    avg(duration_ms) AS avg_duration_ms,
    sum(success) AS success_count
FROM api_usage
GROUP BY day, model;

-- Daily error summary
CREATE MATERIALIZED VIEW IF NOT EXISTS errors_daily_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, error_type, error_code)
AS SELECT
    toStartOfDay(created_at) AS day,
    error_type,
    error_code,
    count() AS error_count
FROM error_analytics
GROUP BY day, error_type, error_code;
