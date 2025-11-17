"""
Unit tests for wc command - all scenarios in one focused file
"""

from unittest.mock import patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.system.wc_command import WcCommand


class TestWcCommand:
    """Unit tests for wc command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_basic_count(self, mock_execute, context):
        """Test basic wc showing all counts (lines, words, characters)"""
        mock_execute.return_value = CommandResult(raw_output="  5  25 150 file.txt\n", success=True, exit_code=0)

        cmd = WcCommand("file.txt")
        result = cmd.execute(context)

        assert result.success
        assert "5" in result.raw_output  # lines
        assert "25" in result.raw_output  # words
        assert "150" in result.raw_output  # characters
        assert "file.txt" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_lines_only(self, mock_execute, context):
        """Test wc -l counting only lines"""
        mock_execute.return_value = CommandResult(raw_output="  5 file.txt\n", success=True, exit_code=0)

        cmd = WcCommand("file.txt").with_option("-l")
        result = cmd.execute(context)

        assert result.success
        assert "5" in result.raw_output
        assert result.raw_output.count(" ") == 1  # Only one count field

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_words_only(self, mock_execute, context):
        """Test wc -w counting only words"""
        mock_execute.return_value = CommandResult(raw_output="  25 file.txt\n", success=True, exit_code=0)

        cmd = WcCommand("file.txt").with_option("-w")
        result = cmd.execute(context)

        assert result.success
        assert "25" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_characters_only(self, mock_execute, context):
        """Test wc -c counting only characters"""
        mock_execute.return_value = CommandResult(raw_output="  150 file.txt\n", success=True, exit_code=0)

        cmd = WcCommand("file.txt").with_option("-c")
        result = cmd.execute(context)

        assert result.success
        assert "150" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_bytes_only(self, mock_execute, context):
        """Test wc -m counting bytes (same as characters in ASCII)"""
        mock_execute.return_value = CommandResult(raw_output="  150 file.txt\n", success=True, exit_code=0)

        cmd = WcCommand("file.txt").with_option("-m")
        result = cmd.execute(context)

        assert result.success
        assert "150" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_longest_line(self, mock_execute, context):
        """Test wc -L finding longest line length"""
        mock_execute.return_value = CommandResult(raw_output="  42 file.txt\n", success=True, exit_code=0)

        cmd = WcCommand("file.txt").with_option("-L")
        result = cmd.execute(context)

        assert result.success
        assert "42" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_multiple_files(self, mock_execute, context):
        """Test wc with multiple files"""
        mock_execute.return_value = CommandResult(
            raw_output="  3  15  90 file1.txt\n  2  10  60 file2.txt\n  5  25 150 total\n", success=True, exit_code=0
        )

        cmd = WcCommand("file1.txt", "file2.txt")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "file2.txt" in result.raw_output
        assert "total" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_stdin_input(self, mock_execute, context):
        """Test wc reading from stdin (no filename)"""
        mock_execute.return_value = CommandResult(raw_output="  5  25 150\n", success=True, exit_code=0)

        cmd = WcCommand()  # No filename = read from stdin
        result = cmd.execute(context)

        assert result.success
        assert "5" in result.raw_output
        assert "25" in result.raw_output
        assert "150" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_empty_file(self, mock_execute, context):
        """Test wc with empty file"""
        mock_execute.return_value = CommandResult(raw_output="  0   0   0 empty.txt\n", success=True, exit_code=0)

        cmd = WcCommand("empty.txt")
        result = cmd.execute(context)

        assert result.success
        assert "0" in result.raw_output
        assert "empty.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_file_not_found(self, mock_execute, context):
        """Test wc with non-existent file"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="wc: nonexistent.txt: No such file or directory"
        )

        cmd = WcCommand("nonexistent.txt")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "No such file or directory" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_permission_denied(self, mock_execute, context):
        """Test wc with permission denied"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="wc: /etc/shadow: Permission denied"
        )

        cmd = WcCommand("/etc/shadow")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "Permission denied" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_invalid_option(self, mock_execute, context):
        """Test wc with invalid option"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="wc: invalid option -- 'z'"
        )

        cmd = WcCommand("file.txt").with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_wc_combined_options(self, mock_execute, context):
        """Test wc with combined options"""
        mock_execute.return_value = CommandResult(raw_output="  5  25 file.txt\n", success=True, exit_code=0)

        cmd = WcCommand("file.txt").with_option("-l").with_option("-w")
        result = cmd.execute(context)

        assert result.success
        assert "5" in result.raw_output
        assert "25" in result.raw_output
