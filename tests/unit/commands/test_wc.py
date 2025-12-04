"""
Unit tests for wc command - all scenarios in one focused file
"""

from unittest.mock import MagicMock, patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.wc_command import WcCommand


class TestWcCommand:
    """Unit tests for wc command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_basic_count(self, mock_get_backend, context):
        """Test basic wc showing all counts (lines, words, characters)"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "5 25 150 file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file.txt")
        result = cmd.execute(context)

        assert result.success
        assert "5" in result.raw_output  # lines
        assert "25" in result.raw_output  # words
        assert "150" in result.raw_output  # characters
        assert "file.txt" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_lines_only(self, mock_get_backend, context):
        """Test wc -l counting only lines"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "5 file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file.txt").with_option("-l")
        result = cmd.execute(context)

        assert result.success
        assert "5" in result.raw_output
        assert result.raw_output.count(" ") == 1  # Only one space between count and filename

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_words_only(self, mock_get_backend, context):
        """Test wc -w counting only words"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "25 file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file.txt").with_option("-w")
        result = cmd.execute(context)

        assert result.success
        assert "25" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_characters_only(self, mock_get_backend, context):
        """Test wc -c counting only characters"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "150 file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file.txt").with_option("-c")
        result = cmd.execute(context)

        assert result.success
        assert "150" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_bytes_only(self, mock_get_backend, context):
        """Test wc -m counting bytes (same as characters in ASCII)"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "150 file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file.txt").with_option("-m")
        result = cmd.execute(context)

        assert result.success
        assert "150" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_longest_line(self, mock_get_backend, context):
        """Test wc -L finding longest line length"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "42 file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file.txt").with_option("-L")
        result = cmd.execute(context)

        assert result.success
        assert "42" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_multiple_files(self, mock_get_backend, context):
        """Test wc with multiple files"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "3 15 90 file1.txt\n2 10 60 file2.txt\n5 25 150 total\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file1.txt", "file2.txt")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "file2.txt" in result.raw_output
        assert "total" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_stdin_input(self, mock_get_backend, context):
        """Test wc reading from stdin (no filename)"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "5 25 150\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand()  # No filename = read from stdin
        result = cmd.execute(context)

        assert result.success
        assert "5" in result.raw_output
        assert "25" in result.raw_output
        assert "150" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_empty_file(self, mock_get_backend, context):
        """Test wc with empty file"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "0 0 0 empty.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("empty.txt")
        result = cmd.execute(context)

        assert result.success
        assert "0" in result.raw_output
        assert "empty.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_file_not_found(self, mock_get_backend, context):
        """Test wc with non-existent file"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "wc: nonexistent.txt: No such file or directory")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("nonexistent.txt")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "No such file or directory" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_permission_denied(self, mock_get_backend, context):
        """Test wc with permission denied"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "wc: /etc/shadow: Permission denied")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("/etc/shadow")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "Permission denied" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_invalid_option(self, mock_get_backend, context):
        """Test wc with invalid option"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "wc: invalid option -- 'z'")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file.txt").with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_wc_combined_options(self, mock_get_backend, context):
        """Test wc with combined options"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "5 25 file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = WcCommand("file.txt").with_option("-l").with_option("-w")
        result = cmd.execute(context)

        assert result.success
        assert "5" in result.raw_output
        assert "25" in result.raw_output
