"""
Unit tests for echo command - all scenarios in one focused file
"""

from unittest.mock import patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.system.echo_command import EchoCommand


class TestEchoCommand:
    """Unit tests for echo command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_basic_text(self, mock_execute, context):
        """Test basic echo with simple text"""
        mock_execute.return_value = CommandResult(raw_output="hello world\n", success=True, exit_code=0)

        cmd = EchoCommand(message="hello world")
        result = cmd.execute(context)

        assert result.success
        assert "hello world" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_no_newline(self, mock_execute, context):
        """Test echo -n without trailing newline"""
        mock_execute.return_value = CommandResult(raw_output="hello world", success=True, exit_code=0)

        cmd = EchoCommand(message="hello world").with_option("-n")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output == "hello world"  # No newline
        assert not result.raw_output.endswith("\n")

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_escape_sequences(self, mock_execute, context):
        """Test echo -e with escape sequence interpretation"""
        mock_execute.return_value = CommandResult(raw_output="hello\tworld\n", success=True, exit_code=0)

        cmd = EchoCommand(message="hello\\tworld").with_option("-e")
        result = cmd.execute(context)

        assert result.success
        assert "hello\tworld" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_multiple_words(self, mock_execute, context):
        """Test echo with multiple words and spaces"""
        mock_execute.return_value = CommandResult(raw_output="this is a test message\n", success=True, exit_code=0)

        cmd = EchoCommand(message="this is a test message")
        result = cmd.execute(context)

        assert result.success
        assert "this is a test message" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_special_characters(self, mock_execute, context):
        """Test echo with special characters"""
        mock_execute.return_value = CommandResult(raw_output="!@#$%^&*()\n", success=True, exit_code=0)

        cmd = EchoCommand(message="!@#$%^&*()")
        result = cmd.execute(context)

        assert result.success
        assert "!@#$%^&*()" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_empty_string(self, mock_execute, context):
        """Test echo with empty string"""
        mock_execute.return_value = CommandResult(raw_output="\n", success=True, exit_code=0)

        cmd = EchoCommand(message="")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output == "\n"

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_quotes_in_message(self, mock_execute, context):
        """Test echo with quotes in the message"""
        mock_execute.return_value = CommandResult(raw_output='he said "hello"\n', success=True, exit_code=0)

        cmd = EchoCommand(message='he said "hello"')
        result = cmd.execute(context)

        assert result.success
        assert 'he said "hello"' in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_newlines_in_message(self, mock_execute, context):
        """Test echo with newlines in message"""
        mock_execute.return_value = CommandResult(raw_output="line1\nline2\n", success=True, exit_code=0)

        cmd = EchoCommand(message="line1\\nline2")
        result = cmd.execute(context)

        assert result.success
        assert "line1\\nline2" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_newlines_interpreted(self, mock_execute, context):
        """Test echo -e with interpreted newlines"""
        mock_execute.return_value = CommandResult(raw_output="line1\nline2\n", success=True, exit_code=0)

        cmd = EchoCommand(message="line1\\nline2").with_option("-e")
        result = cmd.execute(context)

        assert result.success
        assert "line1\nline2" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_backslash_escapes(self, mock_execute, context):
        """Test echo -e with backslash escape sequences"""
        mock_execute.return_value = CommandResult(raw_output="path\to\file\n", success=True, exit_code=0)

        cmd = EchoCommand(message="path\\\\to\\\\file").with_option("-e")
        result = cmd.execute(context)

        assert result.success
        assert "path\\to\\file" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_invalid_option(self, mock_execute, context):
        """Test echo with invalid option"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="echo: invalid option -- 'z'"
        )

        cmd = EchoCommand(message="test").with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_echo_long_message(self, mock_execute, context):
        """Test echo with very long message"""
        long_message = "a" * 1000
        mock_execute.return_value = CommandResult(raw_output=f"{long_message}\n", success=True, exit_code=0)

        cmd = EchoCommand(message=long_message)
        result = cmd.execute(context)

        assert result.success
        assert long_message in result.raw_output
        assert len(result.raw_output) > 1000
