"""
Unit tests for ls command - all scenarios in one focused file
"""

from unittest.mock import patch, MagicMock

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.ls_command import LsCommand


class TestLsCommand:
    """Unit tests for ls command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_basic_listing(self, mock_get_backend, context):
        """Test basic ls command without options"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file1.txt\nfile2.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand()
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert result.exit_code == 0
        mock_backend.execute.assert_called_once()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_long_format(self, mock_get_backend, context):
        """Test ls -l with detailed output"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "-rw-r--r-- 1 user group 1024 Jan 1 12:00 file1.txt", "")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand().with_option("-l")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "1024" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_all_files(self, mock_get_backend, context):
        """Test ls -a showing hidden files"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, ".hidden\nfile1.txt\nfile2.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand().with_option("-a")
        result = cmd.execute(context)

        assert result.success
        assert ".hidden" in result.raw_output
        assert "file1.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_custom_directory(self, mock_get_backend, context):
        """Test ls with custom directory path"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "custom_file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand("/tmp/test_dir")
        result = cmd.execute(context)

        assert result.success
        assert "custom_file.txt" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_human_readable(self, mock_get_backend, context):
        """Test ls -lh with human readable sizes"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "-rw-r--r-- 1 user group 1.0K Jan 1 12:00 file1.txt", "")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand().with_option("-l").with_option("-h")
        result = cmd.execute(context)

        assert result.success
        assert "1.0K" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_nonexistent_directory(self, mock_get_backend, context):
        """Test ls with non-existent directory"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (2, "", "ls: cannot access '/nonexistent': No such file or directory")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand("/nonexistent")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "No such file or directory" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_permission_denied(self, mock_get_backend, context):
        """Test ls with permission denied"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (2, "", "ls: cannot open directory '/root': Permission denied")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand("/root")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "Permission denied" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_invalid_option(self, mock_get_backend, context):
        """Test ls with invalid option"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (2, "", "ls: invalid option -- 'z'")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_empty_directory(self, mock_get_backend, context):
        """Test ls on empty directory"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "", "")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand("/tmp/empty")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0
        assert result.raw_output == ""

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ls_with_time_sorting(self, mock_get_backend, context):
        """Test ls -t sorting by modification time"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "newer_file.txt\nolder_file.txt\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = LsCommand().with_option("-t")
        result = cmd.execute(context)

        assert result.success
        assert "newer_file.txt" in result.raw_output
        assert "older_file.txt" in result.raw_output
