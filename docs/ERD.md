# TFO-Python-MCP Entity Relationship Diagrams

> Entity Relationship Diagrams for TelemetryFlow Python MCP Server

---

## Table of Contents

- [Overview](#overview)
- [Complete Domain ERD](#complete-domain-erd)
- [Session Aggregate ERD](#session-aggregate-erd)
- [Conversation Aggregate ERD](#conversation-aggregate-erd)
- [Value Objects ERD](#value-objects-erd)
- [Domain Model Classes](#domain-model-classes)

---

## Overview

This document provides Entity Relationship Diagrams that describe the data structures and relationships within the TFO-Python-MCP Server.

```mermaid
flowchart LR
    subgraph ERD["Entity Relationship Diagrams"]
        DOMAIN["Domain ERD"]
        SESSION["Session ERD"]
        CONV["Conversation ERD"]
        VO["Value Objects"]
        CLASS["Domain Classes"]
    end

    DOMAIN --> |"Describes"| STRUCT["Domain Structure"]
    SESSION --> |"Details"| SAGG["Session Aggregate"]
    CONV --> |"Details"| CAGG["Conversation Aggregate"]
    VO --> |"Defines"| TYPES["Value Types"]
    CLASS --> |"Maps to"| PYTHON["Python Classes"]

    style DOMAIN fill:#e3f2fd,stroke:#2196f3
    style SESSION fill:#e8f5e9,stroke:#4caf50
    style CONV fill:#fff3e0,stroke:#ff9800
    style VO fill:#fce4ec,stroke:#e91e63
    style CLASS fill:#f3e5f5,stroke:#9c27b0
```

---

## Complete Domain ERD

```mermaid
erDiagram
    SESSION ||--o{ CONVERSATION : contains
    SESSION ||--o{ TOOL : registers
    SESSION ||--o{ RESOURCE : registers
    SESSION ||--o{ PROMPT : registers
    CONVERSATION ||--o{ MESSAGE : contains
    MESSAGE ||--o{ CONTENT_BLOCK : contains
    TOOL ||--o{ TOOL_RESULT : produces
    RESOURCE ||--o{ RESOURCE_CONTENT : provides

    SESSION {
        uuid id PK
        string client_name
        string client_version
        string protocol_version
        enum state
        datetime created_at
        datetime updated_at
    }

    CONVERSATION {
        uuid id PK
        uuid session_id FK
        string model
        string system_prompt
        enum status
        int max_tokens
        float temperature
        datetime created_at
    }

    MESSAGE {
        uuid id PK
        uuid conversation_id FK
        enum role
        datetime created_at
    }

    CONTENT_BLOCK {
        uuid id PK
        uuid message_id FK
        enum type
        text content
        string mime_type
    }

    TOOL {
        string name PK
        string description
        json input_schema
        boolean enabled
        float timeout_seconds
    }

    TOOL_RESULT {
        uuid id PK
        string tool_name FK
        json content
        boolean is_error
        datetime executed_at
    }

    RESOURCE {
        string uri PK
        string name
        string description
        string mime_type
        boolean is_template
    }

    RESOURCE_CONTENT {
        uuid id PK
        string uri FK
        text content
        bytes blob
    }

    PROMPT {
        string name PK
        string description
        json arguments
    }
```

---

## Session Aggregate ERD

```mermaid
erDiagram
    SESSION_AGGREGATE ||--|| SESSION_ID : has
    SESSION_AGGREGATE ||--|| CLIENT_INFO : has
    SESSION_AGGREGATE ||--|| CAPABILITIES : has
    SESSION_AGGREGATE ||--o{ TOOL_ENTITY : contains
    SESSION_AGGREGATE ||--o{ RESOURCE_ENTITY : contains
    SESSION_AGGREGATE ||--o{ PROMPT_ENTITY : contains
    SESSION_AGGREGATE ||--o{ CONVERSATION_AGGREGATE : manages
    SESSION_AGGREGATE ||--o{ DOMAIN_EVENT : emits

    SESSION_AGGREGATE {
        SessionID id
        SessionState state
        ClientInfo client
        Capabilities capabilities
        MCPLogLevel log_level
        datetime created_at
    }

    SESSION_ID {
        uuid value
    }

    CLIENT_INFO {
        string name
        string version
    }

    CAPABILITIES {
        boolean tools
        boolean resources
        boolean prompts
        boolean logging
        boolean sampling
    }

    TOOL_ENTITY {
        ToolName name
        string description
        JSONSchema input_schema
        ToolHandler handler
        boolean enabled
        float timeout_seconds
    }

    RESOURCE_ENTITY {
        ResourceURI uri
        string name
        MimeType mime_type
        ResourceReader reader
        boolean is_template
    }

    PROMPT_ENTITY {
        string name
        string description
        PromptArgument[] arguments
        PromptGenerator generator
    }

    CONVERSATION_AGGREGATE {
        ConversationID id
        Model model
        Message[] messages
        ConversationStatus status
    }

    DOMAIN_EVENT {
        uuid event_id
        string event_type
        datetime timestamp
        json payload
    }
```

---

## Conversation Aggregate ERD

```mermaid
erDiagram
    CONVERSATION_AGGREGATE ||--|| CONVERSATION_ID : has
    CONVERSATION_AGGREGATE ||--|| MODEL : uses
    CONVERSATION_AGGREGATE ||--o{ MESSAGE_ENTITY : contains
    MESSAGE_ENTITY ||--|| MESSAGE_ID : has
    MESSAGE_ENTITY ||--|| ROLE : has
    MESSAGE_ENTITY ||--o{ CONTENT_BLOCK : contains

    CONVERSATION_AGGREGATE {
        ConversationID id
        SessionID session_id
        Model model
        SystemPrompt system_prompt
        ConversationStatus status
        int max_tokens
        float temperature
    }

    CONVERSATION_ID {
        uuid value
    }

    MODEL {
        string value
    }

    MESSAGE_ENTITY {
        MessageID id
        Role role
        ContentBlock[] content
        datetime created_at
    }

    MESSAGE_ID {
        uuid value
    }

    ROLE {
        enum value "user|assistant"
    }

    CONTENT_BLOCK {
        ContentType type
        string text
        string data
        string mime_type
    }
```

---

## Value Objects ERD

```mermaid
erDiagram
    VALUE_OBJECTS ||--o{ IDENTIFIERS : contains
    VALUE_OBJECTS ||--o{ CONTENT_TYPES : contains
    VALUE_OBJECTS ||--o{ MCP_TYPES : contains

    IDENTIFIERS {
        SessionID session_id "UUID"
        ConversationID conversation_id "UUID"
        MessageID message_id "UUID"
        ToolName tool_name "str"
        ResourceURI resource_uri "str"
        PromptName prompt_name "str"
        RequestID request_id "int|str"
    }

    CONTENT_TYPES {
        ContentType type "text|image|resource"
        Role role "user|assistant"
        Model model "claude-*"
        MimeType mime_type "text/*"
        TextContent text "str"
        SystemPrompt system "str"
    }

    MCP_TYPES {
        JSONRPCVersion version "2.0"
        MCPMethod method "str"
        MCPCapability capability "str"
        MCPLogLevel log_level "enum"
        MCPProtocolVersion protocol "2024-11-05"
        MCPErrorCode error_code "int"
    }
```

---

## Domain Model Classes

### Session Domain Classes

```mermaid
classDiagram
    class Session {
        +UUID id
        +SessionState state
        +ClientInfo client
        +SessionCapabilities capabilities
        +MCPLogLevel log_level
        +datetime created_at
        +datetime updated_at
        +dict[str, Tool] tools
        +dict[str, Resource] resources
        +dict[str, Prompt] prompts
        +list[DomainEvent] events
        +create(name, version, capabilities) Session
        +initialize(client, capabilities) dict
        +register_tool(tool) void
        +register_resource(resource) void
        +register_prompt(prompt) void
        +get_tool(name) Tool
        +get_resource(uri) Resource
        +get_prompt(name) Prompt
        +list_tools() list[Tool]
        +list_resources() list[Resource]
        +list_prompts() list[Prompt]
        +close() void
    }

    class SessionCapabilities {
        +bool tools
        +bool resources
        +bool prompts
        +bool logging
        +bool sampling
        +to_dict() dict
    }

    class ClientInfo {
        +str name
        +str version
    }

    class SessionState {
        <<enumeration>>
        CREATED
        INITIALIZING
        READY
        CLOSED
    }

    Session --> SessionCapabilities
    Session --> ClientInfo
    Session --> SessionState
```

### Tool Domain Classes

```mermaid
classDiagram
    class Tool {
        +ToolName name
        +str description
        +dict input_schema
        +str category
        +bool enabled
        +float timeout_seconds
        +ToolHandler handler
        +execute(arguments) ToolResult
        +to_mcp_format() dict
    }

    class ToolName {
        +str value
        +validate() bool
        +__str__() str
    }

    class ToolResult {
        +list[dict] content
        +bool is_error
        +success(content) ToolResult
        +error(message) ToolResult
        +to_dict() dict
    }

    class ToolHandler {
        <<protocol>>
        +__call__(arguments) ToolResult
    }

    Tool --> ToolName
    Tool --> ToolHandler
    Tool ..> ToolResult
```

### Resource Domain Classes

```mermaid
classDiagram
    class Resource {
        +str uri
        +str uri_template
        +str name
        +str description
        +str mime_type
        +bool is_template
        +ResourceReader reader
        +read(params) ResourceContent
        +to_mcp_format() dict
        +to_template_format() dict
    }

    class ResourceContent {
        +str uri
        +str mime_type
        +str text
        +bytes blob
        +to_dict() dict
    }

    class ResourceReader {
        <<protocol>>
        +__call__(params) ResourceContent
    }

    Resource --> ResourceReader
    Resource ..> ResourceContent
```

### Prompt Domain Classes

```mermaid
classDiagram
    class Prompt {
        +str name
        +str description
        +list[PromptArgument] arguments
        +PromptGenerator generator
        +get_messages(arguments) list[PromptMessage]
        +to_mcp_format() dict
    }

    class PromptArgument {
        +str name
        +str description
        +bool required
        +to_dict() dict
    }

    class PromptMessage {
        +str role
        +dict content
        +to_dict() dict
    }

    class PromptGenerator {
        <<protocol>>
        +__call__(arguments) list[PromptMessage]
    }

    Prompt --> PromptArgument
    Prompt --> PromptGenerator
    Prompt ..> PromptMessage
```

### Event Domain Classes

```mermaid
classDiagram
    class DomainEvent {
        <<abstract>>
        +UUID event_id
        +datetime timestamp
        +str event_type
    }

    class SessionCreatedEvent {
        +str session_id
        +str server_name
        +str server_version
    }

    class SessionInitializedEvent {
        +str session_id
        +str client_name
        +str client_version
    }

    class SessionClosedEvent {
        +str session_id
    }

    class ToolRegisteredEvent {
        +str session_id
        +str tool_name
        +str category
    }

    class ToolExecutedEvent {
        +str session_id
        +str tool_name
        +bool success
        +float duration_ms
        +str error_message
    }

    DomainEvent <|-- SessionCreatedEvent
    DomainEvent <|-- SessionInitializedEvent
    DomainEvent <|-- SessionClosedEvent
    DomainEvent <|-- ToolRegisteredEvent
    DomainEvent <|-- ToolExecutedEvent
```

### Telemetry Classes

```mermaid
classDiagram
    class MCPTelemetryClient {
        -TelemetryConfig config
        -TelemetryFlowClient client
        -bool enabled
        -bool initialized
        +initialize() void
        +shutdown(timeout) void
        +flush() void
        +is_enabled bool
        +increment_counter(name, value, attributes) void
        +record_gauge(name, value, attributes) void
        +record_histogram(name, value, unit, attributes) void
        +span(name, kind, attributes) ContextManager
        +record_tool_call(tool_name, duration, success, error_type) void
        +record_resource_read(uri, duration, success) void
        +record_prompt_get(name, duration, success) void
        +record_session_event(event, session_id, attributes) void
    }

    class TelemetryConfig {
        +bool enabled
        +str service_name
        +str service_version
        +str service_namespace
        +str environment
        +str api_key_id
        +str api_key_secret
        +str endpoint
        +str protocol
        +bool enable_traces
        +bool enable_metrics
        +bool enable_logs
    }

    MCPTelemetryClient --> TelemetryConfig
```

---

## Python Type Annotations

### Core Types

```python
from typing import Protocol, TypeVar, Generic
from uuid import UUID
from datetime import datetime
from enum import Enum

# Session types
SessionID = UUID
ConversationID = UUID
MessageID = UUID

# Content types
class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    RESOURCE = "resource"

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

# MCP types
class MCPMethod(str, Enum):
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    LOGGING_SET_LEVEL = "logging/setLevel"
    SHUTDOWN = "shutdown"

class MCPErrorCode(int, Enum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
```

---

## Related Documentation

- [Data Flow Diagrams](DFD.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)

---

<div align="center">

**[Back to Documentation Index](README.md)**

</div>
