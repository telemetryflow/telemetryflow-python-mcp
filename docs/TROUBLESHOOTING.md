# TelemetryFlow Python MCP Server - Troubleshooting Guide

This guide helps diagnose and resolve common issues with the TelemetryFlow Python MCP Server.

## Issue Resolution Flowchart

```mermaid
flowchart TB
    Start["Issue Detected"] --> Category{"Issue Category?"}

    Category -->|"Startup"| Startup["Server Won't Start"]
    Category -->|"Connection"| Connection["Connection Issues"]
    Category -->|"Tools"| Tools["Tool Execution"]
    Category -->|"API"| API["Claude API"]
    Category -->|"Config"| Config["Configuration"]

    Startup --> S1{"Module Error?"}
    S1 -->|"Yes"| S1Fix["pip install -e ."]
    S1 -->|"No"| S2{"API Key Error?"}
    S2 -->|"Yes"| S2Fix["Set ANTHROPIC_API_KEY"]
    S2 -->|"No"| S3["Check Permissions"]

    Connection --> C1{"Session Error?"}
    C1 -->|"Yes"| C1Fix["Send initialize first"]
    C1 -->|"No"| C2["Check Transport"]

    Tools --> T1{"Tool Not Found?"}
    T1 -->|"Yes"| T1Fix["Check tool name"]
    T1 -->|"No"| T2{"Timeout?"}
    T2 -->|"Yes"| T2Fix["Increase timeout"]
    T2 -->|"No"| T3["Check Permissions"]

    API --> A1{"Rate Limited?"}
    A1 -->|"Yes"| A1Fix["Wait/Retry"]
    A1 -->|"No"| A2{"Invalid Key?"}
    A2 -->|"Yes"| A2Fix["Check API Key"]
    A2 -->|"No"| A3["Check Model ID"]

    Config --> CF1{"File Not Found?"}
    CF1 -->|"Yes"| CF1Fix["tfo-mcp init-config"]
    CF1 -->|"No"| CF2["Validate YAML"]
```

## Common Issues

### Server Won't Start

#### Issue: "ModuleNotFoundError: No module named 'tfo_mcp'"

**Cause**: Package not installed properly.

**Solution**:

```bash
pip install -e .
```

#### Issue: "ANTHROPIC_API_KEY not set"

**Cause**: Claude API key not configured.

**Solution**:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# or add to config file:
# claude:
#   api_key: "sk-ant-..."
```

#### Issue: "Permission denied" on startup

**Cause**: File permissions issue.

**Solution**:

```bash
chmod +x $(which tfo-mcp)
```

### Connection Issues

#### Issue: Client can't connect

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: Connect (stdin)
    Server--xClient: No Response

    Note over Client,Server: Check: Is server running?
    Note over Client,Server: Check: Transport matches?
    Note over Client,Server: Check: Error in logs?
```

**Cause**: Transport mismatch or server not running.

**Solution**:

1. Ensure server is running: `tfo-mcp serve`
2. Check transport matches client expectation (stdio)
3. Check logs for errors

#### Issue: "Session not initialized" error

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: tools/list
    Server-->>Client: Error: Session not initialized

    Note over Client,Server: Must send initialize first!

    Client->>Server: initialize
    Server-->>Client: OK
    Client->>Server: tools/list
    Server-->>Client: Tools List
```

**Cause**: Client didn't send `initialize` request first.

**Solution**: Client must send `initialize` request before other operations:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": { "name": "client", "version": "1.0" }
  }
}
```

### Tool Execution Issues

#### Issue: "Tool not found: <name>"

**Cause**: Tool not registered or typo in name.

**Solution**:

1. List available tools: `tools/list`
2. Check tool name spelling (lowercase, underscores)
3. Verify tool is enabled

#### Issue: "Tool execution timed out"

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Tool

    Client->>Server: tools/call (execute_command)
    Server->>Tool: Execute
    Note over Tool: Long running...
    Tool--xServer: Timeout!
    Server-->>Client: Error: Timeout
```

**Cause**: Tool took longer than configured timeout.

**Solution**:

1. Increase tool timeout in config:
   ```yaml
   mcp:
     tool_timeout: 60.0
   ```
2. Or pass longer timeout in execute_command:
   ```json
   { "command": "long_command", "timeout": 120 }
   ```

#### Issue: "Permission denied" in file operations

**Cause**: Server doesn't have access to the file/directory.

**Solution**:

1. Check file permissions
2. Run server with appropriate user
3. Use absolute paths

### Claude API Issues

#### Issue: "Rate limit exceeded"

```mermaid
flowchart LR
    Request["Request"] --> API["Claude API"]
    API -->|"429"| RateLimit["Rate Limited"]
    RateLimit --> Wait["Wait"]
    Wait --> Retry["Retry"]
    Retry --> API
```

**Cause**: Too many API requests.

**Solution**:

1. Reduce request frequency
2. Implement client-side rate limiting
3. Increase retry settings:
   ```yaml
   claude:
     max_retries: 5
   ```

#### Issue: "Invalid API key"

**Cause**: API key is incorrect or expired.

**Solution**:

1. Verify API key at https://console.anthropic.com
2. Check for extra spaces or characters
3. Ensure key has correct permissions

#### Issue: "Model not found"

**Cause**: Invalid model ID specified.

**Solution**: Use a valid model ID:

- `claude-opus-4-20250514`
- `claude-sonnet-4-20250514`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

### Configuration Issues

#### Issue: "Configuration file not found"

**Cause**: Config file doesn't exist at expected location.

**Solution**:

1. Generate default config: `tfo-mcp init-config`
2. Or specify path: `tfo-mcp serve -c /path/to/config.yaml`

#### Issue: "Invalid configuration"

**Cause**: YAML syntax error or invalid values.

**Solution**:

1. Validate config: `tfo-mcp validate -c config.yaml`
2. Check YAML syntax
3. Review error message for specific field

### Logging Issues

#### Issue: "No logs appearing"

**Cause**: Log level too high or output misconfigured.

**Solution**:

1. Lower log level:
   ```yaml
   logging:
     level: "debug"
   ```
2. Check output destination:
   ```yaml
   logging:
     output: "stderr" # or "stdout" or file path
   ```

#### Issue: "Logs not in JSON format"

**Cause**: Format set to text.

**Solution**:

```yaml
logging:
  format: "json"
```

## Debugging

### Debug Flow

```mermaid
flowchart TB
    Enable["Enable Debug Mode"] --> Logs["Check Logs"]
    Logs --> Messages["View Raw Messages"]
    Messages --> Test["Test Individual Components"]
    Test --> Identify["Identify Issue"]
    Identify --> Fix["Apply Fix"]
```

### Enable Debug Mode

```bash
# Via CLI
tfo-mcp serve --debug

# Via environment
TELEMETRYFLOW_MCP_SERVER_DEBUG=true tfo-mcp serve

# Via config
server:
  debug: true
logging:
  level: "debug"
```

### View Raw Messages

Run server with debug logging to see JSON-RPC messages:

```bash
TELEMETRYFLOW_MCP_LOG_LEVEL=debug tfo-mcp serve 2>debug.log
```

### Test Individual Tools

```python
import asyncio
from tfo_mcp.presentation.tools.builtin_tools import _read_file_handler

async def test():
    result = await _read_file_handler({"path": "/tmp/test.txt"})
    print(result)

asyncio.run(test())
```

### Check Server Status

Send a ping request:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "ping", "params": {} }
```

Expected response:

```json
{ "jsonrpc": "2.0", "id": 1, "result": {} }
```

## Error Codes

```mermaid
graph TB
    subgraph JSONRPC["JSON-RPC Errors"]
        E32700["-32700<br/>Parse Error"]
        E32600["-32600<br/>Invalid Request"]
        E32601["-32601<br/>Method Not Found"]
        E32602["-32602<br/>Invalid Params"]
        E32603["-32603<br/>Internal Error"]
    end

    subgraph MCP["MCP Errors"]
        E32001["-32001<br/>Tool Not Found"]
        E32002["-32002<br/>Resource Not Found"]
        E32003["-32003<br/>Prompt Not Found"]
        E32004["-32004<br/>Tool Execution Error"]
        E32008["-32008<br/>Session Not Initialized"]
    end
```

| Code   | Name                    | Description                       |
| ------ | ----------------------- | --------------------------------- |
| -32700 | Parse error             | Invalid JSON received             |
| -32600 | Invalid Request         | Not a valid JSON-RPC request      |
| -32601 | Method not found        | Method does not exist             |
| -32602 | Invalid params          | Invalid method parameters         |
| -32603 | Internal error          | Internal server error             |
| -32001 | Tool not found          | Requested tool not registered     |
| -32002 | Resource not found      | Requested resource not available  |
| -32003 | Prompt not found        | Requested prompt not registered   |
| -32004 | Tool execution error    | Tool failed to execute            |
| -32008 | Session not initialized | Session must be initialized first |

## Getting Help

### Collect Diagnostic Information

When reporting issues, include:

1. **Server version**:

   ```bash
   tfo-mcp --version
   ```

2. **Python version**:

   ```bash
   python --version
   ```

3. **Configuration** (remove sensitive data):

   ```bash
   tfo-mcp validate 2>&1
   ```

4. **Debug logs**:

   ```bash
   tfo-mcp serve --debug 2>debug.log
   ```

5. **Error message** (full stack trace if available)

### Support Channels

- GitHub Issues: https://github.com/telemetryflow/telemetryflow-python-mcp/issues
- Documentation: https://docs.telemetryflow.io/mcp
