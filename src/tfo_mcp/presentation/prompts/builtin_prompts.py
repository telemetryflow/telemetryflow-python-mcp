"""Built-in prompts for the MCP server.

TelemetryFlow Python MCP Server - Community Enterprise Observability Platform
Copyright (c) 2024-2026 Telemetri Data Indonesia. All rights reserved.
Open Source Software built by Telemetri Data Indonesia.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import mcp.types as types

from tfo_mcp.domain.entities import PromptMessage
from tfo_mcp.domain.valueobjects import Role

if TYPE_CHECKING:
    from tfo_mcp.presentation.server import MCPServer


async def _code_review_generator(args: dict[str, str]) -> list[PromptMessage]:
    code = args.get("code", "")
    language = args.get("language", "")

    system_message = PromptMessage(
        role=Role.USER,
        content=f"""Please review the following {language} code and provide feedback on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement

Code to review:
```{language}
{code}
```

Please provide a thorough code review with specific recommendations.""",
    )

    return [system_message]


async def _explain_code_generator(args: dict[str, str]) -> list[PromptMessage]:
    code = args.get("code", "")
    language = args.get("language", "")
    detail_level = args.get("detail_level", "medium")

    detail_instructions = {
        "brief": "Provide a brief, high-level explanation.",
        "medium": "Provide a balanced explanation with key details.",
        "detailed": "Provide a comprehensive, in-depth explanation.",
    }

    message = PromptMessage(
        role=Role.USER,
        content=f"""Please explain the following {language} code.

{detail_instructions.get(detail_level, detail_instructions["medium"])}

Code to explain:
```{language}
{code}
```

Include:
- What the code does overall
- Key functions and their purposes
- Important data structures
- Any notable patterns or techniques used""",
    )

    return [message]


async def _debug_help_generator(args: dict[str, str]) -> list[PromptMessage]:
    code = args.get("code", "")
    error = args.get("error", "")
    language = args.get("language", "")

    message = PromptMessage(
        role=Role.USER,
        content=f"""I need help debugging this {language} code.

The code:
```{language}
{code}
```

The error/issue:
{error}

Please help me:
1. Understand what's causing the error
2. Identify the root cause
3. Suggest a fix with explanation
4. Recommend any preventive measures for similar issues""",
    )

    return [message]


def register_builtin_prompts(server: MCPServer) -> None:
    """Register all built-in prompts with the MCP server."""
    server.register_prompt(
        name="code_review",
        description="Get a thorough code review with actionable feedback",
        arguments=[
            types.PromptArgument(
                name="code",
                description="The code to review",
                required=True,
            ),
            types.PromptArgument(
                name="language",
                description="Programming language of the code",
                required=False,
            ),
        ],
        generator=_code_review_generator,
    )

    server.register_prompt(
        name="explain_code",
        description="Get a detailed explanation of what code does",
        arguments=[
            types.PromptArgument(
                name="code",
                description="The code to explain",
                required=True,
            ),
            types.PromptArgument(
                name="language",
                description="Programming language of the code",
                required=False,
            ),
            types.PromptArgument(
                name="detail_level",
                description="Level of detail: brief, medium, or detailed",
                required=False,
            ),
        ],
        generator=_explain_code_generator,
    )

    server.register_prompt(
        name="debug_help",
        description="Get help debugging code errors",
        arguments=[
            types.PromptArgument(
                name="code",
                description="The code with the bug",
                required=True,
            ),
            types.PromptArgument(
                name="error",
                description="The error message or description of the issue",
                required=True,
            ),
            types.PromptArgument(
                name="language",
                description="Programming language of the code",
                required=False,
            ),
        ],
        generator=_debug_help_generator,
    )
