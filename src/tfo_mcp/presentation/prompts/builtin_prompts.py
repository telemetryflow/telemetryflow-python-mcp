"""Built-in prompts for the MCP server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tfo_mcp.domain.entities import Prompt, PromptArgument, PromptMessage
from tfo_mcp.domain.valueobjects import Role

if TYPE_CHECKING:
    from tfo_mcp.domain.aggregates import Session


async def _code_review_generator(args: dict[str, str]) -> list[PromptMessage]:
    """Generate code review prompt messages."""
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
    """Generate code explanation prompt messages."""
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
    """Generate debugging help prompt messages."""
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


def register_builtin_prompts(session: Session) -> None:
    """Register all built-in prompts with the session."""
    # Code review prompt
    code_review = Prompt.create(
        name="code_review",
        description="Get a thorough code review with actionable feedback",
        arguments=[
            PromptArgument(
                name="code",
                description="The code to review",
                required=True,
            ),
            PromptArgument(
                name="language",
                description="Programming language of the code",
                required=False,
            ),
        ],
        generator=_code_review_generator,
    )
    session.register_prompt(code_review)

    # Explain code prompt
    explain_code = Prompt.create(
        name="explain_code",
        description="Get a detailed explanation of what code does",
        arguments=[
            PromptArgument(
                name="code",
                description="The code to explain",
                required=True,
            ),
            PromptArgument(
                name="language",
                description="Programming language of the code",
                required=False,
            ),
            PromptArgument(
                name="detail_level",
                description="Level of detail: brief, medium, or detailed",
                required=False,
            ),
        ],
        generator=_explain_code_generator,
    )
    session.register_prompt(explain_code)

    # Debug help prompt
    debug_help = Prompt.create(
        name="debug_help",
        description="Get help debugging code errors",
        arguments=[
            PromptArgument(
                name="code",
                description="The code with the bug",
                required=True,
            ),
            PromptArgument(
                name="error",
                description="The error message or description of the issue",
                required=True,
            ),
            PromptArgument(
                name="language",
                description="Programming language of the code",
                required=False,
            ),
        ],
        generator=_debug_help_generator,
    )
    session.register_prompt(debug_help)
