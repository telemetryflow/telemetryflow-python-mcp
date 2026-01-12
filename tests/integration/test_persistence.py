"""Integration tests for persistence layer."""

import asyncio

import pytest

from tfo_mcp.domain.aggregates import Conversation, Session
from tfo_mcp.domain.aggregates.session import ClientInfo
from tfo_mcp.domain.entities import Message, Prompt, PromptArgument, Resource, Tool
from tfo_mcp.domain.valueobjects import MimeType
from tfo_mcp.infrastructure.persistence import (
    InMemoryConversationRepository,
    InMemoryPromptRepository,
    InMemoryResourceRepository,
    InMemorySessionRepository,
    InMemoryToolRepository,
)


class TestSessionPersistence:
    """Test session persistence integration."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemorySessionRepository()

    @pytest.mark.asyncio
    async def test_session_lifecycle_persistence(self, repository):
        """Test persisting session through lifecycle."""
        # Create and save
        session = Session.create(server_name="Test-MCP")
        await repository.save(session)

        # Initialize and save
        session.initialize(ClientInfo(name="test", version="1.0"))
        await repository.save(session)

        # Verify state persisted
        found = await repository.get(session.id)
        assert found.is_ready

    @pytest.mark.asyncio
    async def test_session_with_tools_persistence(self, repository):
        """Test persisting session with tools."""
        session = Session.create()
        session.initialize(ClientInfo(name="test", version="1.0"))

        # Add tools
        tools = [
            Tool.create(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={"type": "object"},
            )
            for i in range(5)
        ]
        for tool in tools:
            session.register_tool(tool)

        await repository.save(session)

        # Verify tools persisted
        found = await repository.get(session.id)
        assert len(found.list_tools()) == 5

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, repository):
        """Test managing multiple sessions."""
        sessions = []
        for i in range(10):
            session = Session.create(server_name=f"MCP-{i}")
            session.initialize(ClientInfo(name=f"client-{i}", version="1.0"))
            sessions.append(session)
            await repository.save(session)

        # Verify all saved
        all_sessions = await repository.list_all()
        assert len(all_sessions) == 10

        # Delete some
        for i in range(5):
            await repository.delete(sessions[i].id)

        remaining = await repository.list_all()
        assert len(remaining) == 5


class TestConversationPersistence:
    """Test conversation persistence integration."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemoryConversationRepository()

    @pytest.mark.asyncio
    async def test_conversation_with_messages(self, repository):
        """Test persisting conversation with messages."""
        conversation = Conversation.create()

        # Add messages
        conversation.add_message(Message.user("Hello"))
        conversation.add_message(Message.assistant("Hi!"))
        conversation.add_message(Message.user("How are you?"))

        await repository.save(conversation)

        # Verify
        found = await repository.get(conversation.id)
        assert found.message_count == 3

    @pytest.mark.asyncio
    async def test_multiple_conversations(self, repository):
        """Test multiple conversations."""
        # Create conversations
        for _ in range(5):
            conv = Conversation.create()
            await repository.save(conv)

        # Verify count
        all_convs = await repository.list_all()
        assert len(all_convs) == 5


class TestToolPersistence:
    """Test tool persistence integration."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemoryToolRepository()

    @pytest.mark.asyncio
    async def test_tool_crud(self, repository):
        """Test tool CRUD operations."""
        tool = Tool.create(
            name="echo",
            description="Echo a message",
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
        )

        # Create
        await repository.save(tool)

        # Read
        found = await repository.get(str(tool.name))
        assert found is not None
        assert str(found.description) == "Echo a message"

        # Delete
        await repository.delete(str(tool.name))
        deleted = await repository.get(str(tool.name))
        assert deleted is None

    @pytest.mark.asyncio
    async def test_tool_listing(self, repository):
        """Test listing all tools."""
        categories = ["file", "system", "ai"]

        for category in categories:
            for j in range(3):
                tool = Tool.create(
                    name=f"{category}_tool_{j}",
                    description=f"Tool {j} in {category}",
                    input_schema={"type": "object"},
                    category=category,
                )
                await repository.save(tool)

        all_tools = await repository.list_all()
        assert len(all_tools) == 9


class TestResourcePersistence:
    """Test resource persistence integration."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemoryResourceRepository()

    @pytest.mark.asyncio
    async def test_resource_crud(self, repository):
        """Test resource CRUD operations."""
        resource = Resource.create(
            uri="config://server",
            name="Server Config",
            description="Server configuration",
            mime_type=MimeType.APPLICATION_JSON,
        )

        # Create
        await repository.save(resource)

        # Read
        found = await repository.get(str(resource.uri))
        assert found is not None
        assert found.name == "Server Config"

        # Delete
        await repository.delete(str(resource.uri))
        deleted = await repository.get(str(resource.uri))
        assert deleted is None

    @pytest.mark.asyncio
    async def test_template_resources(self, repository):
        """Test template resource persistence."""
        resource = Resource.template(
            uri_template="file:///{path}",
            name="File",
            description="Read file",
            mime_type=MimeType.TEXT_PLAIN,
        )

        await repository.save(resource)

        found = await repository.get(str(resource.uri))
        assert found.is_template


class TestPromptPersistence:
    """Test prompt persistence integration."""

    @pytest.fixture
    def repository(self):
        """Create repository."""
        return InMemoryPromptRepository()

    @pytest.mark.asyncio
    async def test_prompt_crud(self, repository):
        """Test prompt CRUD operations."""
        prompt = Prompt.create(
            name="code_review",
            description="Code review assistance",
            arguments=[
                PromptArgument(
                    name="code",
                    description="Code to review",
                    required=True,
                ),
                PromptArgument(
                    name="language",
                    description="Programming language",
                    required=False,
                ),
            ],
        )

        # Create
        await repository.save(prompt)

        # Read
        found = await repository.get(str(prompt.name))
        assert found is not None
        assert len(found.arguments) == 2

        # Delete
        await repository.delete(str(prompt.name))
        deleted = await repository.get(str(prompt.name))
        assert deleted is None


class TestConcurrentOperations:
    """Test concurrent repository operations."""

    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self):
        """Test concurrent session operations."""
        repository = InMemorySessionRepository()

        async def create_and_save(i):
            session = Session.create(server_name=f"MCP-{i}")
            session.initialize(ClientInfo(name=f"client-{i}", version="1.0"))
            await repository.save(session)
            return session

        # Create 20 sessions concurrently
        await asyncio.gather(*[create_and_save(i) for i in range(20)])

        # Verify all saved
        all_sessions = await repository.list_all()
        assert len(all_sessions) == 20

    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(self):
        """Test concurrent tool operations."""
        repository = InMemoryToolRepository()

        async def create_and_save(i):
            tool = Tool.create(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={"type": "object"},
            )
            await repository.save(tool)
            return tool

        # Create 50 tools concurrently
        await asyncio.gather(*[create_and_save(i) for i in range(50)])

        all_tools = await repository.list_all()
        assert len(all_tools) == 50

    @pytest.mark.asyncio
    async def test_read_write_race(self):
        """Test read/write race conditions."""
        repository = InMemorySessionRepository()
        session = Session.create()
        await repository.save(session)

        async def update_session():
            s = await repository.get(session.id)
            if s and not s.is_ready:
                s.initialize(ClientInfo(name="test", version="1.0"))
                await repository.save(s)

        async def read_session():
            return await repository.get(session.id)

        # Run concurrent reads and writes
        tasks = [update_session() if i % 2 == 0 else read_session() for i in range(10)]
        await asyncio.gather(*tasks)

        # Final state should be consistent
        final = await repository.get(session.id)
        assert final is not None
