import pytest

from tfo_mcp.domain.aggregates import Conversation, Session
from tfo_mcp.domain.entities import Resource, Tool
from tfo_mcp.domain.valueobjects import ConversationID, MimeType
from tfo_mcp.infrastructure.persistence import (
    InMemoryConversationRepository,
    InMemoryPromptRepository,
    InMemoryResourceRepository,
    InMemorySessionRepository,
    InMemoryToolRepository,
)


class TestInMemoryConversationRepositoryDeleteNonexistent:
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        repo = InMemoryConversationRepository()
        cid = ConversationID.generate()
        result = await repo.delete(cid)
        assert result is False


class TestInMemoryConversationRepositoryGetById:
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        repo = InMemoryConversationRepository()
        conv = Conversation.create()
        await repo.save(conv)
        found = await repo.get_by_id(str(conv.id))
        assert found is not None
        assert found.id == conv.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        repo = InMemoryConversationRepository()
        found = await repo.get_by_id("nonexistent")
        assert found is None


class TestInMemoryToolRepositoryListEnabled:
    @pytest.mark.asyncio
    async def test_list_enabled(self):
        repo = InMemoryToolRepository()
        t1 = Tool.create(name="enabled_tool", description="A", input_schema={"type": "object"})
        t2 = Tool.create(name="disabled_tool", description="B", input_schema={"type": "object"})
        t2.enabled = False
        await repo.save(t1)
        await repo.save(t2)
        enabled = await repo.list_enabled()
        assert len(enabled) == 1
        assert str(enabled[0].name) == "enabled_tool"


class TestInMemoryToolRepositoryListByCategory:
    @pytest.mark.asyncio
    async def test_list_by_category(self):
        repo = InMemoryToolRepository()
        t1 = Tool.create(
            name="tool_a", description="A", input_schema={"type": "object"}, category="analytics"
        )
        t2 = Tool.create(
            name="tool_b", description="B", input_schema={"type": "object"}, category="general"
        )
        await repo.save(t1)
        await repo.save(t2)
        analytics = await repo.list_by_category("analytics")
        assert len(analytics) == 1
        assert str(analytics[0].name) == "tool_a"


class TestInMemoryToolRepositoryDeleteNonexistent:
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        repo = InMemoryToolRepository()
        result = await repo.delete("nonexistent")
        assert result is False


class TestInMemoryResourceRepositoryTemplateMatch:
    @pytest.mark.asyncio
    async def test_get_template_match(self):
        repo = InMemoryResourceRepository()
        resource = Resource.template(
            uri_template="config://app/{key}",
            name="App Config",
            mime_type=MimeType.APPLICATION_JSON,
        )
        await repo.save(resource)
        found = await repo.get("config://app/theme")
        assert found is not None
        assert found.name == "App Config"

    @pytest.mark.asyncio
    async def test_get_no_match(self):
        repo = InMemoryResourceRepository()
        resource = Resource.create(uri="config://server", name="Server")
        await repo.save(resource)
        found = await repo.get("config://nonexistent")
        assert found is None


class TestInMemoryResourceRepositoryListTemplates:
    @pytest.mark.asyncio
    async def test_list_templates(self):
        repo = InMemoryResourceRepository()
        r1 = Resource.create(uri="config://a", name="A")
        r2 = Resource.template(uri_template="config://app/{key}", name="Tmpl")
        await repo.save(r1)
        await repo.save(r2)
        templates = await repo.list_templates()
        assert len(templates) == 1
        assert templates[0].name == "Tmpl"


class TestInMemoryResourceRepositoryDeleteNonexistent:
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        repo = InMemoryResourceRepository()
        result = await repo.delete("config://nonexistent")
        assert result is False


class TestInMemoryPromptRepositoryDeleteNonexistent:
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        repo = InMemoryPromptRepository()
        result = await repo.delete("nonexistent")
        assert result is False


class TestInMemorySessionRepositoryGetById:
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        repo = InMemorySessionRepository()
        session = Session.create()
        await repo.save(session)
        found = await repo.get_by_id(str(session.id))
        assert found is not None
        assert found.id == session.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        repo = InMemorySessionRepository()
        found = await repo.get_by_id("nonexistent")
        assert found is None
