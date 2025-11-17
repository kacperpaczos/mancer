"""
Unit tests for df command - all scenarios in one focused file
"""

from unittest.mock import patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.system.df_command import DfCommand


class TestDfCommand:
    """Unit tests for df command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_basic_disk_usage(self, mock_execute, context):
        """Test basic df command showing disk usage"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem     1K-blocks  Used Available Use% Mounted on\n/dev/sda1       10000000 5000000  4500000  53% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand()
        result = cmd.execute(context)

        assert result.success
        assert "Filesystem" in result.raw_output
        assert "1K-blocks" in result.raw_output
        assert "/dev/sda1" in result.raw_output
        assert "53%" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_human_readable(self, mock_execute, context):
        """Test df -h with human readable sizes"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        9.6G  4.8G  4.3G  53% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand().with_option("-h")
        result = cmd.execute(context)

        assert result.success
        assert "Size" in result.raw_output
        assert "9.6G" in result.raw_output
        assert "4.8G" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_inode_usage(self, mock_execute, context):
        """Test df -i showing inode usage"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem     Inodes IUsed IFree IUse% Mounted on\n/dev/sda1      1000000 50000 950000    5% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand().with_option("-i")
        result = cmd.execute(context)

        assert result.success
        assert "Inodes" in result.raw_output
        assert "IUsed" in result.raw_output
        assert "IFree" in result.raw_output
        assert "5%" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_specific_filesystem(self, mock_execute, context):
        """Test df for specific filesystem"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem     1K-blocks  Used Available Use% Mounted on\n/dev/sda1       10000000 5000000  4500000  53% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand("/dev/sda1")
        result = cmd.execute(context)

        assert result.success
        assert "/dev/sda1" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_all_filesystems(self, mock_execute, context):
        """Test df -a showing all filesystems"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem     1K-blocks  Used Available Use% Mounted on\n/dev/sda1       10000000 5000000  4500000  53% /\ntmpfs             512000        0   512000   0% /tmp\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand().with_option("-a")
        result = cmd.execute(context)

        assert result.success
        assert "/dev/sda1" in result.raw_output
        assert "tmpfs" in result.raw_output
        assert "/tmp" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_local_filesystems_only(self, mock_execute, context):
        """Test df -l showing only local filesystems"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem     1K-blocks  Used Available Use% Mounted on\n/dev/sda1       10000000 5000000  4500000  53% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand().with_option("-l")
        result = cmd.execute(context)

        assert result.success
        assert "/dev/sda1" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_filesystem_type(self, mock_execute, context):
        """Test df -T showing filesystem types"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem     Type 1K-blocks  Used Available Use% Mounted on\n/dev/sda1      ext4 10000000 5000000  4500000  53% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand().with_option("-T")
        result = cmd.execute(context)

        assert result.success
        assert "Type" in result.raw_output
        assert "ext4" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_portability_mode(self, mock_execute, context):
        """Test df -P with POSIX output format"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem         1024-blocks  Used Available Capacity Mounted on\n/dev/sda1              9765625 4882812  4394531      53% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand().with_option("-P")
        result = cmd.execute(context)

        assert result.success
        assert "1024-blocks" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_specific_mount_point(self, mock_execute, context):
        """Test df for specific mount point"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem     1K-blocks  Used Available Use% Mounted on\n/dev/sda1       10000000 5000000  4500000  53% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand("/")
        result = cmd.execute(context)

        assert result.success
        assert "/" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_no_space_left(self, mock_execute, context):
        """Test df when filesystem is full"""
        mock_execute.return_value = CommandResult(
            raw_output="Filesystem     1K-blocks  Used Available Use% Mounted on\n/dev/sda1       10000000 10000000        0 100% /\n",
            success=True,
            exit_code=0,
        )

        cmd = DfCommand()
        result = cmd.execute(context)

        assert result.success
        assert "100%" in result.raw_output
        assert "0" in result.raw_output.split()[-2]  # Available space should be 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_df_invalid_option(self, mock_execute, context):
        """Test df with invalid option"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="df: invalid option -- 'z'"
        )

        cmd = DfCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message
