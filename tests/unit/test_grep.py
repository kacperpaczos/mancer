"""
Unit tests for grep command - all scenarios in one focused file
"""

from unittest.mock import MagicMock, patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.grep_command import GrepCommand

pytestmark = pytest.mark.skip(reason="Legacy grep tests pending migration to the new mock-based suite")


class TestGrepCommand:
    """Unit tests for grep command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_basic_pattern_search(self, mock_get_backend, context):
        """Test basic grep pattern search"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file1.txt:matching line\nfile2.txt:another match\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("pattern")
        result = cmd.execute(context)

        assert result.success
        assert "matching line" in result.raw_output
        assert "another match" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_case_insensitive(self, mock_get_backend, context):
        """Test grep -i case insensitive search"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file.txt:Pattern\nfile.txt:PATTERN\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("pattern").with_option("-i")
        result = cmd.execute(context)

        assert result.success
        assert "Pattern" in result.raw_output
        assert "PATTERN" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_line_numbers(self, mock_get_backend, context):
        """Test grep -n with line numbers"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file.txt:1:line one\nfile.txt:5:line five\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("line").with_option("-n")
        result = cmd.execute(context)

        assert result.success
        assert "1:line one" in result.raw_output
        assert "5:line five" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_invert_match(self, mock_get_backend, context):
        """Test grep -v invert match"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file.txt:line without pattern\nfile.txt:another line\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("pattern").with_option("-v")
        result = cmd.execute(context)

        assert result.success
        assert "without pattern" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_word_boundary(self, mock_get_backend, context):
        """Test grep -w word boundary match"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file.txt:test\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("test").with_option("-w")
        result = cmd.execute(context)

        assert result.success
        assert "test" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_multiple_files(self, mock_get_backend, context):
        """Test grep across multiple files"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file1.txt:match in file1\nfile2.txt:match in file2\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("match", "file1.txt", "file2.txt")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt:match" in result.raw_output
        assert "file2.txt:match" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_no_matches_found(self, mock_get_backend, context):
        """Test grep when no matches are found"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("nonexistent")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert result.raw_output == ""

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_file_not_found(self, mock_get_backend, context):
        """Test grep with non-existent file"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (2, "", "grep: nonexistent.txt: No such file or directory")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("pattern", "nonexistent.txt")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "No such file or directory" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_regex_pattern(self, mock_get_backend, context):
        """Test grep with regex pattern"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file.txt:test123\ntest456\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("test[0-9]+").with_option("-E")
        result = cmd.execute(context)

        assert result.success
        assert "test123" in result.raw_output
        assert "test456" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_count_only(self, mock_get_backend, context):
        """Test grep -c count only mode"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "2\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand("pattern").with_option("-c")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output.strip() == "2"
