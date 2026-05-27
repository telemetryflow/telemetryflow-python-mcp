import pytest

from tfo_mcp.domain.entities.resource import Resource, ResourceContent
from tfo_mcp.domain.valueobjects import MimeType


class TestResourceContentBlob:
    def test_blob_encoding(self):
        rc = ResourceContent(
            uri="file:///test.bin",
            mime_type=MimeType.APPLICATION_OCTET_STREAM,
            blob=b"\x00\x01\x02",
        )
        d = rc.to_dict()
        import base64

        assert d["blob"] == base64.b64encode(b"\x00\x01\x02").decode("utf-8")

    def test_text_and_blob_none(self):
        rc = ResourceContent(uri="file:///test.txt", mime_type=MimeType.TEXT_PLAIN)
        d = rc.to_dict()
        assert "text" not in d
        assert "blob" not in d


class TestResourceReadNoReader:
    @pytest.mark.asyncio
    async def test_read_without_reader(self):
        resource = Resource.create(uri="config://test", name="Test", mime_type=MimeType.TEXT_PLAIN)
        content = await resource.read()
        assert "No reader configured" in content.text


class TestResourceReadWithReader:
    @pytest.mark.asyncio
    async def test_read_with_reader(self):
        async def mock_reader(uri, _params):
            return ResourceContent(
                uri=uri, mime_type=MimeType.APPLICATION_JSON, text='{"ok": true}'
            )

        resource = Resource.create(uri="config://data", name="Data", reader=mock_reader)
        content = await resource.read()
        assert content.text == '{"ok": true}'


class TestResourceMatchesUriNonTemplate:
    def test_non_template_exact_match(self):
        resource = Resource.create(uri="config://server", name="Server")
        assert resource.matches_uri("config://server") is True

    def test_non_template_no_match(self):
        resource = Resource.create(uri="config://server", name="Server")
        assert resource.matches_uri("config://other") is False


class TestResourceToTemplateFormat:
    def test_non_template_returns_none(self):
        resource = Resource.create(uri="config://server", name="Server")
        assert resource.to_template_format() is None

    def test_template_with_description(self):
        resource = Resource.template(
            uri_template="config://app/{key}",
            name="App Config",
            description="Application configuration",
        )
        result = resource.to_template_format()
        assert result is not None
        assert result["uriTemplate"] == "config://app/{key}"
        assert result["description"] == "Application configuration"

    def test_template_without_description(self):
        resource = Resource.template(uri_template="config://app/{key}", name="App Config")
        result = resource.to_template_format()
        assert result is not None
        assert "description" not in result


class TestResourceToDict:
    def test_to_dict(self):
        resource = Resource.create(
            uri="config://server",
            name="Server",
            description="Server config",
            mime_type=MimeType.APPLICATION_JSON,
        )
        d = resource.to_dict()
        assert d["uri"] == "config://server"
        assert d["name"] == "Server"
        assert d["description"] == "Server config"
        assert d["isTemplate"] is False
        assert d["uriTemplate"] is None
