"""
Unit tests for find command - all scenarios in one focused file
"""

from unittest.mock import patch, MagicMock

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.find_command import FindCommand


class TestFindCommand:
    """Unit tests for find command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_basic_search(self, mock_get_backend, context):
        """Test basic find command in current directory"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./file1.txt\n./file2.txt\n./subdir/file3.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand()
        result = cmd.execute(context)

        assert result.success
        assert "./file1.txt" in result.raw_output
        assert "./file2.txt" in result.raw_output
        assert "./subdir/file3.txt" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_specific_directory(self, mock_get_backend, context):
        """Test find in specific directory"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "/tmp/file1.txt\n/tmp/file2.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand(path="/tmp")
        result = cmd.execute(context)

        assert result.success
        assert "/tmp/file1.txt" in result.raw_output
        assert "/tmp/file2.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_by_name(self, mock_get_backend, context):
        """Test find -name searching by filename pattern"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./test.txt\n./data/test.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-name").with_option("*.txt")
        result = cmd.execute(context)

        assert result.success
        assert "test.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_by_type_file(self, mock_get_backend, context):
        """Test find -type f searching for regular files"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./file1.txt\n./file2.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-type").with_option("f")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "file2.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_by_type_directory(self, mock_get_backend, context):
        """Test find -type d searching for directories"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./dir1\n./dir2\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-type").with_option("d")
        result = cmd.execute(context)

        assert result.success
        assert "./dir1" in result.raw_output
        assert "./dir2" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_max_depth(self, mock_get_backend, context):
        """Test find -maxdepth limiting search depth"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./file1.txt\n./file2.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-maxdepth").with_option("1")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "file2.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_size_filter(self, mock_get_backend, context):
        """Test find -size filtering by file size"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./large_file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-size").with_option("+1M")
        result = cmd.execute(context)

        assert result.success
        assert "large_file.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_mtime_filter(self, mock_get_backend, context):
        """Test find -mtime filtering by modification time"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./recent_file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-mtime").with_option("-7")
        result = cmd.execute(context)

        assert result.success
        assert "recent_file.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_exec_action(self, mock_get_backend, context):
        """Test find -exec executing command on found files"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./file1.txt\n./file2.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-exec").with_option("ls").with_option("-l").with_option("{}").with_option(";")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "file2.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_delete_action(self, mock_get_backend, context):
        """Test find -delete removing found files"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./temp1.txt\n./temp2.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-delete")
        result = cmd.execute(context)

        assert result.success
        assert "temp1.txt" in result.raw_output
        assert "temp2.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_no_matches(self, mock_get_backend, context):
        """Test find when no files match criteria"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "", "")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-name").with_option("nonexistent*.txt")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0
        assert result.raw_output == ""

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_permission_denied(self, mock_get_backend, context):
        """Test find with permission denied"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "./allowed_file.txt\nfind: '/root': Permission denied\n", "find: '/root': Permission denied")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand("/root")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "Permission denied" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_invalid_option(self, mock_get_backend, context):
        """Test find with invalid option"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "find: invalid option -- 'z'")
        mock_get_backend.return_value = mock_backend

        cmd = FindCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_find_complex_criteria(self, mock_get_backend, context):
        """Test find with complex combined criteria"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "./big_text_file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        # Find files larger than 1MB that are text files modified in last 30 days
        cmd = (
            FindCommand()
            .with_option("-size")
            .with_option("+1M")
            .with_option("-name")
            .with_option("*.txt")
            .with_option("-mtime")
            .with_option("-30")
        )
        result = cmd.execute(context)

        assert result.success
        assert "big_text_file.txt" in result.raw_output
