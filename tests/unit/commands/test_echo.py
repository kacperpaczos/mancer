"""
Unit tests for echo command - all scenarios in one focused file
"""

from unittest.mock import MagicMock, patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.echo_command import EchoCommand


class TestEchoCommand:
    """Unit tests for echo command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_basic_text(self, mock_get_backend, context):
        """Test basic echo with simple text"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "hello world\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="hello world")
        result = cmd.execute(context)

        assert result.success
        assert "hello world" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_no_newline(self, mock_get_backend, context):
        """Test echo -n without trailing newline"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "hello world", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="hello world").with_option("-n")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output == "hello world"  # No newline
        assert not result.raw_output.endswith("\n")

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_escape_sequences(self, mock_get_backend, context):
        """Test echo -e with escape sequence interpretation"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "hello\tworld\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="hello\\tworld").with_option("-e")
        result = cmd.execute(context)

        assert result.success
        assert "hello\tworld" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_multiple_words(self, mock_get_backend, context):
        """Test echo with multiple words and spaces"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "this is a test message\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="this is a test message")
        result = cmd.execute(context)

        assert result.success
        assert "this is a test message" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_special_characters(self, mock_get_backend, context):
        """Test echo with special characters"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "!@#$%^&*()\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="!@#$%^&*()")
        result = cmd.execute(context)

        assert result.success
        assert "!@#$%^&*()" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_empty_string(self, mock_get_backend, context):
        """Test echo with empty string"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output == "\n"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_quotes_in_message(self, mock_get_backend, context):
        """Test echo with quotes in the message"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message='he said "hello"')
        result = cmd.execute(context)

        assert result.success
        assert 'he said "hello"' in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_newlines_in_message(self, mock_get_backend, context):
        """Test echo with newlines in message"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "line1\nline2\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="line1\\nline2")
        result = cmd.execute(context)

        assert result.success
        assert "line1\\nline2" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_newlines_interpreted(self, mock_get_backend, context):
        """Test echo -e with interpreted newlines"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "line1\nline2\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="line1\\nline2").with_option("-e")
        result = cmd.execute(context)

        assert result.success
        assert "line1\nline2" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_backslash_escapes(self, mock_get_backend, context):
        """Test echo -e with backslash escape sequences"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "path\to\file\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="path\\\\to\\\\file").with_option("-e")
        result = cmd.execute(context)

        assert result.success
        assert "path\\to\\file" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_invalid_option(self, mock_get_backend, context):
        """Test echo with invalid option"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "echo: invalid option -- 'z'")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message="test").with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_echo_long_message(self, mock_get_backend, context):
        """Test echo with very long message"""
        long_message = "a" * 1000
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "", "")
        mock_get_backend.return_value = mock_backend

        cmd = EchoCommand(message=long_message)
        result = cmd.execute(context)

        assert result.success
        assert long_message in result.raw_output
        assert len(result.raw_output) > 1000
