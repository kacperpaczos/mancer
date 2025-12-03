"""
Unit tests for CpCommand covering positive and negative scenarios.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.file.cp_command import CpCommand


class TestCpCommand:
    """Dedicated CpCommand unit tests with mocked backend interactions."""

    @pytest.fixture  # type: ignore[misc]
    def context(self) -> CommandContext:
        return CommandContext(current_directory="/tmp/workdir")

    def _success_result(self, output: str = "") -> CommandResult:
        return CommandResult(raw_output=output, success=True, structured_output=[])

    def _failure_result(self, message: str) -> CommandResult:
        return CommandResult(raw_output="", success=False, structured_output=[], exit_code=1, error_message=message)

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cp_recursive_copy_single_source(self, mock_get_backend, context):
        """cp -r should succeed and call backend with built command."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._success_result("copied")
        mock_get_backend.return_value = mock_backend

        cmd = CpCommand().recursive().from_source("src").to_destination("dest")
        result = cmd.execute(context)

        assert result.success
        mock_backend.execute_command.assert_called_once()

    def test_cp_source_and_destination_helpers(self, context):
        """Builder helpers should store parameters for later execution."""
        cmd = CpCommand().from_source("a.txt").to_destination("dest/b.txt")

        assert cmd.parameters["source"] == "a.txt"
        assert cmd.parameters["destination"] == "dest/b.txt"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cp_force_overwrite_failure(self, mock_get_backend, context):
        """cp -f should bubble up backend errors."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._failure_result("permission denied")
        mock_get_backend.return_value = mock_backend

        cmd = CpCommand().force().from_source("file").to_destination("/root/secret")
        result = cmd.execute(context)

        assert not result.success
        assert result.error_message == "permission denied"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cp_preserve_and_verbose_options(self, mock_get_backend, context):
        """Combination of builder helpers should be reflected in command string."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._success_result()
        mock_get_backend.return_value = mock_backend

        cmd = CpCommand().preserve().verbose().interactive().from_source("file.txt").to_destination("backup/file.txt")
        _ = cmd.execute(context)

        executed_command = mock_backend.execute_command.call_args[0][0]
        assert "-p" in executed_command
        assert "-v" in executed_command
        assert "-i" in executed_command

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cp_uses_input_result_sources(self, mock_get_backend, context):
        """When previous command produced file names they should be copied automatically."""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = self._success_result()
        mock_get_backend.return_value = mock_backend

        input_result = SimpleNamespace(
            raw_output="file1\nfile2\n",
            structured_output=[{"name": "file1"}, {"name": "file2"}],
            is_success=lambda: True,
        )

        cmd = CpCommand().to_destination("dest")
        result = cmd.execute(context, input_result=input_result)

        assert result.success
        executed_command = mock_backend.execute_command.call_args[0][0]
        assert "file1" in executed_command and "file2" in executed_command
