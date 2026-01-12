# TelemetryFlow Python MCP Data Flow Diagrams

> Data Flow Diagrams for TelemetryFlow Python MCP Server

---

## Table of Contents

- [Overview](#overview)
- [Level 0 - Context Diagram](#level-0---context-diagram)
- [Level 1 - System Overview](#level-1---system-overview)
- [Level 2 - Request Processing](#level-2---request-processing)
- [Level 2 - Tool Execution](#level-2---tool-execution)
- [Level 2 - Claude Conversation](#level-2---claude-conversation)
- [State Diagrams](#state-diagrams)
- [Sequence Diagrams](#sequence-diagrams)

---

## Overview

This document provides Data Flow Diagrams (DFD), State Diagrams, and Sequence Diagrams that describe how data moves through the TelemetryFlow Python MCP Server system.

```mermaid
flowchart LR
    subgraph Diagrams["Flow Diagrams"]
        DFD["DFD<br/>Data Flow"]
        STATE["State<br/>Lifecycle"]
        SEQ["Sequence<br/>Interactions"]
    end

    DFD --> |"Shows"| FLOW["Data Movement"]
    STATE --> |"Shows"| LIFECYCLE["State Changes"]
    SEQ --> |"Shows"| INTERACTION["Component Interaction"]

    style DFD fill:#e8f5e9,stroke:#4caf50
    style STATE fill:#fff3e0,stroke:#ff9800
    style SEQ fill:#fce4ec,stroke:#e91e63
```

---

## Level 0 - Context Diagram

```mermaid
flowchart TB
    subgraph External["External Systems"]
        CLIENT["MCP Client<br/>(Claude Code, IDE)"]
        CLAUDE["Anthropic<br/>Claude API"]
        OTEL["TelemetryFlow<br/>Collector"]
    end

    subgraph TFO_MCP["TelemetryFlow Python MCP Server"]
        SYSTEM["MCP Server<br/>Process"]
    end

    CLIENT -->|"JSON-RPC Requests"| SYSTEM
    SYSTEM -->|"JSON-RPC Responses"| CLIENT
    SYSTEM -->|"API Requests"| CLAUDE
    CLAUDE -->|"API Responses"| SYSTEM
    SYSTEM -->|"Telemetry Data"| OTEL

    style SYSTEM fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px
```

---

## Level 1 - System Overview

```mermaid
flowchart TB
    subgraph Clients["External Clients"]
        C1["Claude Code"]
        C2["IDE Extension"]
        C3["Custom Client"]
    end

    subgraph TFO_MCP["TelemetryFlow Python MCP Server"]
        subgraph Presentation["1.0 Presentation"]
            P1["1.1 Request Parser"]
            P2["1.2 Response Builder"]
            P3["1.3 Method Router"]
        end

        subgraph Application["2.0 Application"]
            A1["2.1 Command Handler"]
            A2["2.2 Query Handler"]
            A3["2.3 Event Publisher"]
        end

        subgraph Domain["3.0 Domain"]
            D1["3.1 Session Aggregate"]
            D2["3.2 Conversation Aggregate"]
            D3["3.3 Tool Entity"]
        end

        subgraph Infrastructure["4.0 Infrastructure"]
            I1["4.1 Claude Client"]
            I2["4.2 Repository"]
            I3["4.3 Telemetry"]
            I4["4.4 Config"]
        end
    end

    subgraph External["External Services"]
        CLAUDE["Claude API"]
        OTLP["TelemetryFlow Collector"]
    end

    C1 & C2 & C3 -->|"JSON-RPC"| P1
    P1 --> P3
    P3 --> A1 & A2
    A1 --> D1 & D2 & D3
    A2 --> I2
    D3 --> I1
    I1 --> CLAUDE
    I3 --> OTLP
    A1 --> A3
    D1 & D2 --> I2
    A1 & A2 --> P2
    P2 -->|"JSON-RPC"| C1 & C2 & C3

    style Presentation fill:#e3f2fd,stroke:#2196f3
    style Application fill:#e8f5e9,stroke:#4caf50
    style Domain fill:#fff3e0,stroke:#ff9800
    style Infrastructure fill:#fce4ec,stroke:#e91e63
```

---

## Level 2 - Request Processing

```mermaid
flowchart TB
    subgraph Input["Input"]
        REQ["JSON-RPC Request"]
    end

    subgraph Parse["1.0 Parse Request"]
        P1["1.1 Validate JSON"]
        P2["1.2 Extract Method"]
        P3["1.3 Extract Params"]
    end

    subgraph Route["2.0 Route Request"]
        R1["2.1 Match Method"]
        R2["2.2 Select Handler"]
    end

    subgraph Handle["3.0 Handle Request"]
        H1["3.1 Validate Params"]
        H2["3.2 Execute Logic"]
        H3["3.3 Build Result"]
    end

    subgraph Output["Output"]
        RES["JSON-RPC Response"]
    end

    REQ --> P1 --> P2 --> P3
    P3 --> R1 --> R2
    R2 --> H1 --> H2 --> H3
    H3 --> RES

    style Parse fill:#e3f2fd,stroke:#2196f3
    style Route fill:#e8f5e9,stroke:#4caf50
    style Handle fill:#fff3e0,stroke:#ff9800
```

---

## Level 2 - Tool Execution

```mermaid
flowchart TB
    subgraph Input["Input"]
        CALL["tools/call Request"]
    end

    subgraph Validate["1.0 Validate"]
        V1["1.1 Parse Tool Name"]
        V2["1.2 Find Tool"]
        V3["1.3 Validate Schema"]
    end

    subgraph Execute["2.0 Execute"]
        E1["2.1 Prepare Context"]
        E2["2.2 Run Handler"]
        E3["2.3 Capture Result"]
    end

    subgraph Transform["3.0 Transform"]
        T1["3.1 Format Content"]
        T2["3.2 Handle Errors"]
        T3["3.3 Build Response"]
    end

    subgraph Telemetry["4.0 Telemetry"]
        TE1["4.1 Create Span"]
        TE2["4.2 Record Metrics"]
        TE3["4.3 Log Event"]
    end

    subgraph Output["Output"]
        RES["CallToolResult"]
    end

    CALL --> V1 --> V2 --> V3
    V3 --> TE1
    TE1 --> E1 --> E2 --> E3
    E3 --> T1 --> T2 --> T3
    T3 --> TE2 --> TE3
    TE3 --> RES

    style Validate fill:#e3f2fd,stroke:#2196f3
    style Execute fill:#e8f5e9,stroke:#4caf50
    style Transform fill:#fff3e0,stroke:#ff9800
    style Telemetry fill:#f3e5f5,stroke:#9c27b0
```

---

## Level 2 - Claude Conversation

```mermaid
flowchart TB
    subgraph Input["Input"]
        MSG["User Message"]
    end

    subgraph Prepare["1.0 Prepare Request"]
        P1["1.1 Get Conversation"]
        P2["1.2 Build Messages"]
        P3["1.3 Add System Prompt"]
        P4["1.4 Configure Model"]
    end

    subgraph API["2.0 API Call"]
        A1["2.1 Create Request"]
        A2["2.2 Send to Claude"]
        A3["2.3 Handle Response"]
    end

    subgraph Process["3.0 Process Response"]
        R1["3.1 Extract Content"]
        R2["3.2 Handle Tool Use"]
        R3["3.3 Update Conversation"]
    end

    subgraph Output["Output"]
        RES["Assistant Response"]
    end

    MSG --> P1 --> P2 --> P3 --> P4
    P4 --> A1 --> A2 --> A3
    A3 --> R1 --> R2 --> R3
    R3 --> RES

    style Prepare fill:#e3f2fd,stroke:#2196f3
    style API fill:#fce4ec,stroke:#e91e63
    style Process fill:#e8f5e9,stroke:#4caf50
```

---

## Level 2 - Telemetry Flow

```mermaid
flowchart TB
    subgraph Input["Input"]
        EVENT["Telemetry Event"]
    end

    subgraph Collect["1.0 Collect"]
        C1["1.1 Create Span/Metric"]
        C2["1.2 Add Attributes"]
        C3["1.3 Set Timestamp"]
    end

    subgraph Process["2.0 Process"]
        P1["2.1 Validate Data"]
        P2["2.2 Add Context"]
        P3["2.3 Batch Events"]
    end

    subgraph Export["3.0 Export"]
        E1["3.1 Serialize"]
        E2["3.2 Compress"]
        E3["3.3 Send to Collector"]
    end

    subgraph Output["Output"]
        OTLP["TelemetryFlow Collector"]
    end

    EVENT --> C1 --> C2 --> C3
    C3 --> P1 --> P2 --> P3
    P3 --> E1 --> E2 --> E3
    E3 --> OTLP

    style Collect fill:#e3f2fd,stroke:#2196f3
    style Process fill:#e8f5e9,stroke:#4caf50
    style Export fill:#fff3e0,stroke:#ff9800
```

---

## State Diagrams

### Session State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Create Session

    Created --> Initializing: Receive initialize

    Initializing --> Ready: Send initialized
    Initializing --> Error: Initialization Failed

    Ready --> Ready: Handle Requests
    Ready --> Ready: tools/list, tools/call
    Ready --> Ready: resources/list, resources/read
    Ready --> Ready: prompts/list, prompts/get

    Ready --> Closing: Receive shutdown

    Error --> Closing: Cleanup

    Closing --> Closed: Cleanup Complete

    Closed --> [*]

    state Ready {
        [*] --> Idle
        Idle --> Processing: Receive Request
        Processing --> Idle: Send Response
    }
```

### Conversation State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Create Conversation

    Created --> Active: First Message

    Active --> Active: Add Message
    Active --> Waiting: API Request Sent

    Waiting --> Active: Response Received
    Waiting --> Error: API Error

    Active --> Closed: Close Conversation

    Error --> Active: Retry Success
    Error --> Closed: Max Retries

    Closed --> [*]

    state Active {
        [*] --> Ready
        Ready --> Processing: Send Message
        Processing --> Ready: Response Received
    }
```

### Tool Execution State Machine

```mermaid
stateDiagram-v2
    [*] --> Received: tools/call

    Received --> Validating: Parse Request

    Validating --> Validated: Schema Valid
    Validating --> Failed: Schema Invalid

    Validated --> Executing: Run Handler

    Executing --> Completed: Handler Success
    Executing --> Failed: Handler Error
    Executing --> TimedOut: Timeout

    Completed --> [*]: Return Result
    Failed --> [*]: Return Error
    TimedOut --> [*]: Return Timeout Error

    state Executing {
        [*] --> Running
        Running --> Timeout: Time Limit
        Running --> Done: Complete
    }
```

### Telemetry Client State Machine

```mermaid
stateDiagram-v2
    [*] --> Disabled: Telemetry Disabled

    [*] --> Creating: Telemetry Enabled

    Creating --> Initializing: Client Created

    Initializing --> Ready: Initialize Success
    Initializing --> Disabled: Initialize Failed

    Ready --> Ready: Record Metrics
    Ready --> Ready: Create Spans
    Ready --> Flushing: Flush Request

    Flushing --> Ready: Flush Complete

    Ready --> ShuttingDown: Shutdown

    ShuttingDown --> Closed: Shutdown Complete

    Closed --> [*]
```

---

## Sequence Diagrams

### Complete MCP Session Flow

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as TFO-Python-MCP Server
    participant Session as Session Aggregate
    participant Telemetry as Telemetry Client
    participant Events as Event Publisher

    Note over Client,Events: Session Initialization

    Client->>Server: initialize
    Server->>Session: Create Session
    Server->>Telemetry: record_session_event(initialized)
    Session->>Events: SessionCreatedEvent
    Server-->>Client: InitializeResult

    Client->>Server: notifications/initialized
    Server->>Session: Set Ready State
    Session->>Events: SessionInitializedEvent

    Note over Client,Events: Tool Operations

    Client->>Server: tools/list
    Server->>Session: Get Tools
    Session-->>Server: Tool List
    Server-->>Client: ToolListResult

    Client->>Server: tools/call
    Server->>Telemetry: span(tools.execute)
    Server->>Session: Execute Tool
    Session->>Telemetry: record_tool_call()
    Session->>Events: ToolExecutedEvent
    Server-->>Client: CallToolResult

    Note over Client,Events: Session Cleanup

    Client->>Server: shutdown
    Server->>Session: Close Session
    Server->>Telemetry: record_session_event(closed)
    Server->>Telemetry: flush()
    Session->>Events: SessionClosedEvent
    Server-->>Client: (acknowledged)
```

### Claude API Integration Flow

```mermaid
sequenceDiagram
    participant Tool as Tool Handler
    participant Service as Claude Service
    participant SDK as anthropic-sdk-python
    participant API as Anthropic API
    participant Telemetry as Telemetry Client

    Tool->>Telemetry: span(claude.request)
    Tool->>Service: create_message(request)

    Service->>Service: Build API Request
    Service->>Service: Add Headers

    loop Retry Loop
        Service->>SDK: client.messages.create()
        SDK->>API: POST /v1/messages

        alt Success
            API-->>SDK: 200 OK + Response
            SDK-->>Service: Message
            Service->>Service: Convert Response
            Service->>Telemetry: record_histogram(duration)
            Service-->>Tool: ClaudeResponse
        else Rate Limited (429)
            API-->>SDK: 429 Too Many Requests
            SDK-->>Service: RateLimitError
            Service->>Service: Wait (exponential backoff)
        else Server Error (5xx)
            API-->>SDK: 5xx Error
            SDK-->>Service: ServerError
            Service->>Service: Wait and Retry
        else Client Error (4xx)
            API-->>SDK: 4xx Error
            SDK-->>Service: ClientError
            Service->>Telemetry: record_error()
            Service-->>Tool: Error
        end
    end
```

### Telemetry Recording Flow

```mermaid
sequenceDiagram
    participant Handler as Tool Handler
    participant Telemetry as MCPTelemetryClient
    participant SDK as TelemetryFlow SDK
    participant Collector as TelemetryFlow Collector

    Handler->>Telemetry: span(tools.execute)
    Telemetry->>SDK: create_span()
    SDK-->>Telemetry: span_id

    Handler->>Handler: Execute Tool

    Handler->>Telemetry: record_tool_call()
    Telemetry->>SDK: increment_counter(mcp.tools.calls)
    Telemetry->>SDK: record_histogram(mcp.tools.duration)

    alt Success
        Handler->>Telemetry: add_span_event(completed)
    else Error
        Handler->>Telemetry: add_span_event(error)
        Telemetry->>SDK: increment_counter(mcp.tools.errors)
    end

    Telemetry->>SDK: end_span()
    SDK->>Collector: Export Batch
```

### Error Handling Flow

```mermaid
sequenceDiagram
    participant Client as Client
    participant Server as Server
    participant Handler as Handler
    participant Domain as Domain

    Client->>Server: Request

    alt Parse Error
        Server-->>Client: -32700 Parse Error
    else Invalid Request
        Server->>Handler: Route
        Handler-->>Server: Invalid
        Server-->>Client: -32600 Invalid Request
    else Method Not Found
        Server->>Handler: Route
        Handler-->>Server: Not Found
        Server-->>Client: -32601 Method Not Found
    else Invalid Params
        Server->>Handler: Route
        Handler->>Domain: Execute
        Domain-->>Handler: Invalid Params
        Handler-->>Server: Error
        Server-->>Client: -32602 Invalid Params
    else Internal Error
        Server->>Handler: Route
        Handler->>Domain: Execute
        Domain-->>Handler: Exception
        Handler-->>Server: Error
        Server-->>Client: -32603 Internal Error
    else Success
        Server->>Handler: Route
        Handler->>Domain: Execute
        Domain-->>Handler: Result
        Handler-->>Server: Success
        Server-->>Client: Result
    end
```

---

## Related Documentation

- [Entity Relationship Diagrams](ERD.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)

---

<div align="center">

**[Back to Documentation Index](README.md)**

</div>
