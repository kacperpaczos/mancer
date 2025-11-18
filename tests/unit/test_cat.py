"""
Unit tests for cat command - all scenarios in one focused file
"""

from unittest.mock import patch, MagicMock

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.cat_command import CatCommand


class TestCatCommand:
    """Unit tests for cat command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_single_file(self, mock_get_backend, context):
        """Test cat displaying single file content"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "line 1\nline 2\nline 3\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="test.txt")
        result = cmd.execute(context)

        assert result.success
        assert "line 1" in result.raw_output
        assert "line 2" in result.raw_output
        assert "line 3" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_multiple_files(self, mock_get_backend, context):
        """Test cat concatenating multiple files"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "content of file1\ncontent of file2\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="file1.txt").with_option("file2.txt")
        result = cmd.execute(context)

        assert result.success
        assert "content of file1" in result.raw_output
        assert "content of file2" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_with_line_numbers(self, mock_get_backend, context):
        """Test cat -n with line numbers"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "     1\tline one\n     2\tline two\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="test.txt").with_option("-n")
        result = cmd.execute(context)

        assert result.success
        assert "1\tline one" in result.raw_output
        assert "2\tline two" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_show_nonprinting(self, mock_get_backend, context):
        """Test cat -v showing non-printing characters"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "line with^M control chars\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="test.txt").with_option("-v")
        result = cmd.execute(context)

        assert result.success
        assert "^M" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_squeeze_blank_lines(self, mock_get_backend, context):
        """Test cat -s squeezing blank lines"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "line1\n\nline2\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="test.txt").with_option("-s")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output.count("\n\n") <= 1

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_file_not_found(self, mock_get_backend, context):
        """Test cat with non-existent file"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "cat: nonexistent.txt: No such file or directory")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="nonexistent.txt")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "No such file or directory" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_permission_denied(self, mock_get_backend, context):
        """Test cat with permission denied"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "cat: /etc/shadow: Permission denied")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="/etc/shadow")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "Permission denied" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_empty_file(self, mock_get_backend, context):
        """Test cat with empty file"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "", "")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="empty.txt")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0
        assert result.raw_output == ""

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_stdin_input(self, mock_get_backend, context):
        """Test cat reading from stdin"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "input from stdin\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand()  # No file specified = read from stdin
        result = cmd.execute(context)

        assert result.success
        assert "input from stdin" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_cat_show_ends(self, mock_get_backend, context):
        """Test cat -E showing line ends"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "line1$\nline2$\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = CatCommand(file_path="test.txt").with_option("-E")
        result = cmd.execute(context)

        assert result.success
        assert "line1$" in result.raw_output
        assert "line2$" in result.raw_output
