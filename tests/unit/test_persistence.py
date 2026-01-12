"""Unit tests for persistence layer."""

import pytest

from tfo_mcp.domain.aggregates import Conversation, Session
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.entities import Prompt, PromptArgument, Resource, Tool
from tfo_mcp.domain.valueobjects import MimeType, SessionID
from tfo_mcp.infrastructure.persistence import (
    InMemoryConversationRepository,
    InMemoryPromptRepository,
    InMemoryResourceRepository,
    InMemorySessionRepository,
    InMemoryToolRepository,
)


class TestInMemorySessionRepository:
    """Test InMemorySessionRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemorySessionRepository()

    @pytest.fixture
    def session(self):
        """Create test session."""
        return Session.create(
            server_name="Test-MCP",
            server_version="1.0.0",
        )

    @pytest.mark.asyncio
    async def test_save_and_find(self, repository, session):
        """Test saving and finding a session."""
        await repository.save(session)

        found = await repository.get(session.id)
        assert found is not None
        assert found.id == session.id

    @pytest.mark.asyncio
    async def test_find_nonexistent(self, repository):
        """Test finding nonexistent session."""
        session_id = SessionID.generate()
        found = await repository.get(session_id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete(self, repository, session):
        """Test deleting a session."""
        await repository.save(session)
        assert await repository.get(session.id) is not None

        deleted = await repository.delete(session.id)
        assert deleted is True
        assert await repository.get(session.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, repository):
        """Test deleting nonexistent session."""
        session_id = SessionID.generate()
        deleted = await repository.delete(session_id)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_all(self, repository):
        """Test listing all sessions."""
        sessions = [
            Session.create(server_name="MCP-1"),
            Session.create(server_name="MCP-2"),
            Session.create(server_name="MCP-3"),
        ]

        for session in sessions:
            await repository.save(session)

        all_sessions = await repository.list_all()
        assert len(all_sessions) == 3

    @pytest.mark.asyncio
    async def test_update_session(self, repository, session):
        """Test updating a session."""
        await repository.save(session)

        # Initialize and save again
        client = ClientInfo(name="test", version="1.0")
        session.initialize(client)
        await repository.save(session)

        found = await repository.get(session.id)
        assert found.is_ready


class TestInMemoryConversationRepository:
    """Test InMemoryConversationRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemoryConversationRepository()

    @pytest.fixture
    def conversation(self):
        """Create test conversation."""
        return Conversation.create()

    @pytest.mark.asyncio
    async def test_save_and_find(self, repository, conversation):
        """Test saving and finding a conversation."""
        await repository.save(conversation)

        found = await repository.get(conversation.id)
        assert found is not None
        assert found.id == conversation.id

    @pytest.mark.asyncio
    async def test_list_all(self, repository):
        """Test listing all conversations."""
        convs = [
            Conversation.create(),
            Conversation.create(),
            Conversation.create(),
        ]

        for conv in convs:
            await repository.save(conv)

        all_convs = await repository.list_all()
        assert len(all_convs) == 3

    @pytest.mark.asyncio
    async def test_delete(self, repository, conversation):
        """Test deleting a conversation."""
        await repository.save(conversation)
        deleted = await repository.delete(conversation.id)

        assert deleted is True
        assert await repository.get(conversation.id) is None


class TestInMemoryToolRepository:
    """Test InMemoryToolRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemoryToolRepository()

    @pytest.fixture
    def tool(self):
        """Create test tool."""
        return Tool.create(
            name="echo",
            description="Echo a message",
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
        )

    @pytest.mark.asyncio
    async def test_save_and_find(self, repository, tool):
        """Test saving and finding a tool."""
        await repository.save(tool)

        found = await repository.get(str(tool.name))
        assert found is not None
        assert found.name == tool.name

    @pytest.mark.asyncio
    async def test_find_all(self, repository):
        """Test finding all tools."""
        tools = [
            Tool.create(name="tool_a", description="A", input_schema={"type": "object"}),
            Tool.create(name="tool_b", description="B", input_schema={"type": "object"}),
        ]

        for tool in tools:
            await repository.save(tool)

        all_tools = await repository.list_all()
        assert len(all_tools) == 2

    @pytest.mark.asyncio
    async def test_delete(self, repository, tool):
        """Test deleting a tool."""
        await repository.save(tool)
        deleted = await repository.delete(str(tool.name))

        assert deleted is True
        assert await repository.get(str(tool.name)) is None


class TestInMemoryResourceRepository:
    """Test InMemoryResourceRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemoryResourceRepository()

    @pytest.fixture
    def resource(self):
        """Create test resource."""
        return Resource.create(
            uri="config://server",
            name="Server Config",
            description="Server configuration",
            mime_type=MimeType.APPLICATION_JSON,
        )

    @pytest.mark.asyncio
    async def test_save_and_find(self, repository, resource):
        """Test saving and finding a resource."""
        await repository.save(resource)

        found = await repository.get(str(resource.uri))
        assert found is not None
        assert found.uri == resource.uri

    @pytest.mark.asyncio
    async def test_find_all(self, repository):
        """Test finding all resources."""
        resources = [
            Resource.create(
                uri="config://a",
                name="A",
                description="A",
                mime_type=MimeType.APPLICATION_JSON,
            ),
            Resource.create(
                uri="config://b",
                name="B",
                description="B",
                mime_type=MimeType.APPLICATION_JSON,
            ),
        ]

        for resource in resources:
            await repository.save(resource)

        all_resources = await repository.list_all()
        assert len(all_resources) == 2

    @pytest.mark.asyncio
    async def test_delete(self, repository, resource):
        """Test deleting a resource."""
        await repository.save(resource)
        deleted = await repository.delete(str(resource.uri))

        assert deleted is True
        assert await repository.get(str(resource.uri)) is None


class TestInMemoryPromptRepository:
    """Test InMemoryPromptRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemoryPromptRepository()

    @pytest.fixture
    def prompt(self):
        """Create test prompt."""
        return Prompt.create(
            name="code_review",
            description="Code review assistance",
            arguments=[
                PromptArgument(
                    name="code",
                    description="Code to review",
                    required=True,
                ),
            ],
        )

    @pytest.mark.asyncio
    async def test_save_and_find(self, repository, prompt):
        """Test saving and finding a prompt."""
        await repository.save(prompt)

        found = await repository.get(str(prompt.name))
        assert found is not None
        assert found.name == prompt.name

    @pytest.mark.asyncio
    async def test_find_all(self, repository):
        """Test finding all prompts."""
        prompts = [
            Prompt.create(name="prompt_a", description="A", arguments=[]),
            Prompt.create(name="prompt_b", description="B", arguments=[]),
        ]

        for prompt in prompts:
            await repository.save(prompt)

        all_prompts = await repository.list_all()
        assert len(all_prompts) == 2

    @pytest.mark.asyncio
    async def test_delete(self, repository, prompt):
        """Test deleting a prompt."""
        await repository.save(prompt)
        deleted = await repository.delete(str(prompt.name))

        assert deleted is True
        assert await repository.get(str(prompt.name)) is None


class TestRepositoryConcurrency:
    """Test repository concurrency handling."""

    @pytest.mark.asyncio
    async def test_concurrent_session_saves(self):
        """Test concurrent session saves."""
        import asyncio

        repository = InMemorySessionRepository()
        sessions = [Session.create() for _ in range(10)]

        await asyncio.gather(*[repository.save(s) for s in sessions])

        all_sessions = await repository.list_all()
        assert len(all_sessions) == 10

    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(self):
        """Test concurrent tool operations."""
        import asyncio

        repository = InMemoryToolRepository()
        tools = [
            Tool.create(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={"type": "object"},
            )
            for i in range(10)
        ]

        await asyncio.gather(*[repository.save(t) for t in tools])

        all_tools = await repository.list_all()
        assert len(all_tools) == 10
