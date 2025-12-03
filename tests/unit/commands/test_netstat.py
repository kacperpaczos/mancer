"""
Unit tests for NetstatCommand verifying parsing and builder helpers.
"""

from unittest.mock import MagicMock, patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.network.netstat_command import NetstatCommand


class TestNetstatCommand:
    """Netstat command coverage."""

    SAMPLE_OUTPUT = """Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 127.0.0.1:8080          0.0.0.0:*               LISTEN
udp        0      0 0.0.0.0:123             0.0.0.0:*""".strip()

    @pytest.fixture  # type: ignore[misc]
    def context(self) -> CommandContext:
        return CommandContext(current_directory="/tmp")

    def _result(self, success=True, output=None):
        return CommandResult(
            raw_output=output if output is not None else self.SAMPLE_OUTPUT,
            success=success,
            structured_output=[],
            exit_code=0 if success else 1,
            error_message=None if success else "netstat failed",
        )

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_netstat_parses_connections(self, mock_get_backend, context):
        """Structured output should include parsed columns."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._result()
        mock_get_backend.return_value = mock_backend

        result = NetstatCommand().execute(context)

        assert result.success
        assert result.structured_output[0]["proto"] == "tcp"
        assert result.structured_output[0]["state"] == "LISTEN"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_netstat_tcp_option(self, mock_get_backend, context):
        """Applying tcp() should add -t to command string."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._result()
        mock_get_backend.return_value = mock_backend

        _ = NetstatCommand().tcp().execute(context)

        executed_command = mock_backend.execute_command.call_args[0][0]
        assert "-t" in executed_command

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_netstat_programs_and_numeric(self, mock_get_backend, context):
        """Combined options should be present and command should succeed."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._result()
        mock_get_backend.return_value = mock_backend

        result = NetstatCommand().programs().numeric().execute(context)

        executed_command = mock_backend.execute_command.call_args[0][0]
        assert "-p" in executed_command and "-n" in executed_command
        assert result.success

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_netstat_routes_view(self, mock_get_backend, context):
        """Route option should append -r."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._result()
        mock_get_backend.return_value = mock_backend

        _ = NetstatCommand().routes().execute(context)

        assert "-r" in mock_backend.execute_command.call_args[0][0]

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_netstat_failure_propagates(self, mock_get_backend, context):
        """Failure from backend should remain untouched."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._result(success=False)
        mock_get_backend.return_value = mock_backend

        result = NetstatCommand().execute(context)

        assert not result.success
        assert result.error_message == "netstat failed"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_netstat_continuous_interval(self, mock_get_backend, context):
        """Continuous mode should include interval parameter."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._result()
        mock_get_backend.return_value = mock_backend

        _ = NetstatCommand().continuous(interval=5).execute(context)

        executed_command = mock_backend.execute_command.call_args[0][0]
        assert "-c" in executed_command
        assert "--interval=5" in executed_command
