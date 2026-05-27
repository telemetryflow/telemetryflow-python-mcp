from __future__ import annotations

from tfo_mcp.application.queries.queries import (
    GetConversationMessagesQuery,
    GetConversationQuery,
    GetPromptQuery,
    GetSessionQuery,
    GetSessionStatsQuery,
    GetToolQuery,
    ListConversationsQuery,
    ListPromptsQuery,
    ListResourcesQuery,
    ListSessionsQuery,
    ListToolsQuery,
    Query,
    ReadResourceQuery,
)


class TestQueryBase:
    def test_base_query(self):
        q = Query()
        assert isinstance(q, Query)


class TestGetSessionQuery:
    def test_create(self):
        q = GetSessionQuery(session_id="abc-123")
        assert q.session_id == "abc-123"

    def test_inherits_query(self):
        q = GetSessionQuery(session_id="x")
        assert isinstance(q, Query)


class TestListSessionsQuery:
    def test_defaults(self):
        q = ListSessionsQuery()
        assert q.limit == 100
        assert q.offset == 0

    def test_custom(self):
        q = ListSessionsQuery(limit=10, offset=5)
        assert q.limit == 10
        assert q.offset == 5


class TestGetSessionStatsQuery:
    def test_create(self):
        q = GetSessionStatsQuery(session_id="sid")
        assert q.session_id == "sid"


class TestGetConversationQuery:
    def test_create(self):
        q = GetConversationQuery(conversation_id="cid")
        assert q.conversation_id == "cid"


class TestListConversationsQuery:
    def test_defaults(self):
        q = ListConversationsQuery()
        assert q.session_id is None
        assert q.limit == 100
        assert q.offset == 0

    def test_with_session(self):
        q = ListConversationsQuery(session_id="s1", limit=50, offset=10)
        assert q.session_id == "s1"
        assert q.limit == 50
        assert q.offset == 10


class TestGetConversationMessagesQuery:
    def test_defaults(self):
        q = GetConversationMessagesQuery(conversation_id="c1")
        assert q.conversation_id == "c1"
        assert q.limit == 100
        assert q.offset == 0

    def test_custom(self):
        q = GetConversationMessagesQuery(conversation_id="c1", limit=10, offset=5)
        assert q.limit == 10


class TestGetToolQuery:
    def test_create(self):
        q = GetToolQuery(name="echo")
        assert q.name == "echo"


class TestListToolsQuery:
    def test_defaults(self):
        q = ListToolsQuery()
        assert q.category is None
        assert q.enabled_only is True
        assert q.cursor is None

    def test_custom(self):
        q = ListToolsQuery(category="utility", enabled_only=False, cursor="abc")
        assert q.category == "utility"
        assert q.enabled_only is False
        assert q.cursor == "abc"


class TestListResourcesQuery:
    def test_defaults(self):
        q = ListResourcesQuery()
        assert q.cursor is None

    def test_with_cursor(self):
        q = ListResourcesQuery(cursor="next-page")
        assert q.cursor == "next-page"


class TestReadResourceQuery:
    def test_defaults(self):
        q = ReadResourceQuery(uri="config://server")
        assert q.uri == "config://server"
        assert q.params == {}

    def test_with_params(self):
        q = ReadResourceQuery(uri="file:///test", params={"path": "/tmp"})
        assert q.params == {"path": "/tmp"}


class TestListPromptsQuery:
    def test_defaults(self):
        q = ListPromptsQuery()
        assert q.cursor is None

    def test_with_cursor(self):
        q = ListPromptsQuery(cursor="xyz")
        assert q.cursor == "xyz"


class TestGetPromptQuery:
    def test_defaults(self):
        q = GetPromptQuery(name="code_review")
        assert q.name == "code_review"
        assert q.arguments == {}

    def test_with_arguments(self):
        q = GetPromptQuery(name="code_review", arguments={"lang": "python"})
        assert q.arguments == {"lang": "python"}
