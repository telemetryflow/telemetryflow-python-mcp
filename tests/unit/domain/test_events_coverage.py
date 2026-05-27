from tfo_mcp.domain.events.events import (
    ConversationCreatedEvent,
    MessageAddedEvent,
    SessionClosedEvent,
    ToolExecutedEvent,
)


class TestSessionClosedEventToDict:
    def test_to_dict(self):
        event = SessionClosedEvent(session_id="sess-1")
        d = event.to_dict()
        assert d["sessionId"] == "sess-1"
        assert d["eventType"] == "SessionClosedEvent"


class TestConversationCreatedEventToDict:
    def test_to_dict(self):
        event = ConversationCreatedEvent(conversation_id="conv-1", model="claude-sonnet-4-20250514")
        d = event.to_dict()
        assert d["conversationId"] == "conv-1"
        assert d["model"] == "claude-sonnet-4-20250514"


class TestMessageAddedEventToDict:
    def test_to_dict(self):
        event = MessageAddedEvent(
            conversation_id="conv-1",
            message_id="msg-1",
            role="user",
        )
        d = event.to_dict()
        assert d["conversationId"] == "conv-1"
        assert d["messageId"] == "msg-1"
        assert d["role"] == "user"


class TestToolExecutedEventToDict:
    def test_to_dict_without_error(self):
        event = ToolExecutedEvent(
            session_id="sess-1",
            tool_name="echo",
            success=True,
            duration_ms=42.0,
        )
        d = event.to_dict()
        assert d["success"] is True
        assert d["durationMs"] == 42.0
        assert "errorMessage" not in d

    def test_to_dict_with_error(self):
        event = ToolExecutedEvent(
            session_id="sess-1",
            tool_name="bad_tool",
            success=False,
            duration_ms=10.0,
            error_message="Something failed",
        )
        d = event.to_dict()
        assert d["success"] is False
        assert d["errorMessage"] == "Something failed"
