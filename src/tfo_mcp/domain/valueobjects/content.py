"""Content-related value objects.

TelemetryFlow Python MCP Server - Community Enterprise Observability Platform
Copyright (c) 2024-2026 Telemetri Data Indonesia. All rights reserved.
Open Source Software built by Telemetri Data Indonesia.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class Role(StrEnum):
    """Message role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ProviderType(StrEnum):
    """LLM provider types."""

    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OLLAMA = "ollama"
    MISTRAL = "mistral"
    GROK = "grok"
    KIMI = "kimi"
    ZHIPU = "zhipu"
    MIMO = "mimo"
    CUSTOM = "custom"


class Model(StrEnum):
    """LLM models from TelemetryFlow Platform seed data."""

    # Anthropic Claude (11 models)
    CLAUDE_OPUS_4_7 = "claude-opus-4-7"
    CLAUDE_OPUS_4_7_FAST = "claude-opus-4-7-fast"
    CLAUDE_OPUS_4_6 = "claude-opus-4-6"
    CLAUDE_OPUS_4_6_FAST = "claude-opus-4-6-fast"
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_OPUS_4_5 = "claude-opus-4-5"
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-5-20250929"
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5"
    CLAUDE_HAIKU_4_5_OCT = "claude-haiku-4-5-20251001"
    CLAUDE_SONNET_4 = "claude-sonnet-4-20250514"
    CLAUDE_MYTHOS_PREVIEW = "claude-mythos-preview"

    # Google Gemini (10 models)
    GEMINI_3_5_FLASH = "gemini-3.5-flash"
    GEMINI_3_1_FLASH_LITE = "gemini-3.1-flash-lite"
    GEMINI_3_1_PRO_PREVIEW = "gemini-3.1-pro-preview"
    GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_1_5_PRO = "gemini-1.5-pro"

    # OpenAI (10 models)
    GPT_5_5_PRO = "gpt-5.5-pro"
    GPT_5_5 = "gpt-5.5"
    GPT_5_4_PRO = "gpt-5.4-pro"
    GPT_5_4 = "gpt-5.4"
    GPT_5_4_MINI = "gpt-5.4-mini"
    GPT_5_4_NANO = "gpt-5.4-nano"
    GPT_5_3_CHAT = "gpt-5.3-chat"
    GPT_5 = "gpt-5"
    GPT_4_1 = "gpt-4.1"
    O3 = "o3"

    # DeepSeek (10 models)
    DEEPSEEK_V4_PRO = "deepseek-v4-pro"
    DEEPSEEK_V4_FLASH = "deepseek-v4-flash"
    DEEPSEEK_V3_2_SPECIALE = "deepseek-v3.2-speciale"
    DEEPSEEK_CHAT = "deepseek-chat"
    DEEPSEEK_V3_2 = "deepseek-v3.2"
    DEEPSEEK_V3_2_EXP = "deepseek-v3.2-exp"
    DEEPSEEK_V3_1_TERMINUS = "deepseek-v3.1-terminus"
    DEEPSEEK_CHAT_V3_1 = "deepseek-chat-v3.1"
    DEEPSEEK_R1_0528 = "deepseek-r1-0528"
    DEEPSEEK_REASONER = "deepseek-reasoner"

    # Alibaba Qwen (10 models)
    QWEN3_6_MAX_PREVIEW = "qwen3.6-max-preview"
    QWEN3_6_PLUS = "qwen3.6-plus"
    QWEN3_6_FLASH = "qwen3.6-flash"
    QWEN3_6_35B_A3B = "qwen3.6-35b-a3b"
    QWEN3_6_27B = "qwen3.6-27b"
    QWEN3_5_PLUS = "qwen3.5-plus"
    QWEN3_5_9B = "qwen3.5-9b"
    QWEN3_5_35B_A3B = "qwen3.5-35b-a3b"
    QWEN3_5_27B = "qwen3.5-27b"
    QWEN3_5_122B_A10B = "qwen3.5-122b-a10b"

    # Ollama (10 models)
    OLLAMA_QWEN3_6_FLASH = "qwen3.6:flash"
    OLLAMA_QWEN3_5_PLUS = "qwen3.5:plus"
    OLLAMA_LLAMA4_MAVERICK = "llama4:maverick-17b"
    OLLAMA_GEMMA4_26B = "gemma4:26b"
    OLLAMA_MISTRAL_SMALL_2603 = "mistral-small:2603"
    OLLAMA_QWEN3_32B = "qwen3:32b"
    OLLAMA_DEEPSEEK_R1_70B = "deepseek-r1:70b"
    OLLAMA_GRANITE_4_1_8B = "granite:4.1-8b"
    OLLAMA_LLAMA3_3_70B = "llama3.3:70b"
    OLLAMA_PHI4_14B = "phi4:14b"

    # Mistral AI (10 models)
    MISTRAL_MEDIUM_3_5 = "mistral-medium-3-5"
    MISTRAL_SMALL_2603 = "mistral-small-2603"
    MISTRAL_LARGE_2512 = "mistral-large-2512"
    DEVSTRAL_2512 = "devstral-2512"
    MINISTRAL_14B_2512 = "ministral-14b-2512"
    MINISTRAL_8B_2512 = "ministral-8b-2512"
    MINISTRAL_3B_2512 = "ministral-3b-2512"
    MISTRAL_MEDIUM_2508 = "mistral-medium-2508"
    CODESTRAL_2508 = "codestral-2508"
    MISTRAL_LARGE_2411 = "mistral-large-2411"

    # xAI Grok (10 models)
    GROK_4_3 = "grok-4.3"
    GROK_4_20_MULTI_AGENT = "grok-4.20-multi-agent"
    GROK_4_20_REASONING = "grok-4.20-0309-reasoning"
    GROK_4_20_NON_REASONING = "grok-4.20-0309-non-reasoning"
    GROK_4_1_FAST_REASONING = "grok-4-1-fast-reasoning"
    GROK_4_1_FAST_NON_REASONING = "grok-4-1-fast-non-reasoning"
    GROK_3 = "grok-3"
    GROK_3_MINI = "grok-3-mini"
    GROK_2 = "grok-2"
    GROK_2_MINI = "grok-2-mini"

    # Kimi / Moonshot (10 models)
    KIMI_K2_6 = "kimi-k2.6"
    KIMI_K2_5 = "kimi-k2.5"
    KIMI_K2_THINKING = "kimi-k2-thinking"
    KIMI_K2_0905 = "kimi-k2-0905"
    KIMI_K2_TURBO_PREVIEW = "kimi-k2-turbo-preview"
    KIMI_K2 = "kimi-k2"
    MOONSHOT_V1_128K = "moonshot-v1-128k"
    MOONSHOT_V1_32K = "moonshot-v1-32k"
    MOONSHOT_V1_8K = "moonshot-v1-8k"
    MOONSHOT_V1_AUTO = "moonshot-v1-auto"

    # Zhipu GLM (10 models)
    GLM_5_1 = "glm-5.1"
    GLM_5_TURBO = "glm-5-turbo"
    GLM_5 = "glm-5"
    GLM_4_7_FLASH = "glm-4.7-flash"
    GLM_4_7 = "glm-4.7"
    GLM_4_6 = "glm-4.6"
    GLM_4_5 = "glm-4.5"
    GLM_4_5_AIR = "glm-4.5-air"
    GLM_4_FLASH = "glm-4-flash"
    GLM_4 = "glm-4"

    # Xiaomi MiMo (10 models)
    MIMO_V2_5_PRO = "mimo-v2.5-pro"
    MIMO_V2_5 = "mimo-v2.5"
    MIMO_V2_OMNI = "mimo-v2-omni"
    MIMO_V2_PRO = "mimo-v2-pro"
    MIMO_V2_FLASH = "mimo-v2-flash"
    MIMO_V2_TTS = "mimo-v2-tts"
    MIMO_7B = "mimo-7b"
    MIMO_VL_7B = "mimo-vl-7b"
    MIMO_V2_5_LITE = "mimo-v2.5-lite"
    MIMO_7B_0321 = "mimo-7b-0321"

    # Custom
    CUSTOM_MODEL_V1 = "custom-model-v1"

    @classmethod
    def default(cls) -> Model:
        """Get the default model."""
        return cls.CLAUDE_SONNET_4

    @classmethod
    def from_string(cls, value: str) -> Model:
        """Create model from string value."""
        for model in cls:
            if model.value == value:
                return model
        raise ValueError(f"Unknown model: {value}")

    @classmethod
    def get_provider(cls, model_id: str) -> ProviderType | None:
        """Get provider type for a model ID."""
        if model_id.startswith("claude-") or model_id.startswith("claude_"):
            return ProviderType.ANTHROPIC
        if model_id.startswith("gemini-"):
            return ProviderType.GOOGLE
        if model_id.startswith("gpt-") or model_id == "o3":
            return ProviderType.OPENAI
        if model_id.startswith("deepseek-") or model_id.startswith("deepseek_"):
            return ProviderType.DEEPSEEK
        if model_id.startswith("qwen") or model_id.startswith("qwen3"):
            return ProviderType.QWEN
        if ":" in model_id:
            return ProviderType.OLLAMA
        if (
            model_id.startswith("mistral-")
            or model_id.startswith("ministral-")
            or model_id.startswith("codestral-")
            or model_id.startswith("devstral-")
        ):
            return ProviderType.MISTRAL
        if model_id.startswith("grok-"):
            return ProviderType.GROK
        if model_id.startswith("kimi-") or model_id.startswith("moonshot-"):
            return ProviderType.KIMI
        if model_id.startswith("glm-"):
            return ProviderType.ZHIPU
        if model_id.startswith("mimo-"):
            return ProviderType.MIMO
        if model_id.startswith("custom-"):
            return ProviderType.CUSTOM
        return None


class ContentType(StrEnum):
    """Content block types."""

    TEXT = "text"
    IMAGE = "image"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class MimeType(StrEnum):
    """Common MIME types."""

    # Text types
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_CSS = "text/css"
    TEXT_JAVASCRIPT = "text/javascript"
    TEXT_MARKDOWN = "text/markdown"
    TEXT_CSV = "text/csv"

    # Application types
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"
    APPLICATION_YAML = "application/yaml"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
    APPLICATION_PDF = "application/pdf"

    # Image types
    IMAGE_PNG = "image/png"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_GIF = "image/gif"
    IMAGE_WEBP = "image/webp"
    IMAGE_SVG = "image/svg+xml"

    @classmethod
    def from_extension(cls, ext: str) -> MimeType:
        """Get MIME type from file extension."""
        ext = ext.lower().lstrip(".")
        extension_map = {
            "txt": cls.TEXT_PLAIN,
            "html": cls.TEXT_HTML,
            "htm": cls.TEXT_HTML,
            "css": cls.TEXT_CSS,
            "js": cls.TEXT_JAVASCRIPT,
            "mjs": cls.TEXT_JAVASCRIPT,
            "md": cls.TEXT_MARKDOWN,
            "markdown": cls.TEXT_MARKDOWN,
            "csv": cls.TEXT_CSV,
            "json": cls.APPLICATION_JSON,
            "xml": cls.APPLICATION_XML,
            "yaml": cls.APPLICATION_YAML,
            "yml": cls.APPLICATION_YAML,
            "pdf": cls.APPLICATION_PDF,
            "png": cls.IMAGE_PNG,
            "jpg": cls.IMAGE_JPEG,
            "jpeg": cls.IMAGE_JPEG,
            "gif": cls.IMAGE_GIF,
            "webp": cls.IMAGE_WEBP,
            "svg": cls.IMAGE_SVG,
        }
        return extension_map.get(ext, cls.APPLICATION_OCTET_STREAM)

    @classmethod
    def from_string(cls, value: str) -> MimeType:
        """Create from string value."""
        for mime_type in cls:
            if mime_type.value == value:
                return mime_type
        return cls.APPLICATION_OCTET_STREAM


@dataclass(frozen=True, slots=True)
class SystemPrompt:
    """System prompt value object."""

    value: str

    MAX_LENGTH = 100000

    def __post_init__(self) -> None:
        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(f"SystemPrompt cannot exceed {self.MAX_LENGTH} characters")

    @classmethod
    def empty(cls) -> Self:
        """Create an empty system prompt."""
        return cls(value="")

    @property
    def is_empty(self) -> bool:
        """Check if the system prompt is empty."""
        return not self.value.strip()

    def __str__(self) -> str:
        return self.value

    def __bool__(self) -> bool:
        return not self.is_empty
