"""
Unit tests for CustomCommand behaviours.
"""

from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.custom.custom_command import CustomCommand


class TestCustomCommand:
    """Covers parsing and stdin wiring for CustomCommand."""

    @pytest.fixture  # type: ignore[misc]
    def context(self) -> CommandContext:
        return CommandContext(current_directory="/workspace")

    def _backend(self, mock_get_backend, exit_code=0, output="", error=""):
        backend = MagicMock()
        backend.execute.return_value = (exit_code, output, error)
        mock_get_backend.return_value = backend
        return backend

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_custom_basic_execution(self, mock_get_backend, context):
        """Simple shell snippet should execute successfully."""
        backend = self._backend(mock_get_backend, output="done\n")

        result = CustomCommand("echo done").execute(context)

        assert result.success
        assert result.raw_output.strip() == "done"
        backend.execute.assert_called_once()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_custom_uses_input_result_as_stdin(self, mock_get_backend, context):
        """Input result raw output should be forwarded to backend."""
        backend = self._backend(mock_get_backend)
        previous = MagicMock(raw_output="payload", spec=["raw_output"])

        _ = CustomCommand("cat").execute(context, input_result=previous)

        assert backend.execute.call_args.kwargs["input_data"] == "payload"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_custom_parses_json_output(self, mock_get_backend, context):
        """JSON output should be converted into a Polars DataFrame."""
        self._backend(mock_get_backend, output='[{"key": "value"}]')

        result = CustomCommand('echo \'[{"key": "value"}]\'').execute(context)

        assert isinstance(result.structured_output, pl.DataFrame)
        assert result.structured_output.to_dicts()[0]["key"] == "value"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_custom_parses_key_value_lines(self, mock_get_backend, context):
        """Key-value text should be transformed into structured rows."""
        self._backend(mock_get_backend, output="status: ok\ninfo: done\n")

        result = CustomCommand("echo 'status: ok'").execute(context)

        rows = result.structured_output
        if isinstance(rows, pl.DataFrame):
            rows = rows.to_dicts()
        assert len(rows) >= 2
        contents = {row["raw_line"] for row in rows}
        assert "status: ok" in contents

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_custom_failure_propagates(self, mock_get_backend, context):
        """Non zero exit code should set success False."""
        self._backend(mock_get_backend, exit_code=1, error="boom")

        result = CustomCommand("false").execute(context)

        assert not result.success
        assert result.error_message == "boom"
