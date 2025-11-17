"""
Unit tests for cat command - all scenarios in one focused file
"""

from unittest.mock import patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.system.cat_command import CatCommand


class TestCatCommand:
    """Unit tests for cat command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_single_file(self, mock_execute, context):
        """Test cat displaying single file content"""
        mock_execute.return_value = CommandResult(raw_output="line 1\nline 2\nline 3\n", success=True, exit_code=0)

        cmd = CatCommand(file_path="test.txt")
        result = cmd.execute(context)

        assert result.success
        assert "line 1" in result.raw_output
        assert "line 2" in result.raw_output
        assert "line 3" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_multiple_files(self, mock_execute, context):
        """Test cat concatenating multiple files"""
        mock_execute.return_value = CommandResult(
            raw_output="content of file1\ncontent of file2\n", success=True, exit_code=0
        )

        cmd = CatCommand(file_path="file1.txt").with_option("file2.txt")
        result = cmd.execute(context)

        assert result.success
        assert "content of file1" in result.raw_output
        assert "content of file2" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_with_line_numbers(self, mock_execute, context):
        """Test cat -n with line numbers"""
        mock_execute.return_value = CommandResult(
            raw_output="     1\tline one\n     2\tline two\n", success=True, exit_code=0
        )

        cmd = CatCommand(file_path="test.txt").with_option("-n")
        result = cmd.execute(context)

        assert result.success
        assert "1\tline one" in result.raw_output
        assert "2\tline two" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_show_nonprinting(self, mock_execute, context):
        """Test cat -v showing non-printing characters"""
        mock_execute.return_value = CommandResult(raw_output="line with^M control chars\n", success=True, exit_code=0)

        cmd = CatCommand(file_path="test.txt").with_option("-v")
        result = cmd.execute(context)

        assert result.success
        assert "^M" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_squeeze_blank_lines(self, mock_execute, context):
        """Test cat -s squeezing blank lines"""
        mock_execute.return_value = CommandResult(raw_output="line1\n\nline2\n", success=True, exit_code=0)

        cmd = CatCommand(file_path="test.txt").with_option("-s")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output.count("\n\n") <= 1

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_file_not_found(self, mock_execute, context):
        """Test cat with non-existent file"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="cat: nonexistent.txt: No such file or directory"
        )

        cmd = CatCommand(file_path="nonexistent.txt")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "No such file or directory" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_permission_denied(self, mock_execute, context):
        """Test cat with permission denied"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="cat: /etc/shadow: Permission denied"
        )

        cmd = CatCommand(file_path="/etc/shadow")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "Permission denied" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_empty_file(self, mock_execute, context):
        """Test cat with empty file"""
        mock_execute.return_value = CommandResult(raw_output="", success=True, exit_code=0)

        cmd = CatCommand(file_path="empty.txt")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0
        assert result.raw_output == ""

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_stdin_input(self, mock_execute, context):
        """Test cat reading from stdin"""
        mock_execute.return_value = CommandResult(raw_output="input from stdin\n", success=True, exit_code=0)

        cmd = CatCommand()  # No file specified = read from stdin
        result = cmd.execute(context)

        assert result.success
        assert "input from stdin" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_cat_show_ends(self, mock_execute, context):
        """Test cat -E showing line ends"""
        mock_execute.return_value = CommandResult(raw_output="line1$\nline2$\n", success=True, exit_code=0)

        cmd = CatCommand(file_path="test.txt").with_option("-E")
        result = cmd.execute(context)

        assert result.success
        assert "line1$" in result.raw_output
        assert "line2$" in result.raw_output
