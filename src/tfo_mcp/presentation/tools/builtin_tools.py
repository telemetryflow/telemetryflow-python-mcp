"""Built-in tools for the MCP server."""

from __future__ import annotations

import asyncio
import os
import platform
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles

from tfo_mcp.domain.entities import Tool, ToolInputSchema, ToolResult

ToolHandlerFunc = Callable[[dict[str, Any]], Awaitable[ToolResult]]

if TYPE_CHECKING:
    from tfo_mcp.domain.aggregates import Session
    from tfo_mcp.infrastructure.claude import ClaudeClient


async def _echo_handler(input_data: dict[str, Any]) -> ToolResult:
    """Echo tool handler - for testing."""
    message = input_data.get("message", "")
    return ToolResult.text(f"Echo: {message}")


async def _read_file_handler(input_data: dict[str, Any]) -> ToolResult:
    """Read file tool handler."""
    path = input_data.get("path")
    encoding = input_data.get("encoding", "utf-8")

    if not path:
        return ToolResult.error("Path is required")

    try:
        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            return ToolResult.error(f"File not found: {path}")
        if not file_path.is_file():
            return ToolResult.error(f"Not a file: {path}")

        async with aiofiles.open(file_path, encoding=encoding) as f:
            content = await f.read()

        return ToolResult.text(content)
    except UnicodeDecodeError:
        return ToolResult.error(f"Cannot decode file with encoding: {encoding}")
    except PermissionError:
        return ToolResult.error(f"Permission denied: {path}")
    except Exception as e:
        return ToolResult.error(f"Error reading file: {e}")


async def _write_file_handler(input_data: dict[str, Any]) -> ToolResult:
    """Write file tool handler."""
    path = input_data.get("path")
    content = input_data.get("content", "")
    create_dirs = input_data.get("create_dirs", False)

    if not path:
        return ToolResult.error("Path is required")

    try:
        file_path = Path(path).expanduser().resolve()

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        elif not file_path.parent.exists():
            return ToolResult.error(f"Directory does not exist: {file_path.parent}")

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content)

        return ToolResult.text(f"Successfully wrote {len(content)} bytes to {path}")
    except PermissionError:
        return ToolResult.error(f"Permission denied: {path}")
    except Exception as e:
        return ToolResult.error(f"Error writing file: {e}")


async def _list_directory_handler(input_data: dict[str, Any]) -> ToolResult:
    """List directory tool handler."""
    path = input_data.get("path", ".")
    recursive = input_data.get("recursive", False)

    try:
        dir_path = Path(path).expanduser().resolve()
        if not dir_path.exists():
            return ToolResult.error(f"Directory not found: {path}")
        if not dir_path.is_dir():
            return ToolResult.error(f"Not a directory: {path}")

        entries = []
        if recursive:
            for entry in dir_path.rglob("*"):
                rel_path = entry.relative_to(dir_path)
                entry_type = "directory" if entry.is_dir() else "file"
                entries.append({"path": str(rel_path), "type": entry_type})
        else:
            for entry in dir_path.iterdir():
                entry_type = "directory" if entry.is_dir() else "file"
                entries.append({"name": entry.name, "type": entry_type})

        return ToolResult.json(entries)
    except PermissionError:
        return ToolResult.error(f"Permission denied: {path}")
    except Exception as e:
        return ToolResult.error(f"Error listing directory: {e}")


async def _search_files_handler(input_data: dict[str, Any]) -> ToolResult:
    """Search files tool handler."""
    path = input_data.get("path", ".")
    pattern = input_data.get("pattern", "*")

    try:
        dir_path = Path(path).expanduser().resolve()
        if not dir_path.exists():
            return ToolResult.error(f"Directory not found: {path}")

        matches = []
        for match in dir_path.rglob(pattern):
            matches.append(str(match.relative_to(dir_path)))

        return ToolResult.json({"matches": matches, "count": len(matches)})
    except Exception as e:
        return ToolResult.error(f"Error searching files: {e}")


async def _execute_command_handler(input_data: dict[str, Any]) -> ToolResult:
    """Execute command tool handler."""
    command = input_data.get("command")
    working_dir = input_data.get("working_dir")
    timeout = input_data.get("timeout", 30)

    if not command:
        return ToolResult.error("Command is required")

    try:
        cwd = Path(working_dir).expanduser().resolve() if working_dir else None

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            process.kill()
            return ToolResult.error(f"Command timed out after {timeout}s")

        result = {
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }

        if process.returncode != 0:
            return ToolResult.json(result, is_error=True)

        return ToolResult.json(result)
    except Exception as e:
        return ToolResult.error(f"Error executing command: {e}")


async def _system_info_handler(_input_data: dict[str, Any]) -> ToolResult:
    """System info tool handler."""
    try:
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "cwd": os.getcwd(),
            "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        }
        return ToolResult.json(info)
    except Exception as e:
        return ToolResult.error(f"Error getting system info: {e}")


def _create_claude_conversation_handler(claude_client: ClaudeClient) -> ToolHandlerFunc:
    """Create a Claude conversation handler with the given client."""

    async def handler(input_data: dict[str, Any]) -> ToolResult:
        """Claude conversation tool handler."""
        from tfo_mcp.domain.entities import Message
        from tfo_mcp.domain.valueobjects import Model, SystemPrompt

        message = input_data.get("message")
        system_prompt = input_data.get("system_prompt", "")
        model_name = input_data.get("model", "claude-sonnet-4-20250514")
        max_tokens = input_data.get("max_tokens", 4096)

        if not message:
            return ToolResult.error("Message is required")

        try:
            model = Model.from_string(model_name)
        except ValueError:
            model = Model.default()

        try:
            user_message = Message.user(message)
            response = await claude_client.create_message(
                messages=[user_message],
                model=model,
                system_prompt=SystemPrompt(value=system_prompt) if system_prompt else None,
                max_tokens=max_tokens,
            )
            return ToolResult.text(response.text)
        except Exception as e:
            return ToolResult.error(f"Error calling Claude API: {e}")

    return handler


# Built-in tool definitions
BUILTIN_TOOLS: list[dict[str, Any]] = [
    {
        "name": "echo",
        "description": "Echo back a message - useful for testing",
        "category": "utility",
        "tags": ["test", "debug"],
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo back",
                }
            },
            "required": ["message"],
        },
        "handler": _echo_handler,
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file",
        "category": "file",
        "tags": ["file", "read"],
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
            },
            "required": ["path"],
        },
        "handler": _read_file_handler,
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "category": "file",
        "tags": ["file", "write"],
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist",
                    "default": False,
                },
            },
            "required": ["path", "content"],
        },
        "handler": _write_file_handler,
    },
    {
        "name": "list_directory",
        "description": "List files and directories in a path",
        "category": "file",
        "tags": ["file", "directory", "list"],
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list",
                    "default": ".",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Recursively list subdirectories",
                    "default": False,
                },
            },
            "required": ["path"],
        },
        "handler": _list_directory_handler,
    },
    {
        "name": "search_files",
        "description": "Search for files matching a pattern",
        "category": "file",
        "tags": ["file", "search", "glob"],
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Base path to search in",
                    "default": ".",
                },
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '*.py', '**/*.txt')",
                },
            },
            "required": ["path", "pattern"],
        },
        "handler": _search_files_handler,
    },
    {
        "name": "execute_command",
        "description": "Execute a shell command",
        "category": "system",
        "tags": ["shell", "command", "execute"],
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for the command",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                    "default": 30,
                },
            },
            "required": ["command"],
        },
        "handler": _execute_command_handler,
    },
    {
        "name": "system_info",
        "description": "Get system information",
        "category": "system",
        "tags": ["system", "info"],
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "handler": _system_info_handler,
    },
]


def register_builtin_tools(
    session: Session,
    claude_client: ClaudeClient | None = None,
) -> None:
    """Register all built-in tools with the session."""
    for tool_def in BUILTIN_TOOLS:
        tool = Tool.create(
            name=tool_def["name"],
            description=tool_def["description"],
            input_schema=ToolInputSchema.from_dict(tool_def["input_schema"]),
            handler=tool_def["handler"],
            category=tool_def.get("category", "general"),
            tags=tool_def.get("tags", []),
        )
        session.register_tool(tool)

    # Register Claude conversation tool if client is available
    if claude_client:
        claude_tool = Tool.create(
            name="claude_conversation",
            description="Have a conversation with Claude AI",
            input_schema=ToolInputSchema.from_dict(
                {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to send to Claude",
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "Optional system prompt",
                        },
                        "model": {
                            "type": "string",
                            "description": "Claude model to use",
                            "default": "claude-sonnet-4-20250514",
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 4096,
                        },
                    },
                    "required": ["message"],
                }
            ),
            handler=_create_claude_conversation_handler(claude_client),
            category="ai",
            tags=["ai", "claude", "conversation"],
            timeout_seconds=120.0,
        )
        session.register_tool(claude_tool)
