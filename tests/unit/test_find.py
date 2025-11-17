"""
Unit tests for find command - all scenarios in one focused file
"""

from unittest.mock import patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.system.find_command import FindCommand


class TestFindCommand:
    """Unit tests for find command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_basic_search(self, mock_execute, context):
        """Test basic find command in current directory"""
        mock_execute.return_value = CommandResult(
            raw_output="./file1.txt\n./file2.txt\n./subdir/file3.txt\n", success=True, exit_code=0
        )

        cmd = FindCommand()
        result = cmd.execute(context)

        assert result.success
        assert "./file1.txt" in result.raw_output
        assert "./file2.txt" in result.raw_output
        assert "./subdir/file3.txt" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_specific_directory(self, mock_execute, context):
        """Test find in specific directory"""
        mock_execute.return_value = CommandResult(
            raw_output="/tmp/file1.txt\n/tmp/file2.txt\n", success=True, exit_code=0
        )

        cmd = FindCommand(path="/tmp")
        result = cmd.execute(context)

        assert result.success
        assert "/tmp/file1.txt" in result.raw_output
        assert "/tmp/file2.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_by_name(self, mock_execute, context):
        """Test find -name searching by filename pattern"""
        mock_execute.return_value = CommandResult(raw_output="./test.txt\n./data/test.txt\n", success=True, exit_code=0)

        cmd = FindCommand().with_option("-name").with_option("*.txt")
        result = cmd.execute(context)

        assert result.success
        assert "test.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_by_type_file(self, mock_execute, context):
        """Test find -type f searching for regular files"""
        mock_execute.return_value = CommandResult(raw_output="./file1.txt\n./file2.txt\n", success=True, exit_code=0)

        cmd = FindCommand().with_option("-type").with_option("f")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "file2.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_by_type_directory(self, mock_execute, context):
        """Test find -type d searching for directories"""
        mock_execute.return_value = CommandResult(raw_output="./dir1\n./dir2\n", success=True, exit_code=0)

        cmd = FindCommand().with_option("-type").with_option("d")
        result = cmd.execute(context)

        assert result.success
        assert "./dir1" in result.raw_output
        assert "./dir2" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_max_depth(self, mock_execute, context):
        """Test find -maxdepth limiting search depth"""
        mock_execute.return_value = CommandResult(raw_output="./file1.txt\n./file2.txt\n", success=True, exit_code=0)

        cmd = FindCommand().with_option("-maxdepth").with_option("1")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "file2.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_size_filter(self, mock_execute, context):
        """Test find -size filtering by file size"""
        mock_execute.return_value = CommandResult(raw_output="./large_file.txt\n", success=True, exit_code=0)

        cmd = FindCommand().with_option("-size").with_option("+1M")
        result = cmd.execute(context)

        assert result.success
        assert "large_file.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_mtime_filter(self, mock_execute, context):
        """Test find -mtime filtering by modification time"""
        mock_execute.return_value = CommandResult(raw_output="./recent_file.txt\n", success=True, exit_code=0)

        cmd = FindCommand().with_option("-mtime").with_option("-7")
        result = cmd.execute(context)

        assert result.success
        assert "recent_file.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_exec_action(self, mock_execute, context):
        """Test find -exec executing command on found files"""
        mock_execute.return_value = CommandResult(raw_output="./file1.txt\n./file2.txt\n", success=True, exit_code=0)

        cmd = FindCommand().with_option("-exec").with_option("ls").with_option("-l").with_option("{}").with_option(";")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "file2.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_delete_action(self, mock_execute, context):
        """Test find -delete removing found files"""
        mock_execute.return_value = CommandResult(raw_output="./temp1.txt\n./temp2.txt\n", success=True, exit_code=0)

        cmd = FindCommand().with_option("-delete")
        result = cmd.execute(context)

        assert result.success
        assert "temp1.txt" in result.raw_output
        assert "temp2.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_no_matches(self, mock_execute, context):
        """Test find when no files match criteria"""
        mock_execute.return_value = CommandResult(raw_output="", success=True, exit_code=0)

        cmd = FindCommand().with_option("-name").with_option("nonexistent*.txt")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0
        assert result.raw_output == ""

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_permission_denied(self, mock_execute, context):
        """Test find with permission denied"""
        mock_execute.return_value = CommandResult(
            raw_output="./allowed_file.txt\nfind: '/root': Permission denied\n",
            success=False,
            exit_code=1,
            error_message="find: '/root': Permission denied",
        )

        cmd = FindCommand("/root")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "Permission denied" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_invalid_option(self, mock_execute, context):
        """Test find with invalid option"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="find: invalid option -- 'z'"
        )

        cmd = FindCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_find_complex_criteria(self, mock_execute, context):
        """Test find with complex combined criteria"""
        mock_execute.return_value = CommandResult(raw_output="./big_text_file.txt\n", success=True, exit_code=0)

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
