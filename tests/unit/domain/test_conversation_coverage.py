from tfo_mcp.domain.aggregates.conversation import (
    Conversation,
    ConversationSettings,
    ConversationStatus,
)
from tfo_mcp.domain.entities import Message
from tfo_mcp.domain.valueobjects import Model, Role


class TestConversationSettingsToDict:
    def test_all_optional_fields_present(self):
        settings = ConversationSettings(
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            stop_sequences=["END"],
        )
        d = settings.to_dict()
        assert d["max_tokens"] == 2048
        assert d["temperature"] == 0.7
        assert d["top_p"] == 0.9
        assert d["top_k"] == 50
        assert d["stop_sequences"] == ["END"]

    def test_no_optional_fields(self):
        settings = ConversationSettings()
        d = settings.to_dict()
        assert "top_p" not in d
        assert "top_k" not in d
        assert "stop_sequences" not in d

    def test_only_top_p(self):
        settings = ConversationSettings(top_p=0.95)
        d = settings.to_dict()
        assert d["top_p"] == 0.95
        assert "top_k" not in d

    def test_only_top_k(self):
        settings = ConversationSettings(top_k=40)
        d = settings.to_dict()
        assert d["top_k"] == 40
        assert "top_p" not in d

    def test_empty_stop_sequences(self):
        settings = ConversationSettings(stop_sequences=[])
        d = settings.to_dict()
        assert "stop_sequences" not in d


class TestConversationCreateFromString:
    def test_create_with_string_model(self):
        conv = Conversation.create(model="claude-sonnet-4-20250514")
        assert conv.model == Model.CLAUDE_SONNET_4


class TestConversationGetEvents:
    def test_get_events_clears(self):
        conv = Conversation.create()
        events1 = conv.get_events()
        assert len(events1) == 1
        events2 = conv.get_events()
        assert len(events2) == 0


class TestConversationGetMessagesForApi:
    def test_get_messages_for_api(self):
        conv = Conversation.create()
        msg = Message.user("hello")
        conv.add_message(msg)
        api_msgs = conv.get_messages_for_api()
        assert len(api_msgs) == 1
        assert api_msgs[0]["role"] == "user"


class TestConversationSetStatus:
    def test_set_status(self):
        conv = Conversation.create()
        conv.set_status(ConversationStatus.PAUSED)
        assert conv.status == ConversationStatus.PAUSED


class TestConversationTotalTokens:
    def test_total_tokens_property(self):
        conv = Conversation.create()
        msg = Message.create(role=Role.USER, text="hi")
        msg.input_tokens = 10
        msg.output_tokens = 5
        conv.add_message(msg)
        assert conv.total_tokens == 15


class TestConversationToDict:
    def test_to_dict(self):
        conv = Conversation.create(system_prompt="You are helpful.")
        d = conv.to_dict()
        assert "id" in d
        assert d["model"] == conv.model.value
        assert d["systemPrompt"] == "You are helpful."
        assert d["status"] == "active"
        assert d["totalInputTokens"] == 0
        assert d["totalOutputTokens"] == 0
