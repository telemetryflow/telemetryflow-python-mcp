from __future__ import annotations

import signal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from tfo_mcp import __version__
from tfo_mcp.main import cli, info, init_config, main, run_server, setup_signal_handlers, validate


class TestSetupSignalHandlers:
    def test_sets_up_handlers(self):
        mock_server = MagicMock()
        with patch("signal.signal") as mock_signal:
            setup_signal_handlers(mock_server)
            assert mock_signal.call_count == 2

    def test_handler_calls_stop(self):
        mock_server = MagicMock()
        with patch("signal.signal") as mock_signal:
            setup_signal_handlers(mock_server)
            handler = mock_signal.call_args_list[0][0][1]
            handler(signal.SIGINT, None)
            mock_server.stop.assert_called_once()


def _make_mock_config():
    mock_config = MagicMock()
    mock_config.server.debug = False
    mock_config.logging.level = "info"
    mock_config.server.name = "Test"
    mock_config.server.transport = "stdio"
    mock_config.server.version = "1.0.0"
    mock_config.telemetry.enabled = False
    mock_config.telemetry.service_name = "test"
    mock_config.telemetry.endpoint = "localhost:4317"
    mock_config.claude.api_key = ""
    return mock_config


def _make_mock_server():
    mock_server_instance = MagicMock()
    mock_server_instance.run = AsyncMock()
    mock_server_instance._tool_definitions = {}
    mock_server_instance._resource_definitions = []
    mock_server_instance._template_definitions = []
    mock_server_instance._prompt_definitions = {}
    return mock_server_instance


class TestRunServer:
    @patch("tfo_mcp.infrastructure.config.load_config")
    @patch("tfo_mcp.infrastructure.logging.setup_logging")
    @patch("tfo_mcp.infrastructure.telemetry.initialize_telemetry", return_value=None)
    @patch("tfo_mcp.presentation.server.MCPServer")
    @patch("tfo_mcp.presentation.tools.tfo_clickhouse_tools.register_clickhouse_tools")
    @patch("tfo_mcp.presentation.tools.tfo_postgres_tools.register_postgres_tools")
    @patch("tfo_mcp.presentation.tools.register_builtin_tools")
    @patch("tfo_mcp.presentation.resources.register_builtin_resources")
    @patch("tfo_mcp.presentation.prompts.register_builtin_prompts")
    async def test_run_server_basic(
        self,
        mock_prompts,
        mock_res,
        mock_tools,
        _mock_pg,
        _mock_ch,
        mock_server_cls,
        _mock_tel,
        _mock_log,
        mock_load,
    ):
        mock_load.return_value = _make_mock_config()
        mock_server_cls.return_value = _make_mock_server()

        with patch("tfo_mcp.main.setup_signal_handlers"):
            await run_server()

        mock_tools.assert_called_once()
        mock_res.assert_called_once()
        mock_prompts.assert_called_once()

    @patch("tfo_mcp.infrastructure.config.load_config")
    @patch("tfo_mcp.infrastructure.logging.setup_logging")
    @patch("tfo_mcp.infrastructure.telemetry.initialize_telemetry", return_value=None)
    @patch("tfo_mcp.presentation.server.MCPServer")
    @patch("tfo_mcp.infrastructure.claude.ClaudeClient")
    @patch("tfo_mcp.presentation.tools.tfo_clickhouse_tools.register_clickhouse_tools")
    @patch("tfo_mcp.presentation.tools.tfo_postgres_tools.register_postgres_tools")
    @patch("tfo_mcp.presentation.tools.register_builtin_tools")
    @patch("tfo_mcp.presentation.resources.register_builtin_resources")
    @patch("tfo_mcp.presentation.prompts.register_builtin_prompts")
    async def test_run_server_with_claude(
        self,
        _mock_prompts,
        _mock_res,
        _mock_tools,
        _mock_pg,
        _mock_ch,
        mock_claude,
        mock_server_cls,
        _mock_tel,
        _mock_log,
        mock_load,
    ):
        config = _make_mock_config()
        config.claude.api_key = "sk-test-key"
        config.claude.default_model = "claude-sonnet-4-20250514"
        mock_load.return_value = config
        mock_server_cls.return_value = _make_mock_server()

        with patch("tfo_mcp.main.setup_signal_handlers"):
            await run_server()

        mock_claude.assert_called_once()

    @patch("tfo_mcp.infrastructure.config.load_config")
    @patch("tfo_mcp.infrastructure.logging.setup_logging")
    @patch("tfo_mcp.infrastructure.telemetry.initialize_telemetry", return_value=None)
    @patch("tfo_mcp.presentation.server.MCPServer")
    @patch(
        "tfo_mcp.presentation.tools.tfo_clickhouse_tools.register_clickhouse_tools",
        side_effect=Exception("no ch"),
    )
    @patch(
        "tfo_mcp.presentation.tools.tfo_postgres_tools.register_postgres_tools",
        side_effect=Exception("no asyncpg"),
    )
    @patch("tfo_mcp.presentation.tools.register_builtin_tools")
    @patch("tfo_mcp.presentation.resources.register_builtin_resources")
    @patch("tfo_mcp.presentation.prompts.register_builtin_prompts")
    async def test_run_server_optional_tools_fail(
        self,
        _mock_prompts,
        _mock_res,
        _mock_tools,
        _mock_pg,
        _mock_ch,
        mock_server_cls,
        _mock_tel,
        _mock_log,
        mock_load,
    ):
        mock_load.return_value = _make_mock_config()
        mock_server_cls.return_value = _make_mock_server()

        with patch("tfo_mcp.main.setup_signal_handlers"):
            await run_server()

    @patch("tfo_mcp.infrastructure.config.load_config")
    @patch("tfo_mcp.infrastructure.logging.setup_logging")
    @patch("tfo_mcp.infrastructure.telemetry.initialize_telemetry", return_value=None)
    @patch("tfo_mcp.presentation.server.MCPServer")
    @patch("tfo_mcp.presentation.tools.tfo_clickhouse_tools.register_clickhouse_tools")
    @patch("tfo_mcp.presentation.tools.tfo_postgres_tools.register_postgres_tools")
    @patch("tfo_mcp.presentation.tools.register_builtin_tools")
    @patch("tfo_mcp.presentation.resources.register_builtin_resources")
    @patch("tfo_mcp.presentation.prompts.register_builtin_prompts")
    async def test_run_server_keyboard_interrupt(
        self,
        _mock_prompts,
        _mock_res,
        _mock_tools,
        _mock_pg,
        _mock_ch,
        mock_server_cls,
        _mock_tel,
        _mock_log,
        mock_load,
    ):
        mock_load.return_value = _make_mock_config()
        server = _make_mock_server()
        server.run = AsyncMock(side_effect=KeyboardInterrupt())
        mock_server_cls.return_value = server

        with (
            patch("tfo_mcp.main.setup_signal_handlers"),
            patch("tfo_mcp.infrastructure.telemetry.shutdown_telemetry"),
        ):
            await run_server()

    @patch("tfo_mcp.infrastructure.config.load_config")
    @patch("tfo_mcp.infrastructure.logging.setup_logging")
    @patch("tfo_mcp.infrastructure.telemetry.initialize_telemetry", return_value=None)
    @patch("tfo_mcp.presentation.server.MCPServer")
    @patch("tfo_mcp.presentation.tools.tfo_clickhouse_tools.register_clickhouse_tools")
    @patch("tfo_mcp.presentation.tools.tfo_postgres_tools.register_postgres_tools")
    @patch("tfo_mcp.presentation.tools.register_builtin_tools")
    @patch("tfo_mcp.presentation.resources.register_builtin_resources")
    @patch("tfo_mcp.presentation.prompts.register_builtin_prompts")
    async def test_run_server_exception(
        self,
        _mock_prompts,
        _mock_res,
        _mock_tools,
        _mock_pg,
        _mock_ch,
        mock_server_cls,
        _mock_tel,
        _mock_log,
        mock_load,
    ):
        mock_load.return_value = _make_mock_config()
        server = _make_mock_server()
        server.run = AsyncMock(side_effect=RuntimeError("server error"))
        mock_server_cls.return_value = server

        with (
            patch("tfo_mcp.main.setup_signal_handlers"),
            patch("tfo_mcp.infrastructure.telemetry.shutdown_telemetry"),
            pytest.raises(RuntimeError, match="server error"),
        ):
            await run_server()

    @patch("tfo_mcp.infrastructure.config.load_config")
    @patch("tfo_mcp.infrastructure.logging.setup_logging")
    @patch("tfo_mcp.infrastructure.telemetry.initialize_telemetry")
    @patch("tfo_mcp.presentation.server.MCPServer")
    @patch("tfo_mcp.presentation.tools.tfo_clickhouse_tools.register_clickhouse_tools")
    @patch("tfo_mcp.presentation.tools.tfo_postgres_tools.register_postgres_tools")
    @patch("tfo_mcp.presentation.tools.register_builtin_tools")
    @patch("tfo_mcp.presentation.resources.register_builtin_resources")
    @patch("tfo_mcp.presentation.prompts.register_builtin_prompts")
    async def test_run_server_with_telemetry(
        self,
        _mock_prompts,
        _mock_res,
        _mock_tools,
        _mock_pg,
        _mock_ch,
        mock_server_cls,
        mock_init_tel,
        _mock_log,
        mock_load,
    ):
        config = _make_mock_config()
        config.telemetry.enabled = True
        mock_load.return_value = config

        mock_tel_client = MagicMock()
        mock_tel_client.is_enabled = True
        mock_init_tel.return_value = mock_tel_client

        server = _make_mock_server()
        server._tool_definitions = {"t1": MagicMock()}
        server._resource_definitions = [MagicMock()]
        server._template_definitions = [MagicMock()]
        server._prompt_definitions = {"p1": MagicMock()}
        mock_server_cls.return_value = server

        with (
            patch("tfo_mcp.main.setup_signal_handlers"),
            patch("tfo_mcp.infrastructure.telemetry.shutdown_telemetry"),
        ):
            await run_server()

        mock_tel_client.record_session_event.assert_called()
        mock_tel_client.increment_counter.assert_called()

    @patch("tfo_mcp.infrastructure.config.load_config")
    @patch("tfo_mcp.infrastructure.logging.setup_logging")
    @patch("tfo_mcp.infrastructure.telemetry.initialize_telemetry", return_value=None)
    @patch("tfo_mcp.presentation.server.MCPServer")
    @patch("tfo_mcp.presentation.tools.tfo_clickhouse_tools.register_clickhouse_tools")
    @patch("tfo_mcp.presentation.tools.tfo_postgres_tools.register_postgres_tools")
    @patch("tfo_mcp.presentation.tools.register_builtin_tools")
    @patch("tfo_mcp.presentation.resources.register_builtin_resources")
    @patch("tfo_mcp.presentation.prompts.register_builtin_prompts")
    async def test_run_server_debug_mode(
        self,
        _mock_prompts,
        _mock_res,
        _mock_tools,
        _mock_pg,
        _mock_ch,
        mock_server_cls,
        _mock_tel,
        _mock_log,
        mock_load,
    ):
        config = _make_mock_config()
        mock_load.return_value = config
        mock_server_cls.return_value = _make_mock_server()

        with patch("tfo_mcp.main.setup_signal_handlers"):
            await run_server(debug=True)

        assert config.server.debug is True
        assert config.logging.level == "debug"


class TestServeCommand:
    def test_serve_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.output
        assert "--debug" in result.output


class TestValidateCommand:
    def test_validate_default(self):
        runner = CliRunner()
        result = runner.invoke(validate)
        assert result.exit_code == 0
        assert "Configuration is valid!" in result.output

    def test_validate_shows_details(self):
        runner = CliRunner()
        result = runner.invoke(validate)
        assert result.exit_code == 0
        assert "Server:" in result.output
        assert "Transport:" in result.output

    def test_validate_custom_file(self, tmp_path):
        config_file = tmp_path / "test.yaml"
        config_file.write_text('server:\n  name: "Custom"\n')
        runner = CliRunner()
        result = runner.invoke(validate, ["-c", str(config_file)])
        assert result.exit_code == 0
        assert "Custom" in result.output

    def test_validate_nonexistent(self):
        runner = CliRunner()
        result = runner.invoke(validate, ["-c", "/nonexistent/config.yaml"])
        assert result.exit_code != 0


class TestInfoCommand:
    def test_info_output(self):
        runner = CliRunner()
        result = runner.invoke(info)
        assert result.exit_code == 0
        assert "TelemetryFlow Python MCP Server" in result.output
        assert __version__ in result.output

    def test_info_shows_tools(self):
        runner = CliRunner()
        result = runner.invoke(info)
        assert "echo" in result.output
        assert "read_file" in result.output


class TestInitConfigCommand:
    def test_creates_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init_config)
            assert result.exit_code == 0
            assert Path("tfo-mcp.yaml").exists()

    def test_wont_overwrite(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tfo-mcp.yaml").write_text("existing")
            result = runner.invoke(init_config)
            assert result.exit_code == 1
            assert "already exists" in result.output


class TestMainFunction:
    def test_main_calls_cli(self):
        with patch("tfo_mcp.main.cli") as mock_cli:
            main()
            mock_cli.assert_called_once()


class TestCLIGroup:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "serve" in result.output
        assert "validate" in result.output
        assert "info" in result.output
        assert "init-config" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output
