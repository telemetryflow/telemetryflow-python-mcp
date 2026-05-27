from __future__ import annotations

import contextlib
from unittest.mock import MagicMock, patch

import pytest

from tfo_mcp.infrastructure.config import TelemetryConfig
from tfo_mcp.infrastructure.telemetry.client import (
    MCPTelemetryClient,
    get_telemetry_client,
    initialize_telemetry,
    shutdown_telemetry,
    traced,
)


@pytest.fixture(autouse=True)
def reset_global():
    import tfo_mcp.infrastructure.telemetry.client as mod

    orig = mod._telemetry_client
    mod._telemetry_client = None
    yield
    mod._telemetry_client = orig


@pytest.fixture
def disabled_config():
    return TelemetryConfig(enabled=False)


@pytest.fixture
def enabled_config():
    return TelemetryConfig(
        enabled=True,
        api_key_id="test-id",
        api_key_secret="test-secret",
        endpoint="localhost:4317",
        protocol="grpc",
        insecure=True,
        timeout=5.0,
    )


class TestMCPTelemetryClientInit:
    def test_disabled_by_config(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        assert not client._enabled
        assert not client.is_enabled

    @patch(
        "tfo_mcp.infrastructure.telemetry.client.MCPTelemetryClient._setup_client",
        side_effect=ImportError,
    )
    def test_import_error_disables(self, _mock_setup):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        assert not client._enabled

    @patch(
        "tfo_mcp.infrastructure.telemetry.client.MCPTelemetryClient._setup_client",
        side_effect=Exception("fail"),
    )
    def test_setup_exception_disables(self, _mock_setup):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        assert not client._enabled

    def test_setup_client_with_api_keys(self):
        config = TelemetryConfig(
            enabled=True,
            api_key_id="kid",
            api_key_secret="ksec",
            protocol="http",
        )
        mock_builder = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder.return_value = mock_builder_instance
        mock_builder_instance.with_api_key.return_value = mock_builder_instance
        mock_builder_instance.with_endpoint.return_value = mock_builder_instance
        mock_builder_instance.with_http.return_value = mock_builder_instance
        mock_builder_instance.with_insecure.return_value = mock_builder_instance
        mock_builder_instance.with_service.return_value = mock_builder_instance
        mock_builder_instance.with_service_namespace.return_value = mock_builder_instance
        mock_builder_instance.with_environment.return_value = mock_builder_instance
        mock_builder_instance.with_timeout.return_value = mock_builder_instance
        mock_builder_instance.with_compression.return_value = mock_builder_instance
        mock_builder_instance.with_signals.return_value = mock_builder_instance
        mock_builder_instance.with_exemplars.return_value = mock_builder_instance
        mock_builder_instance.with_batch_settings.return_value = mock_builder_instance
        mock_builder_instance.with_retry.return_value = mock_builder_instance
        mock_builder_instance.with_rate_limit.return_value = mock_builder_instance
        mock_builder_instance.with_custom_attribute.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "telemetryflow": MagicMock(TelemetryFlowBuilder=mock_builder),
                "telemetryflow.application": MagicMock(),
                "telemetryflow.application.commands": MagicMock(SpanKind=MagicMock()),
            },
        ):
            MCPTelemetryClient(config)
            mock_builder_instance.with_api_key.assert_called_once_with("kid", "ksec")

    def test_setup_client_with_auto_config(self):
        config = TelemetryConfig(enabled=True, protocol="grpc")
        mock_builder = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder.return_value = mock_builder_instance
        mock_builder_instance.with_auto_configuration.return_value = mock_builder_instance
        mock_builder_instance.with_endpoint.return_value = mock_builder_instance
        mock_builder_instance.with_grpc.return_value = mock_builder_instance
        mock_builder_instance.with_insecure.return_value = mock_builder_instance
        mock_builder_instance.with_service.return_value = mock_builder_instance
        mock_builder_instance.with_service_namespace.return_value = mock_builder_instance
        mock_builder_instance.with_environment.return_value = mock_builder_instance
        mock_builder_instance.with_timeout.return_value = mock_builder_instance
        mock_builder_instance.with_compression.return_value = mock_builder_instance
        mock_builder_instance.with_signals.return_value = mock_builder_instance
        mock_builder_instance.with_exemplars.return_value = mock_builder_instance
        mock_builder_instance.with_batch_settings.return_value = mock_builder_instance
        mock_builder_instance.with_retry.return_value = mock_builder_instance
        mock_builder_instance.with_rate_limit.return_value = mock_builder_instance
        mock_builder_instance.with_custom_attribute.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "telemetryflow": MagicMock(TelemetryFlowBuilder=mock_builder),
                "telemetryflow.application": MagicMock(),
                "telemetryflow.application.commands": MagicMock(SpanKind=MagicMock()),
            },
        ):
            MCPTelemetryClient(config)
            mock_builder_instance.with_auto_configuration.assert_called_once()


class TestInitialize:
    def test_disabled_skips(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client.initialize()
        assert not client._initialized

    def test_already_initialized_skips(self):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        client._enabled = False
        client._initialized = True
        client.initialize()
        assert client._initialized

    def test_initialize_success(self):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        client._enabled = False
        client._client = MagicMock()
        client._enabled = True
        client.initialize()
        assert client._initialized

    def test_initialize_failure(self):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._client.initialize.side_effect = Exception("fail")
        client._enabled = True
        client.initialize()
        assert not client._enabled


class TestShutdown:
    def test_disabled_skips(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client.shutdown()

    def test_not_initialized_skips(self):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        client._enabled = True
        client._initialized = False
        client.shutdown()

    def test_shutdown_success(self):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._enabled = True
        client._initialized = True
        client.shutdown()
        assert not client._initialized
        client._client.shutdown.assert_called_once()

    def test_shutdown_error(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._client.shutdown.side_effect = Exception("err")
        client._enabled = True
        client._initialized = True
        client.shutdown()
        client._client.shutdown.assert_called_once()


class TestFlush:
    def test_disabled_skips(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client.flush()

    def test_flush_success(self):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._enabled = True
        client._initialized = True
        client.flush()
        client._client.flush.assert_called_once()

    def test_flush_error(self):
        config = TelemetryConfig(enabled=True)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._client.flush.side_effect = Exception("err")
        client._enabled = True
        client._initialized = True
        client.flush()


class TestMetrics:
    def _make_enabled_client(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._enabled = True
        client._initialized = True
        return client

    def test_increment_counter(self):
        client = self._make_enabled_client()
        client.increment_counter("test.metric", value=5, attributes={"k": "v"})
        client._client.increment_counter.assert_called_once_with(
            "mcp.test.metric", value=5, attributes={"k": "v"}
        )

    def test_increment_counter_disabled(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client.increment_counter("test")

    def test_increment_counter_error(self):
        client = self._make_enabled_client()
        client._client.increment_counter.side_effect = Exception("err")
        client.increment_counter("test")

    def test_record_gauge(self):
        client = self._make_enabled_client()
        client.record_gauge("test.gauge", value=3.14)
        client._client.record_gauge.assert_called_once()

    def test_record_gauge_disabled(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client.record_gauge("test", value=1.0)

    def test_record_histogram(self):
        client = self._make_enabled_client()
        client.record_histogram("test.hist", value=0.5, unit="s")
        client._client.record_histogram.assert_called_once()

    def test_record_histogram_disabled(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client.record_histogram("test", value=1.0)


class TestLogging:
    def _make_enabled_client(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._enabled = True
        client._initialized = True
        return client

    def test_log_info(self):
        client = self._make_enabled_client()
        client.log_info("test msg", attributes={"a": "b"})
        client._client.log_info.assert_called_once()

    def test_log_warn(self):
        client = self._make_enabled_client()
        client.log_warn("warning")
        client._client.log_warn.assert_called_once()

    def test_log_error(self):
        client = self._make_enabled_client()
        client.log_error("error msg")
        client._client.log_error.assert_called_once()

    def test_log_debug(self):
        client = self._make_enabled_client()
        client.log_debug("debug msg")
        client._client.log_debug.assert_called_once()

    def test_log_disabled(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client.log_info("test")
        client.log_warn("test")
        client.log_error("test")
        client.log_debug("test")


class TestTracing:
    def _make_enabled_client(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._enabled = True
        client._initialized = True

        mock_span_kind = MagicMock()
        mock_span_kind.INTERNAL = "INTERNAL"
        mock_span_kind.SERVER = "SERVER"
        mock_span_kind.CLIENT = "CLIENT"
        mock_span_kind.PRODUCER = "PRODUCER"
        mock_span_kind.CONSUMER = "CONSUMER"
        client._SpanKind = mock_span_kind
        return client

    def test_span_yields_none_when_disabled(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        with client.span("test") as span_id:
            assert span_id is None

    def test_span_yields_id_when_enabled(self):
        client = self._make_enabled_client()
        client._client.span.return_value.__enter__ = MagicMock(return_value="span-123")
        client._client.span.return_value.__exit__ = MagicMock(return_value=False)

        with client.span("test", kind="server") as span_id:
            assert span_id == "span-123"

    def test_span_error_yields_none(self):
        client = self._make_enabled_client()
        client._client.span.side_effect = Exception("err")
        with client.span("test") as span_id:
            assert span_id is None

    def test_add_span_event_disabled(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client.add_span_event("span-1", "event")

    def test_add_span_event_none_id(self):
        client = self._make_enabled_client()
        client.add_span_event(None, "event")

    def test_add_span_event(self):
        client = self._make_enabled_client()
        client.add_span_event("span-1", "event", attributes={"k": "v"})
        client._client.add_span_event.assert_called_once()

    def test_add_span_event_error(self):
        client = self._make_enabled_client()
        client._client.add_span_event.side_effect = Exception("err")
        with contextlib.suppress(TypeError):
            client.add_span_event("span-1", "event")

    def test_get_span_kind(self):
        client = self._make_enabled_client()
        assert client._get_span_kind("server") == "SERVER"
        assert client._get_span_kind("client") == "CLIENT"
        assert client._get_span_kind("internal") == "INTERNAL"
        assert client._get_span_kind("producer") == "PRODUCER"
        assert client._get_span_kind("consumer") == "CONSUMER"
        assert client._get_span_kind("unknown") == "INTERNAL"


class TestConvenienceMethods:
    def _make_enabled_client(self):
        config = TelemetryConfig(enabled=False)
        client = MCPTelemetryClient(config)
        client._client = MagicMock()
        client._enabled = True
        client._initialized = True
        return client

    def test_record_tool_call_success(self):
        client = self._make_enabled_client()
        client.record_tool_call("echo", 0.5, success=True)
        client._client.increment_counter.assert_called()
        client._client.record_histogram.assert_called()

    def test_record_tool_call_failure(self):
        client = self._make_enabled_client()
        client.record_tool_call("echo", 0.5, success=False, error_type="TimeoutError")
        assert client._client.increment_counter.call_count >= 2

    def test_record_resource_read(self):
        client = self._make_enabled_client()
        client.record_resource_read("config://server", 0.1, success=True)
        client._client.increment_counter.assert_called()
        client._client.record_histogram.assert_called()

    def test_record_prompt_get(self):
        client = self._make_enabled_client()
        client.record_prompt_get("code_review", 0.05, success=True)
        client._client.increment_counter.assert_called()

    def test_record_session_event(self):
        client = self._make_enabled_client()
        client.record_session_event("initialized", session_id="s1")
        client._client.increment_counter.assert_called()
        client._client.log_info.assert_called()

    def test_record_session_event_no_session(self):
        client = self._make_enabled_client()
        client.record_session_event("closed")
        client._client.increment_counter.assert_called()


class TestModuleLevelFunctions:
    def test_initialize_telemetry_disabled(self):
        config = TelemetryConfig(enabled=False)
        result = initialize_telemetry(config)
        assert result is None

    def test_initialize_telemetry_enabled(self):
        config = TelemetryConfig(enabled=True)
        with patch.object(MCPTelemetryClient, "_setup_client"):
            client = MCPTelemetryClient(config)
            client._client = MagicMock()
            with (
                patch.object(MCPTelemetryClient, "initialize"),
                patch(
                    "tfo_mcp.infrastructure.telemetry.client.MCPTelemetryClient",
                    return_value=client,
                ),
            ):
                result = initialize_telemetry(config)
                assert result is not None

    def test_shutdown_telemetry(self):
        import tfo_mcp.infrastructure.telemetry.client as mod

        mock_client = MagicMock()
        mod._telemetry_client = mock_client
        shutdown_telemetry(timeout=5.0)
        mock_client.shutdown.assert_called_once_with(timeout=5.0)
        assert mod._telemetry_client is None

    def test_shutdown_telemetry_none(self):
        import tfo_mcp.infrastructure.telemetry.client as mod

        mod._telemetry_client = None
        shutdown_telemetry()

    def test_get_telemetry_client(self):
        import tfo_mcp.infrastructure.telemetry.client as mod

        assert get_telemetry_client() is None
        mock_client = MagicMock()
        mod._telemetry_client = mock_client
        assert get_telemetry_client() is mock_client


class TestTracedDecorator:
    async def test_traced_async_no_client(self):
        import tfo_mcp.infrastructure.telemetry.client as mod

        mod._telemetry_client = None

        @traced("test.op")
        async def my_func():
            return 42

        result = await my_func()
        assert result == 42

    async def test_traced_async_with_client(self):
        mock_client = MagicMock()
        mock_client.is_enabled = True
        mock_span_ctx = MagicMock()
        mock_span_ctx.__enter__ = MagicMock(return_value="span-id")
        mock_span_ctx.__exit__ = MagicMock(return_value=False)
        mock_client.span.return_value = mock_span_ctx

        import tfo_mcp.infrastructure.telemetry.client as mod

        mod._telemetry_client = mock_client

        @traced("test.op", kind="server")
        async def my_func():
            return "ok"

        result = await my_func()
        assert result == "ok"
        mock_client.span.assert_called_once_with("test.op", kind="server")

    async def test_traced_async_error(self):
        mock_client = MagicMock()
        mock_client.is_enabled = True
        mock_span_ctx = MagicMock()
        mock_span_ctx.__enter__ = MagicMock(return_value="span-id")
        mock_span_ctx.__exit__ = MagicMock(return_value=False)
        mock_client.span.return_value = mock_span_ctx

        import tfo_mcp.infrastructure.telemetry.client as mod

        mod._telemetry_client = mock_client

        @traced("test.op")
        async def my_func():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await my_func()

        mock_client.add_span_event.assert_called()

    def test_traced_sync_no_client(self):
        import tfo_mcp.infrastructure.telemetry.client as mod

        mod._telemetry_client = None

        @traced("test.sync")
        def my_func():
            return "sync-ok"

        result = my_func()
        assert result == "sync-ok"

    def test_traced_sync_with_client(self):
        mock_client = MagicMock()
        mock_client.is_enabled = True
        mock_span_ctx = MagicMock()
        mock_span_ctx.__enter__ = MagicMock(return_value="span-id")
        mock_span_ctx.__exit__ = MagicMock(return_value=False)
        mock_client.span.return_value = mock_span_ctx

        import tfo_mcp.infrastructure.telemetry.client as mod

        mod._telemetry_client = mock_client

        @traced("test.sync", kind="client")
        def my_func():
            return "sync-result"

        result = my_func()
        assert result == "sync-result"
        mock_client.span.assert_called_once()

    def test_traced_sync_error(self):
        mock_client = MagicMock()
        mock_client.is_enabled = True
        mock_span_ctx = MagicMock()
        mock_span_ctx.__enter__ = MagicMock(return_value="span-id")
        mock_span_ctx.__exit__ = MagicMock(return_value=False)
        mock_client.span.return_value = mock_span_ctx

        import tfo_mcp.infrastructure.telemetry.client as mod

        mod._telemetry_client = mock_client

        @traced("test.sync")
        def my_func():
            raise RuntimeError("err")

        with pytest.raises(RuntimeError, match="err"):
            my_func()

        mock_client.add_span_event.assert_called()
