"""
Unit tests for ls command - all scenarios in one focused file
"""

from unittest.mock import patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.system.ls_command import LsCommand


class TestLsCommand:
    """Unit tests for ls command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_basic_listing(self, mock_execute, context):
        """Test basic ls command without options"""
        mock_execute.return_value = CommandResult(raw_output="file1.txt\nfile2.txt\n", success=True, exit_code=0)

        cmd = LsCommand()
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert result.exit_code == 0
        mock_execute.assert_called_once()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_long_format(self, mock_execute, context):
        """Test ls -l with detailed output"""
        mock_execute.return_value = CommandResult(
            raw_output="-rw-r--r-- 1 user group 1024 Jan 1 12:00 file1.txt", success=True, exit_code=0
        )

        cmd = LsCommand().with_option("-l")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "1024" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_all_files(self, mock_execute, context):
        """Test ls -a showing hidden files"""
        mock_execute.return_value = CommandResult(
            raw_output=".hidden\nfile1.txt\nfile2.txt\n", success=True, exit_code=0
        )

        cmd = LsCommand().with_option("-a")
        result = cmd.execute(context)

        assert result.success
        assert ".hidden" in result.raw_output
        assert "file1.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_custom_directory(self, mock_execute, context):
        """Test ls with custom directory path"""
        mock_execute.return_value = CommandResult(raw_output="custom_file.txt\n", success=True, exit_code=0)

        cmd = LsCommand("/tmp/test_dir")
        result = cmd.execute(context)

        assert result.success
        assert "custom_file.txt" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_human_readable(self, mock_execute, context):
        """Test ls -lh with human readable sizes"""
        mock_execute.return_value = CommandResult(
            raw_output="-rw-r--r-- 1 user group 1.0K Jan 1 12:00 file1.txt", success=True, exit_code=0
        )

        cmd = LsCommand().with_option("-l").with_option("-h")
        result = cmd.execute(context)

        assert result.success
        assert "1.0K" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_nonexistent_directory(self, mock_execute, context):
        """Test ls with non-existent directory"""
        mock_execute.return_value = CommandResult(
            raw_output="",
            success=False,
            exit_code=2,
            error_message="ls: cannot access '/nonexistent': No such file or directory",
        )

        cmd = LsCommand("/nonexistent")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "No such file or directory" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_permission_denied(self, mock_execute, context):
        """Test ls with permission denied"""
        mock_execute.return_value = CommandResult(
            raw_output="",
            success=False,
            exit_code=2,
            error_message="ls: cannot open directory '/root': Permission denied",
        )

        cmd = LsCommand("/root")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "Permission denied" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_invalid_option(self, mock_execute, context):
        """Test ls with invalid option"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=2, error_message="ls: invalid option -- 'z'"
        )

        cmd = LsCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_empty_directory(self, mock_execute, context):
        """Test ls on empty directory"""
        mock_execute.return_value = CommandResult(raw_output="", success=True, exit_code=0)

        cmd = LsCommand("/tmp/empty")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0
        assert result.raw_output == ""

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_with_time_sorting(self, mock_execute, context):
        """Test ls -t sorting by modification time"""
        mock_execute.return_value = CommandResult(
            raw_output="newer_file.txt\nolder_file.txt\n", success=True, exit_code=0
        )

        cmd = LsCommand().with_option("-t")
        result = cmd.execute(context)

        assert result.success
        assert "newer_file.txt" in result.raw_output
        assert "older_file.txt" in result.raw_output
