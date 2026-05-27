import pytest

from tfo_mcp.domain.valueobjects.content import Model, ProviderType


class TestProviderType:
    def test_anthropic_claude_prefix(self):
        assert Model.get_provider("claude-opus-4-7") == ProviderType.ANTHROPIC

    def test_anthropic_claude_underscore(self):
        assert Model.get_provider("claude_opus") == ProviderType.ANTHROPIC

    def test_google_gemini(self):
        assert Model.get_provider("gemini-2.5-pro") == ProviderType.GOOGLE

    def test_openai_gpt(self):
        assert Model.get_provider("gpt-5.5-pro") == ProviderType.OPENAI

    def test_openai_o3(self):
        assert Model.get_provider("o3") == ProviderType.OPENAI

    def test_deepseek_prefix(self):
        assert Model.get_provider("deepseek-v4-pro") == ProviderType.DEEPSEEK

    def test_deepseek_underscore(self):
        assert Model.get_provider("deepseek_v4") == ProviderType.DEEPSEEK

    def test_qwen_prefix(self):
        assert Model.get_provider("qwen3.6-max-preview") == ProviderType.QWEN

    def test_qwen3_prefix(self):
        assert Model.get_provider("qwen3:32b") == ProviderType.QWEN

    def test_ollama_colon(self):
        assert Model.get_provider("llama4:maverick-17b") == ProviderType.OLLAMA

    def test_mistral_prefix(self):
        assert Model.get_provider("mistral-medium-3-5") == ProviderType.MISTRAL

    def test_ministral_prefix(self):
        assert Model.get_provider("ministral-14b-2512") == ProviderType.MISTRAL

    def test_codestral_prefix(self):
        assert Model.get_provider("codestral-2508") == ProviderType.MISTRAL

    def test_devstral_prefix(self):
        assert Model.get_provider("devstral-2512") == ProviderType.MISTRAL

    def test_grok_prefix(self):
        assert Model.get_provider("grok-4.3") == ProviderType.GROK

    def test_kimi_prefix(self):
        assert Model.get_provider("kimi-k2.6") == ProviderType.KIMI

    def test_moonshot_prefix(self):
        assert Model.get_provider("moonshot-v1-128k") == ProviderType.KIMI

    def test_glm_prefix(self):
        assert Model.get_provider("glm-5.1") == ProviderType.ZHIPU

    def test_mimo_prefix(self):
        assert Model.get_provider("mimo-v2.5-pro") == ProviderType.MIMO

    def test_custom_prefix(self):
        assert Model.get_provider("custom-model-v1") == ProviderType.CUSTOM

    def test_unknown_returns_none(self):
        assert Model.get_provider("unknown-model-xyz") is None


class TestProviderTypeEnum:
    def test_all_providers(self):
        providers = list(ProviderType)
        assert len(providers) >= 11
        assert ProviderType.ANTHROPIC in providers
        assert ProviderType.GOOGLE in providers
        assert ProviderType.OPENAI in providers
        assert ProviderType.DEEPSEEK in providers
        assert ProviderType.QWEN in providers
        assert ProviderType.OLLAMA in providers
        assert ProviderType.MISTRAL in providers
        assert ProviderType.GROK in providers
        assert ProviderType.KIMI in providers
        assert ProviderType.ZHIPU in providers
        assert ProviderType.MIMO in providers
        assert ProviderType.CUSTOM in providers


class TestModelFromString:
    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            Model.from_string("nonexistent-model-xyz")


class TestMimeTypeFromString:
    def test_unknown_returns_octet_stream(self):
        from tfo_mcp.domain.valueobjects import MimeType

        result = MimeType.from_string("application/x-unknown")
        assert result == MimeType.APPLICATION_OCTET_STREAM


class TestSystemPrompt:
    def test_exceeds_max_length(self):
        from tfo_mcp.domain.valueobjects import SystemPrompt

        with pytest.raises(ValueError, match="cannot exceed"):
            SystemPrompt(value="x" * 100001)

    def test_empty_factory(self):
        from tfo_mcp.domain.valueobjects import SystemPrompt

        prompt = SystemPrompt.empty()
        assert prompt.value == ""
        assert prompt.is_empty
