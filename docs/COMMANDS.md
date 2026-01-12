# TFO-Python-MCP Commands Reference

> Complete CLI and MCP protocol commands reference for TelemetryFlow Python MCP Server

---

## Table of Contents

- [Overview](#overview)
- [CLI Commands](#cli-commands)
- [MCP Protocol Methods](#mcp-protocol-methods)
- [Built-in Tools](#built-in-tools)
- [Resource Operations](#resource-operations)
- [Prompt Operations](#prompt-operations)
- [Session Management](#session-management)
- [Examples](#examples)

---

## Overview

TFO-Python-MCP provides two interfaces for interaction:

1. **CLI Commands** - Command-line interface for server management
2. **MCP Protocol Methods** - JSON-RPC methods for client communication

### Command Architecture

```mermaid
flowchart TB
    subgraph CLI["CLI Interface"]
        SERVE["python -m tfo_mcp serve"]
        INFO["python -m tfo_mcp info"]
        VALIDATE["python -m tfo_mcp validate"]
        INIT["python -m tfo_mcp init-config"]
    end

    subgraph MCP["MCP Protocol"]
        INIT_M["initialize"]
        TOOLS["tools/*"]
        RESOURCES["resources/*"]
        PROMPTS["prompts/*"]
        LOGGING["logging/*"]
    end

    subgraph Server["TFO-Python-MCP Server"]
        HANDLER["Command Handler"]
    end

    CLI --> HANDLER
    MCP --> HANDLER

    style CLI fill:#e3f2fd,stroke:#2196f3
    style MCP fill:#e8f5e9,stroke:#4caf50
    style Server fill:#fff3e0,stroke:#ff9800
```

---

## CLI Commands

### Command Structure

```mermaid
flowchart LR
    subgraph Structure["Command Structure"]
        PYTHON["python -m tfo_mcp"]
        CMD["command"]
        FLAGS["--flags"]
        ARGS["arguments"]
    end

    PYTHON --> CMD --> FLAGS --> ARGS

    style Structure fill:#e3f2fd,stroke:#2196f3
```

### Available Commands

| Command       | Description              | Usage                                     |
| ------------- | ------------------------ | ----------------------------------------- |
| `serve`       | Start the MCP server     | `python -m tfo_mcp serve [OPTIONS]`       |
| `info`        | Show version information | `python -m tfo_mcp info`                  |
| `validate`    | Validate configuration   | `python -m tfo_mcp validate [OPTIONS]`    |
| `init-config` | Generate sample config   | `python -m tfo_mcp init-config [OPTIONS]` |

### serve Command

Start the MCP server.

```mermaid
flowchart TB
    subgraph Serve["python -m tfo_mcp serve"]
        PARSE["Parse Options"]
        LOAD["Load Config"]
        INIT["Initialize Server"]
        START["Start Listening"]
        SERVE["Serve Requests"]
    end

    PARSE --> LOAD --> INIT --> START --> SERVE

    style Serve fill:#e8f5e9,stroke:#4caf50
```

**Usage:**

```bash
# Basic usage
python -m tfo_mcp serve

# With custom config
python -m tfo_mcp serve --config /path/to/config.yaml

# With debug logging
python -m tfo_mcp serve --log-level debug

# With specific transport
python -m tfo_mcp serve --transport stdio
```

**Options:**

| Option        | Short | Type | Default | Description                          |
| ------------- | ----- | ---- | ------- | ------------------------------------ |
| `--config`    | `-c`  | PATH | None    | Configuration file path              |
| `--log-level` | `-l`  | TEXT | "info"  | Log level (debug/info/warning/error) |
| `--transport` | `-t`  | TEXT | "stdio" | Transport type                       |

### info Command

Display version and system information.

```bash
python -m tfo_mcp info
```

**Output:**

```
TFO-Python-MCP - TelemetryFlow Python MCP Server
Version:     1.1.2
Python:      3.11.7
Platform:    darwin (arm64)
MCP Protocol: 2024-11-05
```

### validate Command

Validate the configuration file.

```mermaid
flowchart TB
    subgraph Validate["python -m tfo_mcp validate"]
        READ["Read Config"]
        PARSE["Parse YAML"]
        CHECK["Validate Fields"]
        REPORT["Report Results"]
    end

    READ --> PARSE --> CHECK --> REPORT

    style Validate fill:#fff3e0,stroke:#ff9800
```

**Usage:**

```bash
# Validate default config
python -m tfo_mcp validate

# Validate specific file
python -m tfo_mcp validate --config /path/to/config.yaml

# Verbose output
python -m tfo_mcp validate --verbose
```

**Options:**

| Option      | Short | Type | Default | Description             |
| ----------- | ----- | ---- | ------- | ----------------------- |
| `--config`  | `-c`  | PATH | None    | Configuration file path |
| `--verbose` | `-v`  | FLAG | false   | Verbose output          |

### init-config Command

Generate a sample configuration file.

```bash
# Generate config in current directory
python -m tfo_mcp init-config

# Generate in specific path
python -m tfo_mcp init-config --output /path/to/config.yaml

# Overwrite existing
python -m tfo_mcp init-config --force
```

---

## MCP Protocol Methods

### Protocol Overview

```mermaid
flowchart TB
    subgraph Client["MCP Client"]
        REQ["JSON-RPC Request"]
    end

    subgraph Server["TFO-Python-MCP Server"]
        ROUTER["Method Router"]

        subgraph Handlers["Method Handlers"]
            H1["initialize"]
            H2["tools/list"]
            H3["tools/call"]
            H4["resources/list"]
            H5["resources/read"]
            H6["prompts/list"]
            H7["prompts/get"]
            H8["logging/setLevel"]
        end
    end

    subgraph Response["Response"]
        RES["JSON-RPC Response"]
    end

    REQ --> ROUTER
    ROUTER --> H1 & H2 & H3 & H4 & H5 & H6 & H7 & H8
    Handlers --> RES

    style Client fill:#e3f2fd,stroke:#2196f3
    style Server fill:#fff3e0,stroke:#ff9800
    style Response fill:#e8f5e9,stroke:#4caf50
```

### Method Categories

```mermaid
flowchart LR
    subgraph Methods["MCP Methods"]
        direction TB
        LIFECYCLE["Lifecycle<br/>initialize, shutdown"]
        TOOLS["Tools<br/>tools/list, tools/call"]
        RESOURCES["Resources<br/>resources/list, resources/read"]
        PROMPTS["Prompts<br/>prompts/list, prompts/get"]
        LOGGING["Logging<br/>logging/setLevel"]
    end

    style LIFECYCLE fill:#e1bee7,stroke:#9c27b0
    style TOOLS fill:#e3f2fd,stroke:#2196f3
    style RESOURCES fill:#e8f5e9,stroke:#4caf50
    style PROMPTS fill:#fff3e0,stroke:#ff9800
    style LOGGING fill:#f5f5f5,stroke:#9e9e9e
```

### initialize

Initialize the MCP session.

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: initialize
    Note right of Server: Create session<br/>Register capabilities
    Server-->>Client: InitializeResult
    Client->>Server: notifications/initialized
    Server-->>Client: (acknowledged)
```

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "my-client",
      "version": "1.0.0"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {},
      "prompts": {},
      "logging": {}
    },
    "serverInfo": {
      "name": "TelemetryFlow-MCP",
      "version": "1.1.2"
    }
  }
}
```

### tools/list

List available tools.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "claude_conversation",
        "description": "Have a conversation with Claude AI",
        "inputSchema": {
          "type": "object",
          "properties": {
            "message": {
              "type": "string",
              "description": "The message to send to Claude"
            },
            "model": {
              "type": "string",
              "description": "Claude model to use"
            }
          },
          "required": ["message"]
        }
      }
    ]
  }
}
```

### tools/call

Execute a tool.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Tool
    participant Claude as Claude API

    Client->>Server: tools/call
    Server->>Tool: Execute
    alt Tool is claude_conversation
        Tool->>Claude: API Request
        Claude-->>Tool: API Response
    end
    Tool-->>Server: Result
    Server-->>Client: CallToolResult
```

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "claude_conversation",
    "arguments": {
      "message": "What is the capital of France?",
      "model": "claude-sonnet-4-20250514"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "The capital of France is Paris."
      }
    ],
    "isError": false
  }
}
```

### resources/list

List available resources.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/list",
  "params": {}
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "resources": [
      {
        "uri": "config://server",
        "name": "Server Configuration",
        "description": "Current server configuration",
        "mimeType": "application/json"
      },
      {
        "uri": "status://health",
        "name": "Health Status",
        "description": "Server health status",
        "mimeType": "application/json"
      }
    ]
  }
}
```

### resources/read

Read a resource.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {
    "uri": "config://server"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "contents": [
      {
        "uri": "config://server",
        "mimeType": "application/json",
        "text": "{\"name\": \"TelemetryFlow-MCP\", ...}"
      }
    ]
  }
}
```

### prompts/list

List available prompts.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "prompts/list",
  "params": {}
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "prompts": [
      {
        "name": "code_review",
        "description": "Review code for best practices",
        "arguments": [
          {
            "name": "code",
            "description": "Code to review",
            "required": true
          },
          {
            "name": "language",
            "description": "Programming language",
            "required": false
          }
        ]
      }
    ]
  }
}
```

### prompts/get

Get a specific prompt.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "prompts/get",
  "params": {
    "name": "code_review",
    "arguments": {
      "code": "def hello(): print('Hello')",
      "language": "python"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "description": "Review code for best practices",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Please review this python code for best practices:\n\ndef hello(): print('Hello')"
        }
      }
    ]
  }
}
```

### logging/setLevel

Set the logging level.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "logging/setLevel",
  "params": {
    "level": "debug"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "result": {}
}
```

---

## Built-in Tools

### Tool Overview

```mermaid
flowchart TB
    subgraph Tools["Built-in Tools"]
        direction TB
        AI["AI Tools"]
        FILE["File Tools"]
        SYSTEM["System Tools"]
    end

    subgraph AITools["AI Tools"]
        CLAUDE["claude_conversation"]
    end

    subgraph FileTools["File Tools"]
        READ["read_file"]
        WRITE["write_file"]
        LIST["list_directory"]
        SEARCH["search_files"]
    end

    subgraph SystemTools["System Tools"]
        EXEC["execute_command"]
        INFO["system_info"]
        ECHO["echo"]
    end

    AI --> AITools
    FILE --> FileTools
    SYSTEM --> SystemTools

    style AI fill:#e1bee7,stroke:#9c27b0
    style FILE fill:#e3f2fd,stroke:#2196f3
    style SYSTEM fill:#e8f5e9,stroke:#4caf50
```

### claude_conversation

Interact with Claude AI.

**Parameters:**

| Name            | Type   | Required | Description                          |
| --------------- | ------ | -------- | ------------------------------------ |
| `message`       | string | Yes      | Message to send to Claude            |
| `model`         | string | No       | Claude model (default: config value) |
| `system_prompt` | string | No       | System prompt for context            |
| `max_tokens`    | int    | No       | Maximum response tokens              |
| `temperature`   | float  | No       | Response temperature (0-1)           |

**Example:**

```json
{
  "name": "claude_conversation",
  "arguments": {
    "message": "Explain recursion in programming",
    "model": "claude-sonnet-4-20250514",
    "system_prompt": "You are a helpful programming tutor",
    "max_tokens": 1000
  }
}
```

### read_file

Read file contents.

**Parameters:**

| Name       | Type   | Required | Description                    |
| ---------- | ------ | -------- | ------------------------------ |
| `path`     | string | Yes      | File path to read              |
| `encoding` | string | No       | File encoding (default: utf-8) |

**Example:**

```json
{
  "name": "read_file",
  "arguments": {
    "path": "/project/main.py"
  }
}
```

### write_file

Write content to a file.

**Parameters:**

| Name          | Type   | Required | Description               |
| ------------- | ------ | -------- | ------------------------- |
| `path`        | string | Yes      | File path to write        |
| `content`     | string | Yes      | Content to write          |
| `create_dirs` | bool   | No       | Create parent directories |

**Example:**

```json
{
  "name": "write_file",
  "arguments": {
    "path": "/project/output.txt",
    "content": "Hello, World!",
    "create_dirs": true
  }
}
```

### list_directory

List directory contents.

**Parameters:**

| Name             | Type   | Required | Description          |
| ---------------- | ------ | -------- | -------------------- |
| `path`           | string | Yes      | Directory path       |
| `recursive`      | bool   | No       | List recursively     |
| `include_hidden` | bool   | No       | Include hidden files |

**Example:**

```json
{
  "name": "list_directory",
  "arguments": {
    "path": "/project",
    "recursive": true
  }
}
```

### search_files

Search for files matching a pattern.

**Parameters:**

| Name      | Type   | Required | Description                      |
| --------- | ------ | -------- | -------------------------------- |
| `pattern` | string | Yes      | Search pattern (glob)            |
| `path`    | string | No       | Base path (default: current dir) |

**Example:**

```json
{
  "name": "search_files",
  "arguments": {
    "pattern": "*.py",
    "path": "/project"
  }
}
```

### execute_command

Execute a shell command.

**Parameters:**

| Name          | Type   | Required | Description                  |
| ------------- | ------ | -------- | ---------------------------- |
| `command`     | string | Yes      | Command to execute           |
| `args`        | list   | No       | Command arguments            |
| `timeout`     | int    | No       | Execution timeout in seconds |
| `working_dir` | string | No       | Working directory            |

**Example:**

```json
{
  "name": "execute_command",
  "arguments": {
    "command": "python",
    "args": ["-c", "print('Hello')"],
    "timeout": 60,
    "working_dir": "/project"
  }
}
```

### system_info

Get system information.

**Parameters:**

| Name      | Type | Required | Description                             |
| --------- | ---- | -------- | --------------------------------------- |
| `include` | list | No       | Info to include (os, cpu, memory, disk) |

**Example:**

```json
{
  "name": "system_info",
  "arguments": {
    "include": ["os", "cpu", "memory"]
  }
}
```

### echo

Echo back the input (useful for testing).

**Parameters:**

| Name      | Type   | Required | Description     |
| --------- | ------ | -------- | --------------- |
| `message` | string | Yes      | Message to echo |

**Example:**

```json
{
  "name": "echo",
  "arguments": {
    "message": "Hello, TFO-Python-MCP!"
  }
}
```

---

## Resource Operations

### Resource Types

| Scheme      | Description          | Example                    |
| ----------- | -------------------- | -------------------------- |
| `config://` | Server configuration | `config://server`          |
| `status://` | Status information   | `status://health`          |
| `file:///`  | Local file system    | `file:///path/to/file.txt` |

---

## Prompt Operations

### Built-in Prompts

| Prompt         | Description           | Arguments                    |
| -------------- | --------------------- | ---------------------------- |
| `code_review`  | Code review assistant | code, language               |
| `explain_code` | Code explanation      | code, language, detail_level |
| `debug_help`   | Debugging assistant   | error_message, code_context  |

---

## Session Management

### Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: Start Server
    Created --> Initializing: initialize
    Initializing --> Ready: initialized
    Ready --> Ready: Handle Requests
    Ready --> Closing: shutdown
    Closing --> Closed: Complete
    Closed --> [*]
```

---

## Examples

### CLI Usage Examples

```bash
# Start server with default config
python -m tfo_mcp serve

# Start with debug logging
python -m tfo_mcp serve --log-level debug

# Start with custom config
python -m tfo_mcp serve --config /etc/tfo-mcp/production.yaml

# Validate configuration
python -m tfo_mcp validate --verbose

# Show version
python -m tfo_mcp info

# Get help
python -m tfo_mcp --help
python -m tfo_mcp serve --help
```

### JSON-RPC Examples

```bash
# Initialize session
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"test","version":"1.0.0"}}}' | python -m tfo_mcp serve

# List tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python -m tfo_mcp serve

# Call echo tool
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"echo","arguments":{"message":"Hello!"}}}' | python -m tfo_mcp serve
```

---

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md)
- [Configuration Guide](CONFIGURATION.md)
- [Development Guide](DEVELOPMENT.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

---

<div align="center">

**[Back to Documentation Index](README.md)**

</div>
