"""
Unit tests for CdCommand ensuring directory resolution is fully mocked.
"""

from unittest.mock import MagicMock, patch

import pytest

from mancer.domain.model.command_context import CommandContext, ExecutionMode, RemoteHostInfo
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.file.cd_command import CdCommand


class TestCdCommand:
    """All CdCommand scenarios live in this dedicated test file."""

    @pytest.fixture  # type: ignore[misc]
    def context(self) -> CommandContext:
        """Default local execution context."""
        return CommandContext(current_directory="/home/mancer")

    @patch("mancer.infrastructure.command.file.cd_command.os.path.isdir", return_value=True)
    def test_cd_to_relative_directory(self, mock_isdir, context):
        """cd should resolve relative paths against current directory."""
        result = CdCommand().to_directory("projects").execute(context)

        assert result.success
        assert context.current_directory.endswith("projects")
        mock_isdir.assert_called_once()

    @patch("mancer.infrastructure.command.file.cd_command.os.path.isdir", return_value=True)
    def test_cd_to_absolute_directory(self, _mock_isdir, context):
        """Absolute paths should be respected without normalization."""
        target = "/var/log"
        result = CdCommand().to_directory(target).execute(context)

        assert result.success
        assert context.current_directory == target
        assert result.structured_output == [target]

    @patch("mancer.infrastructure.command.file.cd_command.os.path.isdir", return_value=False)
    def test_cd_fails_when_directory_missing(self, _mock_isdir, context):
        """Missing directory should produce an error result without touching context."""
        result = CdCommand().to_directory("missing").execute(context)

        assert not result.success
        assert "missing" in (result.error_message or "")
        assert context.current_directory == "/home/mancer"

    @staticmethod
    def _fake_result(rows):
        fake = MagicMock()
        fake.is_success.return_value = True
        fake.structured_output = rows
        return fake

    @patch("mancer.infrastructure.command.file.cd_command.os.path.isdir", return_value=True)
    def test_cd_uses_input_result_when_available(self, _mock_isdir, context):
        """When previous output provides directories, cd should consume them."""
        input_result = self._fake_result([{"name": "docs"}])

        result = CdCommand().execute(context, input_result=input_result)

        assert result.success
        assert context.current_directory.endswith("docs")

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cd_remote_missing_directory(self, mock_get_backend):
        """In remote mode cd validates directory existence via backend call."""
        context = CommandContext(
            current_directory="/remote",
            execution_mode=ExecutionMode.REMOTE,
            remote_host=RemoteHostInfo(host="example.com"),
        )
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="not_exists",
            success=True,
            structured_output=[],
        )
        mock_get_backend.return_value = mock_backend

        result = CdCommand().to_directory("/remote/data").execute(context)

        assert not result.success
        assert "Nie ma takiego pliku" in (result.error_message or "")
        mock_backend.execute_command.assert_called_once()
