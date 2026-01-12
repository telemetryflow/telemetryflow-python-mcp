# TelemetryFlow Python MCP Server - Configuration Guide

This document describes all configuration options for the TelemetryFlow Python MCP Server.

## Configuration Sources

```mermaid
flowchart TB
    subgraph Priority["Configuration Priority"]
        direction TB
        E["1. Environment Variables<br/>(Highest Priority)"]
        F["2. Configuration File"]
        D["3. Default Values<br/>(Lowest Priority)"]
    end

    E --> Merge
    F --> Merge
    D --> Merge
    Merge["Merged Configuration"] --> App["Application"]
```

Configuration is loaded from multiple sources with the following priority (highest first):

1. **Environment Variables** - Prefix: `TELEMETRYFLOW_MCP_`
2. **Configuration File** - YAML format
3. **Default Values** - Built-in defaults

## Configuration File Locations

```mermaid
flowchart LR
    CLI["-c/--config option"] --> Load
    CWD["./tfo-mcp.yaml"] --> Load
    Configs["./configs/tfo-mcp.yaml"] --> Load
    Home["~/.config/tfo-mcp/config.yaml"] --> Load
    Etc["/etc/tfo-mcp/config.yaml"] --> Load
    Load["Load First Found"]
```

The server searches for configuration files in this order:

1. Path specified via `-c/--config` CLI option
2. `./tfo-mcp.yaml` (current directory)
3. `./configs/tfo-mcp.yaml`
4. `~/.config/tfo-mcp/config.yaml`
5. `/etc/tfo-mcp/config.yaml`

## Configuration Structure

```mermaid
classDiagram
    class Config {
        +ServerConfig server
        +ClaudeConfig claude
        +MCPConfig mcp
        +LoggingConfig logging
        +CacheConfig cache
        +QueueConfig queue
        +DatabaseConfig database
        +AnalyticsConfig analytics
        +TelemetryMCPConfig telemetry_mcp
        +TelemetryConfig telemetry
    }

    class ServerConfig {
        +str name
        +str version
        +str host
        +int port
        +str transport
        +bool debug
        +float read_timeout
        +float write_timeout
    }

    class ClaudeConfig {
        +str api_key
        +str default_model
        +int max_tokens
        +float temperature
        +float timeout
        +int max_retries
        +str base_url
    }

    class MCPConfig {
        +str protocol_version
        +bool enable_tools
        +bool enable_resources
        +bool enable_prompts
        +bool enable_logging
        +bool enable_sampling
        +float tool_timeout
        +int max_message_size
    }

    class LoggingConfig {
        +str level
        +str format
        +str output
    }

    class CacheConfig {
        +str redis_url
        +bool cache_enabled
        +int cache_ttl
    }

    class QueueConfig {
        +bool queue_enabled
        +int queue_concurrency
        +str nats_url
    }

    class DatabaseConfig {
        +str postgres_url
        +int postgres_max_conns
        +int postgres_min_conns
    }

    class AnalyticsConfig {
        +str clickhouse_url
    }

    class TelemetryMCPConfig {
        +bool enabled
        +str backend
        +str otlp_endpoint
        +str service_name
    }

    class TelemetryConfig {
        +bool enabled
        +str api_key
        +str api_key_id
        +str api_key_secret
        +str service_name
        +str endpoint
        +str protocol
    }

    Config --> ServerConfig
    Config --> ClaudeConfig
    Config --> MCPConfig
    Config --> LoggingConfig
    Config --> CacheConfig
    Config --> QueueConfig
    Config --> DatabaseConfig
    Config --> AnalyticsConfig
    Config --> TelemetryMCPConfig
    Config --> TelemetryConfig
```

---

## Environment Variables Summary

### Quick Reference

| Variable                                 | Description               | Default                   |
| ---------------------------------------- | ------------------------- | ------------------------- |
| `ANTHROPIC_API_KEY`                      | Claude API key (required) | -                         |
| `TELEMETRYFLOW_MCP_SERVER_TRANSPORT`     | Transport type            | stdio                     |
| `TELEMETRYFLOW_MCP_SERVER_PORT`          | Server port (SSE/WS)      | 8080                      |
| `TELEMETRYFLOW_MCP_LOG_LEVEL`            | Log level                 | info                      |
| `TELEMETRYFLOW_MCP_LOG_FORMAT`           | Log format                | json                      |
| `TELEMETRYFLOW_MCP_DEBUG`                | Debug mode                | false                     |
| `TELEMETRYFLOW_MCP_CLAUDE_DEFAULT_MODEL` | Default Claude model      | claude-sonnet-4-20250514  |
| `TELEMETRYFLOW_MCP_OTLP_ENDPOINT`        | OTEL collector endpoint   | localhost:4317            |
| `TELEMETRYFLOW_API_KEY`                  | TelemetryFlow API key     | -                         |
| `TELEMETRYFLOW_ENDPOINT`                 | TelemetryFlow endpoint    | api.telemetryflow.id:4317 |

---

## Server Configuration

```yaml
server:
  name: "TelemetryFlow-MCP" # Server name
  version: "1.1.2" # Server version
  host: "localhost" # Host (for future HTTP transports)
  port: 8080 # Port (for future HTTP transports)
  transport: "stdio" # Transport type: stdio, sse, websocket
  debug: false # Debug mode
  read_timeout: 300.0 # Read timeout in seconds
  write_timeout: 60.0 # Write timeout in seconds
```

| Option        | Environment Variable                     | Default           | Description       |
| ------------- | ---------------------------------------- | ----------------- | ----------------- |
| name          | `TELEMETRYFLOW_MCP_SERVER_NAME`          | TelemetryFlow-MCP | Server name       |
| version       | `TELEMETRYFLOW_MCP_SERVER_VERSION`       | 1.1.2             | Server version    |
| host          | `TELEMETRYFLOW_MCP_SERVER_HOST`          | localhost         | Server host       |
| port          | `TELEMETRYFLOW_MCP_SERVER_PORT`          | 8080              | Server port       |
| transport     | `TELEMETRYFLOW_MCP_SERVER_TRANSPORT`     | stdio             | Transport type    |
| debug         | `TELEMETRYFLOW_MCP_SERVER_DEBUG`         | false             | Debug mode        |
| read_timeout  | `TELEMETRYFLOW_MCP_SERVER_READ_TIMEOUT`  | 300.0             | Read timeout (s)  |
| write_timeout | `TELEMETRYFLOW_MCP_SERVER_WRITE_TIMEOUT` | 60.0              | Write timeout (s) |

---

## Claude Configuration

```yaml
claude:
  api_key: "" # Anthropic API key
  default_model: "claude-sonnet-4-20250514" # Default model
  max_tokens: 4096 # Max tokens per request
  temperature: 1.0 # Temperature (0.0-2.0)
  timeout: 120.0 # Request timeout in seconds
  max_retries: 3 # Max retry attempts
  base_url: null # Custom base URL (optional)
```

| Option        | Environment Variable                     | Default                  | Description                  |
| ------------- | ---------------------------------------- | ------------------------ | ---------------------------- |
| api_key       | `ANTHROPIC_API_KEY`                      | -                        | Anthropic API key (required) |
| api_key       | `TELEMETRYFLOW_MCP_CLAUDE_API_KEY`       | -                        | Alternative API key env var  |
| default_model | `TELEMETRYFLOW_MCP_CLAUDE_DEFAULT_MODEL` | claude-sonnet-4-20250514 | Default Claude model         |
| max_tokens    | `TELEMETRYFLOW_MCP_CLAUDE_MAX_TOKENS`    | 4096                     | Maximum tokens               |
| temperature   | `TELEMETRYFLOW_MCP_CLAUDE_TEMPERATURE`   | 1.0                      | Temperature                  |
| timeout       | `TELEMETRYFLOW_MCP_CLAUDE_TIMEOUT`       | 120.0                    | Timeout (seconds)            |
| max_retries   | `TELEMETRYFLOW_MCP_CLAUDE_MAX_RETRIES`   | 3                        | Max retries                  |
| base_url      | `TELEMETRYFLOW_MCP_CLAUDE_BASE_URL`      | null                     | Custom base URL              |

### Available Models

```mermaid
graph LR
    subgraph Claude4["Claude 4"]
        Opus["claude-opus-4-20250514<br/>Most Capable"]
        Sonnet4["claude-sonnet-4-20250514<br/>Balanced"]
    end

    subgraph Claude35["Claude 3.5"]
        Sonnet35["claude-3-5-sonnet-20241022"]
        Haiku35["claude-3-5-haiku-20241022<br/>Fast"]
    end

    Opus -.->|"More capable"| Sonnet4
    Sonnet4 -.->|"More capable"| Sonnet35
    Sonnet35 -.->|"More capable"| Haiku35
```

| Model ID                   | Description                  |
| -------------------------- | ---------------------------- |
| claude-opus-4-20250514     | Claude 4 Opus - Most capable |
| claude-sonnet-4-20250514   | Claude 4 Sonnet - Balanced   |
| claude-3-5-sonnet-20241022 | Claude 3.5 Sonnet            |
| claude-3-5-haiku-20241022  | Claude 3.5 Haiku - Fast      |

---

## MCP Configuration

```yaml
mcp:
  protocol_version: "2024-11-05" # MCP protocol version
  enable_tools: true # Enable tools capability
  enable_resources: true # Enable resources capability
  enable_prompts: true # Enable prompts capability
  enable_logging: true # Enable logging capability
  enable_sampling: false # Enable sampling capability
  tool_timeout: 30.0 # Tool execution timeout (seconds)
  max_message_size: 10485760 # Max message size (10MB)
```

| Option           | Environment Variable                     | Default    | Description      |
| ---------------- | ---------------------------------------- | ---------- | ---------------- |
| protocol_version | `TELEMETRYFLOW_MCP_MCP_PROTOCOL_VERSION` | 2024-11-05 | Protocol version |
| enable_tools     | `TELEMETRYFLOW_MCP_ENABLE_TOOLS`         | true       | Enable tools     |
| enable_resources | `TELEMETRYFLOW_MCP_ENABLE_RESOURCES`     | true       | Enable resources |
| enable_prompts   | `TELEMETRYFLOW_MCP_ENABLE_PROMPTS`       | true       | Enable prompts   |
| enable_logging   | `TELEMETRYFLOW_MCP_MCP_ENABLE_LOGGING`   | true       | Enable logging   |
| enable_sampling  | `TELEMETRYFLOW_MCP_MCP_ENABLE_SAMPLING`  | false      | Enable sampling  |
| tool_timeout     | `TELEMETRYFLOW_MCP_MCP_TOOL_TIMEOUT`     | 30.0       | Tool timeout (s) |
| max_message_size | `TELEMETRYFLOW_MCP_MCP_MAX_MESSAGE_SIZE` | 10485760   | Max message size |

---

## Logging Configuration

```yaml
logging:
  level: "info" # Log level
  format: "json" # Log format
  output: "stderr" # Log output
```

| Option | Environment Variable           | Default | Description |
| ------ | ------------------------------ | ------- | ----------- |
| level  | `TELEMETRYFLOW_MCP_LOG_LEVEL`  | info    | Log level   |
| format | `TELEMETRYFLOW_MCP_LOG_FORMAT` | json    | Log format  |
| output | `TELEMETRYFLOW_MCP_LOG_OUTPUT` | stderr  | Log output  |

### Log Levels

```mermaid
graph LR
    DEBUG["debug"] --> INFO["info"] --> WARNING["warning"] --> ERROR["error"]

    style DEBUG fill:#e3f2fd
    style INFO fill:#e8f5e9
    style WARNING fill:#fff3e0
    style ERROR fill:#ffebee
```

- `debug` - Detailed debugging information
- `info` - General operational information
- `warning` - Warning messages
- `error` - Error messages only

### Log Formats

- `json` - Structured JSON logs (recommended for production)
- `text` - Human-readable console output (recommended for development)

### Log Output

- `stderr` - Standard error (default)
- `stdout` - Standard output
- `/path/to/file.log` - File path

---

## Cache Configuration (Redis)

```yaml
cache:
  redis_url: "redis://localhost:6379" # Redis connection URL
  cache_enabled: true # Enable caching
  cache_ttl: 300 # Cache TTL in seconds
```

| Option        | Environment Variable              | Default                | Description    |
| ------------- | --------------------------------- | ---------------------- | -------------- |
| redis_url     | `TELEMETRYFLOW_MCP_REDIS_URL`     | redis://localhost:6379 | Redis URL      |
| cache_enabled | `TELEMETRYFLOW_MCP_CACHE_ENABLED` | true                   | Enable caching |
| cache_ttl     | `TELEMETRYFLOW_MCP_CACHE_TTL`     | 300                    | TTL (seconds)  |

---

## Queue Configuration (NATS)

```yaml
queue:
  queue_enabled: true # Enable queue processing
  queue_concurrency: 5 # Queue concurrency
  nats_url: "nats://localhost:4222" # NATS connection URL
```

| Option            | Environment Variable                  | Default               | Description  |
| ----------------- | ------------------------------------- | --------------------- | ------------ |
| queue_enabled     | `TELEMETRYFLOW_MCP_QUEUE_ENABLED`     | true                  | Enable queue |
| queue_concurrency | `TELEMETRYFLOW_MCP_QUEUE_CONCURRENCY` | 5                     | Concurrency  |
| nats_url          | `TELEMETRYFLOW_MCP_NATS_URL`          | nats://localhost:4222 | NATS URL     |

---

## Database Configuration (PostgreSQL)

```yaml
database:
  postgres_url: "postgres://telemetryflow:telemetryflow@localhost:5432/tfo_mcp?sslmode=disable"
  postgres_max_conns: 25 # Maximum connections
  postgres_min_conns: 5 # Minimum connections
```

| Option             | Environment Variable                   | Default                          | Description     |
| ------------------ | -------------------------------------- | -------------------------------- | --------------- |
| postgres_url       | `TELEMETRYFLOW_MCP_POSTGRES_URL`       | postgres://...localhost:5432/... | PostgreSQL URL  |
| postgres_max_conns | `TELEMETRYFLOW_MCP_POSTGRES_MAX_CONNS` | 25                               | Max connections |
| postgres_min_conns | `TELEMETRYFLOW_MCP_POSTGRES_MIN_CONNS` | 5                                | Min connections |

---

## Analytics Configuration (ClickHouse)

```yaml
analytics:
  clickhouse_url: "clickhouse://localhost:9000/tfo_mcp_analytics"
```

| Option         | Environment Variable               | Default                                       | Description    |
| -------------- | ---------------------------------- | --------------------------------------------- | -------------- |
| clickhouse_url | `TELEMETRYFLOW_MCP_CLICKHOUSE_URL` | clickhouse://localhost:9000/tfo_mcp_analytics | ClickHouse URL |

---

## MCP Telemetry Configuration

This section controls MCP-level telemetry settings.

```yaml
telemetry_mcp:
  enabled: true # Enable telemetry
  backend: "telemetryflow" # Backend: telemetryflow, otel
  otlp_endpoint: "localhost:4317" # OTLP endpoint
  service_name: "telemetryflow-python-mcp" # Service name
```

| Option        | Environment Variable                  | Default                  | Description       |
| ------------- | ------------------------------------- | ------------------------ | ----------------- |
| enabled       | `TELEMETRYFLOW_MCP_TELEMETRY_ENABLED` | true                     | Enable telemetry  |
| backend       | `TELEMETRYFLOW_MCP_TELEMETRY_BACKEND` | telemetryflow            | Telemetry backend |
| otlp_endpoint | `TELEMETRYFLOW_MCP_OTLP_ENDPOINT`     | localhost:4317           | OTLP endpoint     |
| service_name  | `TELEMETRYFLOW_MCP_SERVICE_NAME`      | telemetryflow-python-mcp | Service name      |

---

## TelemetryFlow SDK Configuration

This section configures the TelemetryFlow Python SDK for observability.

```yaml
telemetry:
  enabled: false # Enable TelemetryFlow SDK
  service_name: "telemetryflow-python-mcp" # Service name
  service_version: "1.1.2" # Service version
  service_namespace: "telemetryflow" # Service namespace
  environment: "development" # Environment

  # API credentials - supports both formats
  api_key: "" # Single key (Go SDK compatibility)
  api_key_id: "" # Key ID (tfk_*)
  api_key_secret: "" # Key secret (tfs_*)

  # Connection settings
  endpoint: "api.telemetryflow.id:4317" # TelemetryFlow endpoint
  protocol: "grpc" # Protocol: grpc, http
  insecure: false # Use insecure connection
  timeout: 30.0 # Timeout (seconds)
  compression: true # Enable compression

  # Signal configuration
  enable_traces: true # Enable traces
  enable_metrics: true # Enable metrics
  enable_logs: true # Enable logs
  enable_exemplars: true # Enable exemplars

  # Batch settings
  batch_timeout_ms: 5000 # Batch timeout (ms)
  batch_max_size: 512 # Max batch size

  # Retry settings
  retry_enabled: true # Enable retry
  max_retries: 3 # Max retries
  retry_backoff_ms: 500 # Retry backoff (ms)

  # Rate limiting
  rate_limit: 1000 # Rate limit (req/min)
```

### Core Settings

| Option            | Environment Variable              | Default                  | Description       |
| ----------------- | --------------------------------- | ------------------------ | ----------------- |
| enabled           | `TELEMETRYFLOW_ENABLED`           | false                    | Enable SDK        |
| service_name      | `TELEMETRYFLOW_SERVICE_NAME`      | telemetryflow-python-mcp | Service name      |
| service_version   | `TELEMETRYFLOW_SERVICE_VERSION`   | 1.1.2                    | Service version   |
| service_namespace | `TELEMETRYFLOW_SERVICE_NAMESPACE` | telemetryflow            | Service namespace |
| environment       | `TELEMETRYFLOW_ENVIRONMENT`       | production               | Environment       |

### API Credentials

| Option         | Environment Variable           | Default | Description                |
| -------------- | ------------------------------ | ------- | -------------------------- |
| api_key        | `TELEMETRYFLOW_API_KEY`        | -       | Single API key (Go compat) |
| api_key_id     | `TELEMETRYFLOW_API_KEY_ID`     | -       | API key ID (tfk\_\*)       |
| api_key_secret | `TELEMETRYFLOW_API_KEY_SECRET` | -       | API key secret (tfs\_\*)   |

### Connection Settings

| Option      | Environment Variable        | Default                   | Description   |
| ----------- | --------------------------- | ------------------------- | ------------- |
| endpoint    | `TELEMETRYFLOW_ENDPOINT`    | api.telemetryflow.id:4317 | Endpoint      |
| protocol    | `TELEMETRYFLOW_PROTOCOL`    | grpc                      | Protocol      |
| insecure    | `TELEMETRYFLOW_INSECURE`    | false                     | Insecure mode |
| timeout     | `TELEMETRYFLOW_TIMEOUT`     | 30.0                      | Timeout (s)   |
| compression | `TELEMETRYFLOW_COMPRESSION` | true                      | Compression   |

### Signal Configuration

| Option           | Environment Variable             | Default | Description      |
| ---------------- | -------------------------------- | ------- | ---------------- |
| enable_traces    | `TELEMETRYFLOW_ENABLE_TRACES`    | true    | Enable traces    |
| enable_metrics   | `TELEMETRYFLOW_ENABLE_METRICS`   | true    | Enable metrics   |
| enable_logs      | `TELEMETRYFLOW_ENABLE_LOGS`      | true    | Enable logs      |
| enable_exemplars | `TELEMETRYFLOW_ENABLE_EXEMPLARS` | true    | Enable exemplars |

### Batch & Retry Settings

| Option           | Environment Variable             | Default | Description        |
| ---------------- | -------------------------------- | ------- | ------------------ |
| batch_timeout_ms | `TELEMETRYFLOW_BATCH_TIMEOUT_MS` | 5000    | Batch timeout (ms) |
| batch_max_size   | `TELEMETRYFLOW_BATCH_MAX_SIZE`   | 512     | Max batch size     |
| retry_enabled    | `TELEMETRYFLOW_RETRY_ENABLED`    | true    | Enable retry       |
| max_retries      | `TELEMETRYFLOW_MAX_RETRIES`      | 3       | Max retries        |
| retry_backoff_ms | `TELEMETRYFLOW_RETRY_BACKOFF_MS` | 500     | Retry backoff (ms) |
| rate_limit       | `TELEMETRYFLOW_RATE_LIMIT`       | 1000    | Rate limit         |

---

## Example Configurations

### Development

```yaml
server:
  name: "TelemetryFlow-MCP-Dev"
  debug: true

claude:
  default_model: "claude-3-5-haiku-20241022"
  max_tokens: 2048

logging:
  level: "debug"
  format: "text"

telemetry_mcp:
  enabled: false
```

### Production

```yaml
server:
  name: "TelemetryFlow-MCP"
  debug: false

claude:
  default_model: "claude-sonnet-4-20250514"
  max_tokens: 4096
  max_retries: 5

mcp:
  tool_timeout: 60.0

logging:
  level: "info"
  format: "json"

cache:
  redis_url: "redis://redis:6379"
  cache_enabled: true
  cache_ttl: 600

database:
  postgres_url: "postgres://telemetryflow:password@postgres:5432/tfo_mcp"
  postgres_max_conns: 50

telemetry_mcp:
  enabled: true
  backend: "telemetryflow"

telemetry:
  enabled: true
  api_key: "your-telemetryflow-api-key"
  endpoint: "api.telemetryflow.id:4317"
  environment: "production"
```

### Full Stack (Docker Compose)

```yaml
server:
  host: "0.0.0.0"
  port: 8080

cache:
  redis_url: "redis://redis:6379"

queue:
  nats_url: "nats://nats:4222"

database:
  postgres_url: "postgres://telemetryflow:telemetryflow@postgres:5432/tfo_mcp"

analytics:
  clickhouse_url: "clickhouse://clickhouse:9000/tfo_mcp_analytics"

telemetry_mcp:
  enabled: true
  otlp_endpoint: "otel-collector:4317"
```

### Minimal (Environment Variables Only)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export TELEMETRYFLOW_MCP_LOG_LEVEL="info"
export TELEMETRYFLOW_API_KEY="your-api-key"
tfo-mcp serve
```

---

## Validation

Validate your configuration:

```bash
tfo-mcp validate -c /path/to/config.yaml
```

## Generate Default Configuration

Generate a default configuration file:

```bash
tfo-mcp init-config
```

This creates `tfo-mcp.yaml` in the current directory.

---

## Related Documentation

- [Installation Guide](INSTALLATION.md)
- [Commands Reference](COMMANDS.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
