import pytest

from tfo_mcp.domain.aggregates.session import ClientInfo, Session, SessionCapabilities, SessionState
from tfo_mcp.domain.entities import Resource, Tool
from tfo_mcp.domain.valueobjects import MimeType


class TestClientInfoToDict:
    def test_to_dict(self):
        info = ClientInfo(name="test-client", version="2.0")
        d = info.to_dict()
        assert d == {"name": "test-client", "version": "2.0"}


class TestSessionCapabilitiesExperimental:
    def test_experimental_included(self):
        caps = SessionCapabilities(experimental={"feature_x": True})
        d = caps.to_dict()
        assert d["experimental"] == {"feature_x": True}

    def test_sampling_included(self):
        caps = SessionCapabilities(sampling=True)
        d = caps.to_dict()
        assert d["sampling"] == {}

    def test_from_dict(self):
        data = {
            "tools": {},
            "resources": {"subscribe": True},
            "prompts": {"listChanged": True},
            "logging": {},
            "sampling": {},
            "experimental": {"foo": "bar"},
        }
        caps = SessionCapabilities.from_dict(data)
        assert caps.tools is True
        assert caps.resources is True
        assert caps.prompts is True
        assert caps.logging is True
        assert caps.sampling is True
        assert caps.experimental == {"foo": "bar"}


class TestSessionUnregisterTool:
    def test_unregister_existing_tool(self):
        session = Session.create()
        tool = Tool.create(name="test_tool", description="test", input_schema={"type": "object"})
        session.register_tool(tool)
        assert session.get_tool("test_tool") is not None
        result = session.unregister_tool("test_tool")
        assert result is True
        assert session.get_tool("test_tool") is None

    def test_unregister_nonexistent_tool(self):
        session = Session.create()
        result = session.unregister_tool("no_such_tool")
        assert result is False


class TestSessionGetResourceTemplateMatch:
    @pytest.mark.asyncio
    async def test_template_match(self):
        from tfo_mcp.domain.entities.resource import Resource

        resource = Resource.template(
            uri_template="config://app/{key}",
            name="App Config",
            mime_type=MimeType.APPLICATION_JSON,
        )
        session = Session.create()
        session.register_resource(resource)
        found = session.get_resource("config://app/theme")
        assert found is resource

    def test_no_match_returns_none(self):
        session = Session.create()
        resource = Resource.create(
            uri="config://server", name="Server", mime_type=MimeType.TEXT_PLAIN
        )
        session.register_resource(resource)
        assert session.get_resource("config://nonexistent") is None


class TestSessionIsClosed:
    def test_is_closed_property(self):
        session = Session.create()
        assert session.is_closed is False
        session.close()
        assert session.is_closed is True


class TestSessionCloseIdempotent:
    def test_close_twice(self):
        session = Session.create()
        session.close()
        session.close()
        assert session.state == SessionState.CLOSED


class TestSessionToDict:
    def test_to_dict(self):
        session = Session.create()
        d = session.to_dict()
        assert "id" in d
        assert d["state"] == "created"
        assert d["clientInfo"] is None
        assert d["serverInfo"] is not None
        assert d["initializedAt"] is None
        assert d["closedAt"] is None
