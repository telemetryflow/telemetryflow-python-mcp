from __future__ import annotations

import logging

import pytest
import structlog

from tfo_mcp.infrastructure.config import LoggingConfig
from tfo_mcp.infrastructure.logging.logger import get_logger, setup_logging


class TestSetupLogging:
    @pytest.fixture(autouse=True)
    def reset_logging(self):
        root = logging.getLogger()
        original_level = root.level
        original_handlers = root.handlers[:]
        yield
        root.level = original_level
        root.handlers = original_handlers

    def _force_setup(self, config):
        root = logging.getLogger()
        root.handlers = []
        setup_logging(config)

    def test_default_level(self):
        config = LoggingConfig(level="info")
        self._force_setup(config)
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_debug_level(self):
        config = LoggingConfig(level="debug")
        self._force_setup(config)
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_warning_level(self):
        config = LoggingConfig(level="warning")
        self._force_setup(config)
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_error_level(self):
        config = LoggingConfig(level="error")
        self._force_setup(config)
        root = logging.getLogger()
        assert root.level == logging.ERROR

    def test_json_format(self):
        config = LoggingConfig(format="json", output="stdout")
        self._force_setup(config)
        assert structlog.is_configured()

    def test_console_format(self):
        config = LoggingConfig(format="console", output="stdout")
        self._force_setup(config)
        assert structlog.is_configured()

    def test_stdout_output(self):
        config = LoggingConfig(output="stdout")
        self._force_setup(config)
        root = logging.getLogger()
        handler = root.handlers[0]
        assert isinstance(handler, logging.StreamHandler)

    def test_stderr_output(self):
        config = LoggingConfig(output="stderr")
        self._force_setup(config)
        root = logging.getLogger()
        handler = root.handlers[0]
        assert isinstance(handler, logging.StreamHandler)

    def test_file_output(self, tmp_path):
        log_file = tmp_path / "test.log"
        config = LoggingConfig(output=str(log_file))
        self._force_setup(config)
        root = logging.getLogger()
        handler = root.handlers[0]
        assert isinstance(handler, logging.FileHandler)

    def test_noisy_libraries_suppressed(self):
        config = LoggingConfig(output="stdout")
        self._force_setup(config)
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING

    def test_case_insensitive_level(self):
        config = LoggingConfig(level="WARNING")
        self._force_setup(config)
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_invalid_level_defaults_to_info(self):
        config = LoggingConfig(level="invalid_level")
        self._force_setup(config)
        root = logging.getLogger()
        assert root.level == logging.INFO


class TestGetLogger:
    def test_returns_logger(self):
        logger = get_logger("test_module")
        assert logger is not None

    def test_returns_named_logger(self):
        logger = get_logger("custom_name")
        assert logger is not None

    def test_returns_logger_without_name(self):
        logger = get_logger()
        assert logger is not None

    def test_logger_is_structlog_logger(self):
        config = LoggingConfig(output="stdout")
        setup_logging(config)
        logger = get_logger("test")
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
