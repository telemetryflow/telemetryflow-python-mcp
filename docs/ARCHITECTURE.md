# TelemetryFlow Python MCP Server - Architecture

This document describes the architecture of the TelemetryFlow Python MCP Server Python implementation.

## Overview

The TelemetryFlow Python MCP Server is an enterprise-grade Model Context Protocol (MCP) implementation that serves as the AI integration layer for the TelemetryFlow platform. It follows Domain-Driven Design (DDD) and CQRS patterns for maintainability and scalability.

## Architecture Layers

```mermaid
graph TB
    subgraph Presentation["Presentation Layer"]
        Server["MCP Server<br/>(JSON-RPC)"]
        Tools["Tools Registry"]
        Resources["Resources Manager"]
        Prompts["Prompts Manager"]
    end

    subgraph Application["Application Layer"]
        subgraph Commands["Commands"]
            C1["Initialize"]
            C2["RegisterTool"]
            C3["ExecuteTool"]
            C4["SendMessage"]
        end
        subgraph Queries["Queries"]
            Q1["GetSession"]
            Q2["ListTools"]
            Q3["ListResources"]
            Q4["GetPrompt"]
        end
        subgraph Handlers["Handlers"]
            H1["SessionHandler"]
            H2["ToolHandler"]
            H3["ConversationHandler"]
        end
    end

    subgraph Domain["Domain Layer"]
        subgraph Aggregates["Aggregates"]
            Session["Session"]
            Conversation["Conversation"]
        end
        subgraph Entities["Entities"]
            Message["Message"]
            Tool["Tool"]
            Resource["Resource"]
            Prompt["Prompt"]
        end
        ValueObjects["Value Objects"]
        DomainEvents["Domain Events"]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        Claude["ClaudeClient<br/>(Anthropic)"]
        Config["Config<br/>(Pydantic)"]
        Logging["Logging<br/>(structlog)"]
        Persistence["Persistence<br/>(In-Memory)"]
        Cache["Cache<br/>(Redis)"]
        Queue["Queue<br/>(NATS)"]
    end

    Presentation --> Application
    Application --> Domain
    Infrastructure --> Domain
    Application --> Infrastructure

    style Presentation fill:#e1f5fe
    style Application fill:#fff3e0
    style Domain fill:#e8f5e9
    style Infrastructure fill:#fce4ec
```

## Layer Responsibilities

### Presentation Layer

The presentation layer handles all external communication:

- **MCP Server**: JSON-RPC 2.0 server over stdio
- **Tools Registry**: Manages tool registration and execution
- **Resources Manager**: Handles resource listing and reading
- **Prompts Manager**: Manages prompt templates

### Application Layer

The application layer orchestrates business operations using CQRS:

- **Commands**: Write operations (Initialize, RegisterTool, ExecuteTool)
- **Queries**: Read operations (ListTools, GetSession, ReadResource)
- **Handlers**: Process commands and queries

### Domain Layer

The domain layer contains core business logic:

- **Aggregates**: Session and Conversation manage their invariants
- **Entities**: Tool, Resource, Prompt, Message
- **Value Objects**: Immutable types (IDs, enums, configs)
- **Domain Events**: For event sourcing and cross-aggregate communication

### Infrastructure Layer

The infrastructure layer provides external service implementations:

- **Claude Client**: Anthropic API integration
- **Configuration**: Pydantic settings management
- **Logging**: Structured logging with structlog
- **Persistence**: Repository implementations

## MCP Protocol Implementation

### Transport

```mermaid
flowchart LR
    Client["Client"]
    Server["MCP Server"]
    Session["Session State"]
    Tools["Tool Registry"]
    Resources["Resources"]
    Prompts["Prompts"]

    Client -->|"stdin"| Server
    Server -->|"stdout"| Client
    Server --> Session
    Server --> Tools
    Server --> Resources
    Server --> Prompts
```

### Message Flow

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Handler
    participant Domain

    Client->>Server: JSON-RPC Request (stdin)
    Server->>Server: Parse & Validate JSON-RPC 2.0
    Server->>Handler: Route to Handler
    Handler->>Domain: Execute Command/Query
    Domain-->>Handler: Result
    Handler-->>Server: Response
    Server-->>Client: JSON-RPC Response (stdout)
```

### Supported Methods

| Category  | Methods                                                  |
| --------- | -------------------------------------------------------- |
| Lifecycle | initialize, notifications/initialized, ping, shutdown    |
| Tools     | tools/list, tools/call                                   |
| Resources | resources/list, resources/read, resources/templates/list |
| Prompts   | prompts/list, prompts/get                                |
| Logging   | logging/setLevel                                         |

## Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> CREATED: new Session()
    CREATED --> INITIALIZING: initialize request
    INITIALIZING --> READY: initialization complete
    READY --> CLOSING: shutdown request
    CLOSING --> CLOSED: cleanup complete
    CLOSED --> [*]

    READY --> READY: tools/call, resources/read, etc.
```

## Data Flow

```mermaid
flowchart TB
    subgraph Client
        Request["JSON-RPC Request"]
        Response["JSON-RPC Response"]
    end

    subgraph Server["MCP Server"]
        Parse["Parse JSON"]
        Route["Route Method"]
        Serialize["Serialize Response"]
    end

    subgraph Handlers
        SessionH["Session Handler"]
        ToolH["Tool Handler"]
        ResourceH["Resource Handler"]
        PromptH["Prompt Handler"]
    end

    subgraph Domain
        Session["Session"]
        Tools["Tools"]
        Resources["Resources"]
        Prompts["Prompts"]
    end

    Request --> Parse
    Parse --> Route
    Route --> SessionH & ToolH & ResourceH & PromptH
    SessionH --> Session
    ToolH --> Tools
    ResourceH --> Resources
    PromptH --> Prompts
    Session & Tools & Resources & Prompts --> Serialize
    Serialize --> Response
```

## Built-in Components

### Tools (8)

| Tool                | Category | Description        |
| ------------------- | -------- | ------------------ |
| echo                | utility  | Echo testing tool  |
| read_file           | file     | Read file contents |
| write_file          | file     | Write to file      |
| list_directory      | file     | List directory     |
| search_files        | file     | Search by pattern  |
| execute_command     | system   | Run shell command  |
| system_info         | system   | System information |
| claude_conversation | ai       | Chat with Claude   |

### Resources (3)

| Resource        | Type     | Description          |
| --------------- | -------- | -------------------- |
| config://server | static   | Server configuration |
| status://health | static   | Health status        |
| file:///{path}  | template | File access          |

### Prompts (3)

| Prompt       | Description            |
| ------------ | ---------------------- |
| code_review  | Code review assistance |
| explain_code | Code explanation       |
| debug_help   | Debugging assistance   |

## Configuration

```mermaid
flowchart TB
    subgraph Sources["Configuration Sources"]
        Env["Environment Variables<br/>TELEMETRYFLOW_MCP_*"]
        File["Config File<br/>tfo-mcp.yaml"]
        Default["Default Values"]
    end

    subgraph Priority["Priority (High to Low)"]
        P1["1. Environment"]
        P2["2. Config File"]
        P3["3. Defaults"]
    end

    subgraph Config["Configuration"]
        Server["ServerConfig"]
        Claude["ClaudeConfig"]
        MCP["MCPConfig"]
        Logging["LoggingConfig"]
        Telemetry["TelemetryConfig"]
    end

    Env --> P1
    File --> P2
    Default --> P3
    P1 & P2 & P3 --> Config
```

### Key Configuration Sections

```yaml
server: # Server settings (name, version, transport)
claude: # Claude API settings (api_key, model, tokens)
mcp: # MCP protocol settings (capabilities, timeouts)
logging: # Logging settings (level, format, output)
telemetry: # Telemetry settings (OTLP endpoint)
```

## Error Handling

```mermaid
flowchart TB
    Request["Request"] --> Parse{"Parse JSON"}
    Parse -->|"Invalid"| ParseError["-32700<br/>Parse Error"]
    Parse -->|"Valid"| Validate{"Validate Request"}
    Validate -->|"Invalid"| InvalidReq["-32600<br/>Invalid Request"]
    Validate -->|"Valid"| Route{"Route Method"}
    Route -->|"Not Found"| MethodNotFound["-32601<br/>Method Not Found"]
    Route -->|"Found"| Execute{"Execute"}
    Execute -->|"Bad Params"| InvalidParams["-32602<br/>Invalid Params"]
    Execute -->|"Error"| InternalError["-32603<br/>Internal Error"]
    Execute -->|"Success"| Success["Result"]
```

### Error Codes

| Code   | Name               | Description        |
| ------ | ------------------ | ------------------ |
| -32700 | Parse error        | Invalid JSON       |
| -32600 | Invalid Request    | Not valid JSON-RPC |
| -32601 | Method not found   | Unknown method     |
| -32602 | Invalid params     | Invalid parameters |
| -32603 | Internal error     | Server error       |
| -32001 | Tool not found     | MCP specific       |
| -32002 | Resource not found | MCP specific       |
| -32003 | Prompt not found   | MCP specific       |

## Testing Strategy

```mermaid
graph TB
    subgraph Unit["Unit Tests"]
        Domain["Domain Tests"]
        Entity["Entity Tests"]
        ValueObject["Value Object Tests"]
        Tool["Tool Handler Tests"]
    end

    subgraph Integration["Integration Tests"]
        Handler["Handler Tests"]
        Server["Server Tests"]
        Repository["Repository Tests"]
    end

    subgraph E2E["E2E Tests"]
        Protocol["Protocol Tests"]
        Flow["Full Flow Tests"]
    end

    Unit --> Integration --> E2E
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Client["AI Client"]
        Claude["Claude Desktop"]
    end

    subgraph Container["Docker Container"]
        MCP["TFO-MCP Server"]
    end

    subgraph Optional["Optional Services"]
        Redis["Redis Cache"]
        NATS["NATS JetStream"]
        Postgres["PostgreSQL"]
        ClickHouse["ClickHouse"]
    end

    Claude <-->|"stdio"| MCP
    MCP -.->|"cache"| Redis
    MCP -.->|"queue"| NATS
    MCP -.->|"persistence"| Postgres
    MCP -.->|"analytics"| ClickHouse
```

## Future Enhancements

1. **Additional Transports**: SSE, WebSocket support
2. **Database Persistence**: PostgreSQL, ClickHouse
3. **Caching**: Redis integration
4. **Message Queue**: NATS JetStream
5. **Observability**: OpenTelemetry integration
6. **Authentication**: API key validation
7. **Rate Limiting**: Request throttling
