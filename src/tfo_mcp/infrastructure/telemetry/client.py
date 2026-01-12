"""TelemetryFlow SDK integration for MCP Server.

This module provides a thin wrapper around the TelemetryFlow Python SDK,
optimized for use within the TelemetryFlow MCP Server. It provides:

- Automatic client initialization from MCP configuration
- MCP-specific metrics and span names
- Thread-safe singleton pattern
- Graceful degradation when telemetry is disabled
"""

from __future__ import annotations

import functools
import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypeVar

import structlog

if TYPE_CHECKING:
    from tfo_mcp.infrastructure.config import TelemetryConfig

logger = structlog.get_logger(__name__)

# Global telemetry client singleton
_telemetry_client: MCPTelemetryClient | None = None
_telemetry_lock = threading.Lock()

# Type variable for decorators
F = TypeVar("F", bound=Callable[..., Any])


class MCPTelemetryClient:
    """MCP-specific telemetry client wrapper.

    Wraps the TelemetryFlow Python SDK with MCP-specific functionality:
    - Automatic span naming with mcp.* prefix
    - Built-in metrics for tool calls, resource reads, etc.
    - Request context propagation
    """

    def __init__(self, config: TelemetryConfig) -> None:
        """Initialize the MCP telemetry client.

        Args:
            config: TelemetryConfig from MCP server configuration.
        """
        self._config = config
        self._client: Any = None
        self._enabled = config.enabled
        self._initialized = False

        # Import here to allow optional dependency
        if self._enabled:
            try:
                self._setup_client()
            except ImportError:
                logger.warning(
                    "TelemetryFlow SDK not installed, telemetry disabled. "
                    "Install with: pip install tfo-mcp[telemetry]"
                )
                self._enabled = False
            except Exception as e:
                logger.error("Failed to initialize telemetry client", error=str(e))
                self._enabled = False

    def _setup_client(self) -> None:
        """Set up the TelemetryFlow client from configuration."""
        from telemetryflow import TelemetryFlowBuilder
        from telemetryflow.application.commands import SpanKind

        self._SpanKind = SpanKind

        builder = TelemetryFlowBuilder()

        # Set API credentials
        if self._config.api_key_id and self._config.api_key_secret:
            builder.with_api_key(self._config.api_key_id, self._config.api_key_secret)
        else:
            # Try auto-configuration from environment
            builder.with_auto_configuration()

        # Set endpoint and protocol
        builder.with_endpoint(self._config.endpoint)
        if self._config.protocol.lower() == "http":
            builder.with_http()
        else:
            builder.with_grpc()

        builder.with_insecure(self._config.insecure)

        # Set service information
        builder.with_service(
            self._config.service_name,
            self._config.service_version,
        )
        builder.with_service_namespace(self._config.service_namespace)
        builder.with_environment(self._config.environment)

        # Set connection settings
        builder.with_timeout(timedelta(seconds=self._config.timeout))
        builder.with_compression(self._config.compression)

        # Set signal configuration
        builder.with_signals(
            metrics=self._config.enable_metrics,
            logs=self._config.enable_logs,
            traces=self._config.enable_traces,
        )
        builder.with_exemplars(self._config.enable_exemplars)

        # Set batch settings
        builder.with_batch_settings(
            timeout=timedelta(milliseconds=self._config.batch_timeout_ms),
            max_size=self._config.batch_max_size,
        )

        # Set retry settings
        builder.with_retry(
            enabled=self._config.retry_enabled,
            max_retries=self._config.max_retries,
            backoff=timedelta(milliseconds=self._config.retry_backoff_ms),
        )

        # Set rate limit
        builder.with_rate_limit(self._config.rate_limit)

        # Add custom attributes for MCP context
        builder.with_custom_attribute("mcp.server", "telemetryflow-python-mcp")
        builder.with_custom_attribute("mcp.protocol", "2024-11-05")

        # Build client
        self._client = builder.build()

    def initialize(self) -> None:
        """Initialize the telemetry client.

        Must be called before using any telemetry methods.
        """
        if not self._enabled or self._initialized:
            return

        try:
            self._client.initialize()
            self._initialized = True
            logger.info(
                "Telemetry client initialized",
                service=self._config.service_name,
                endpoint=self._config.endpoint,
                protocol=self._config.protocol,
            )
        except Exception as e:
            logger.error("Failed to initialize telemetry client", error=str(e))
            self._enabled = False

    def shutdown(self, timeout: float = 30.0) -> None:
        """Shutdown the telemetry client.

        Args:
            timeout: Maximum time to wait for pending telemetry to flush.
        """
        if not self._enabled or not self._initialized:
            return

        try:
            self._client.shutdown(timeout=timeout)
            self._initialized = False
            logger.info("Telemetry client shutdown complete")
        except Exception as e:
            logger.error("Error during telemetry shutdown", error=str(e))

    def flush(self) -> None:
        """Flush any pending telemetry data."""
        if not self._enabled or not self._initialized:
            return

        try:
            self._client.flush()
        except Exception as e:
            logger.error("Error flushing telemetry", error=str(e))

    @property
    def is_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return self._enabled and self._initialized

    # -------------------------------------------------------------------------
    # Metrics API
    # -------------------------------------------------------------------------

    def increment_counter(
        self,
        name: str,
        value: int = 1,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Metric name (will be prefixed with mcp.).
            value: Value to increment by.
            attributes: Additional metric attributes.
        """
        if not self.is_enabled:
            return

        try:
            self._client.increment_counter(
                f"mcp.{name}",
                value=value,
                attributes=attributes or {},
            )
        except Exception as e:
            logger.debug("Failed to record metric", name=name, error=str(e))

    def record_gauge(
        self,
        name: str,
        value: float,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record a gauge metric.

        Args:
            name: Metric name (will be prefixed with mcp.).
            value: Gauge value.
            attributes: Additional metric attributes.
        """
        if not self.is_enabled:
            return

        try:
            self._client.record_gauge(
                f"mcp.{name}",
                value=value,
                attributes=attributes or {},
            )
        except Exception as e:
            logger.debug("Failed to record gauge", name=name, error=str(e))

    def record_histogram(
        self,
        name: str,
        value: float,
        unit: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record a histogram metric.

        Args:
            name: Metric name (will be prefixed with mcp.).
            value: Histogram value.
            unit: Unit of measurement.
            attributes: Additional metric attributes.
        """
        if not self.is_enabled:
            return

        try:
            self._client.record_histogram(
                f"mcp.{name}",
                value=value,
                unit=unit,
                attributes=attributes or {},
            )
        except Exception as e:
            logger.debug("Failed to record histogram", name=name, error=str(e))

    # -------------------------------------------------------------------------
    # Logging API
    # -------------------------------------------------------------------------

    def log_info(self, message: str, attributes: dict[str, Any] | None = None) -> None:
        """Log an info message."""
        if not self.is_enabled:
            return

        try:
            self._client.log_info(message, attributes=attributes or {})
        except Exception as e:
            logger.debug("Failed to send log", error=str(e))

    def log_warn(self, message: str, attributes: dict[str, Any] | None = None) -> None:
        """Log a warning message."""
        if not self.is_enabled:
            return

        try:
            self._client.log_warn(message, attributes=attributes or {})
        except Exception as e:
            logger.debug("Failed to send log", error=str(e))

    def log_error(self, message: str, attributes: dict[str, Any] | None = None) -> None:
        """Log an error message."""
        if not self.is_enabled:
            return

        try:
            self._client.log_error(message, attributes=attributes or {})
        except Exception as e:
            logger.debug("Failed to send log", error=str(e))

    def log_debug(self, message: str, attributes: dict[str, Any] | None = None) -> None:
        """Log a debug message."""
        if not self.is_enabled:
            return

        try:
            self._client.log_debug(message, attributes=attributes or {})
        except Exception as e:
            logger.debug("Failed to send log", error=str(e))

    # -------------------------------------------------------------------------
    # Tracing API
    # -------------------------------------------------------------------------

    @contextmanager
    def span(
        self,
        name: str,
        kind: str = "internal",
        attributes: dict[str, Any] | None = None,
    ) -> Generator[str | None, None, None]:
        """Create a span context manager.

        Args:
            name: Span name (will be prefixed with mcp.).
            kind: Span kind (internal, server, client, producer, consumer).
            attributes: Span attributes.

        Yields:
            Span ID or None if telemetry is disabled.
        """
        if not self.is_enabled:
            yield None
            return

        try:
            span_kind = self._get_span_kind(kind)
            with self._client.span(
                f"mcp.{name}",
                kind=span_kind,
                attributes=attributes or {},
            ) as span_id:
                yield span_id
        except Exception as e:
            logger.debug("Failed to create span", name=name, error=str(e))
            yield None

    def _get_span_kind(self, kind: str) -> Any:
        """Convert string kind to SpanKind enum."""
        kind_map = {
            "internal": self._SpanKind.INTERNAL,
            "server": self._SpanKind.SERVER,
            "client": self._SpanKind.CLIENT,
            "producer": self._SpanKind.PRODUCER,
            "consumer": self._SpanKind.CONSUMER,
        }
        return kind_map.get(kind.lower(), self._SpanKind.INTERNAL)

    def add_span_event(
        self,
        span_id: str | None,
        event_name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Add an event to the current span.

        Args:
            span_id: Span ID from span() context manager.
            event_name: Event name.
            attributes: Event attributes.
        """
        if not self.is_enabled or span_id is None:
            return

        try:
            self._client.add_span_event(
                span_id,
                event_name,
                attributes=attributes or {},
            )
        except Exception as e:
            logger.debug("Failed to add span event", event=event_name, error=str(e))

    # -------------------------------------------------------------------------
    # MCP-Specific Convenience Methods
    # -------------------------------------------------------------------------

    def record_tool_call(
        self,
        tool_name: str,
        duration_seconds: float,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        """Record a tool call metric.

        Args:
            tool_name: Name of the tool.
            duration_seconds: Duration of the call in seconds.
            success: Whether the call succeeded.
            error_type: Error type if failed.
        """
        attributes = {"tool.name": tool_name, "success": str(success).lower()}
        if error_type:
            attributes["error.type"] = error_type

        self.increment_counter("tools.calls", attributes=attributes)
        self.record_histogram(
            "tools.duration",
            value=duration_seconds,
            unit="s",
            attributes={"tool.name": tool_name},
        )

        if not success:
            self.increment_counter("tools.errors", attributes=attributes)

    def record_resource_read(
        self,
        resource_uri: str,
        duration_seconds: float,
        success: bool,
    ) -> None:
        """Record a resource read metric.

        Args:
            resource_uri: URI of the resource.
            duration_seconds: Duration of the read in seconds.
            success: Whether the read succeeded.
        """
        attributes = {"resource.uri": resource_uri, "success": str(success).lower()}

        self.increment_counter("resources.reads", attributes=attributes)
        self.record_histogram(
            "resources.read_duration",
            value=duration_seconds,
            unit="s",
            attributes={"resource.uri": resource_uri},
        )

    def record_prompt_get(
        self,
        prompt_name: str,
        duration_seconds: float,
        success: bool,
    ) -> None:
        """Record a prompt get metric.

        Args:
            prompt_name: Name of the prompt.
            duration_seconds: Duration in seconds.
            success: Whether the get succeeded.
        """
        attributes = {"prompt.name": prompt_name, "success": str(success).lower()}

        self.increment_counter("prompts.gets", attributes=attributes)
        self.record_histogram(
            "prompts.get_duration",
            value=duration_seconds,
            unit="s",
            attributes={"prompt.name": prompt_name},
        )

    def record_session_event(
        self,
        event: str,
        session_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record a session lifecycle event.

        Args:
            event: Event type (initialized, closed, error).
            session_id: Session identifier.
            attributes: Additional attributes.
        """
        attrs: dict[str, Any] = {"event": event}
        if session_id:
            attrs["session.id"] = session_id
        if attributes:
            attrs.update(attributes)

        self.increment_counter("sessions.events", attributes=attrs)
        self.log_info(f"Session {event}", attributes=attrs)


# -----------------------------------------------------------------------------
# Module-level functions
# -----------------------------------------------------------------------------


def initialize_telemetry(config: TelemetryConfig) -> MCPTelemetryClient | None:
    """Initialize the global telemetry client.

    Args:
        config: TelemetryConfig from MCP server configuration.

    Returns:
        The initialized telemetry client, or None if disabled.
    """
    global _telemetry_client

    if not config.enabled:
        logger.info("Telemetry disabled by configuration")
        return None

    with _telemetry_lock:
        if _telemetry_client is not None:
            return _telemetry_client

        _telemetry_client = MCPTelemetryClient(config)
        _telemetry_client.initialize()
        return _telemetry_client


def shutdown_telemetry(timeout: float = 30.0) -> None:
    """Shutdown the global telemetry client.

    Args:
        timeout: Maximum time to wait for pending telemetry to flush.
    """
    global _telemetry_client

    with _telemetry_lock:
        if _telemetry_client is not None:
            _telemetry_client.shutdown(timeout=timeout)
            _telemetry_client = None


def get_telemetry_client() -> MCPTelemetryClient | None:
    """Get the global telemetry client.

    Returns:
        The telemetry client, or None if not initialized.
    """
    return _telemetry_client


def traced(name: str, kind: str = "internal") -> Callable[[F], F]:
    """Decorator to trace a function.

    Args:
        name: Span name (will be prefixed with mcp.).
        kind: Span kind.

    Returns:
        Decorated function.

    Example:
        @traced("tools.execute", kind="server")
        async def execute_tool(name: str, args: dict) -> ToolResult:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            client = get_telemetry_client()
            if client is None or not client.is_enabled:
                return await func(*args, **kwargs)

            with client.span(name, kind=kind) as span_id:
                try:
                    result = await func(*args, **kwargs)
                    if span_id:
                        client.add_span_event(span_id, "completed", {"status": "success"})
                    return result
                except Exception as e:
                    if span_id:
                        client.add_span_event(
                            span_id,
                            "error",
                            {"error.type": type(e).__name__, "error.message": str(e)},
                        )
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            client = get_telemetry_client()
            if client is None or not client.is_enabled:
                return func(*args, **kwargs)

            with client.span(name, kind=kind) as span_id:
                try:
                    result = func(*args, **kwargs)
                    if span_id:
                        client.add_span_event(span_id, "completed", {"status": "success"})
                    return result
                except Exception as e:
                    if span_id:
                        client.add_span_event(
                            span_id,
                            "error",
                            {"error.type": type(e).__name__, "error.message": str(e)},
                        )
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator
