"""
Unit tests for ps command - all scenarios in one focused file
"""

from unittest.mock import MagicMock, patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.ps_command import PsCommand


class TestPsCommand:
    """Unit tests for ps command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_basic_process_list(self, mock_get_backend, context):
        """Test basic ps command showing current processes"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            "  PID TTY          TIME CMD\n 1234 pts/0    00:00:01 bash\n 5678 pts/0    00:00:00 ps\n",
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand()
        result = cmd.execute(context)

        assert result.success
        assert "PID" in result.raw_output
        assert "bash" in result.raw_output
        assert "ps" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_all_processes(self, mock_get_backend, context):
        """Test ps -e showing all processes"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            "  PID TTY          TIME CMD\n    1 ?        00:00:02 systemd\n  123 ?        00:00:01 init\n",
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-e")
        result = cmd.execute(context)

        assert result.success
        assert "systemd" in result.raw_output
        assert "init" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_full_format(self, mock_get_backend, context):
        """Test ps -f full format listing"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            (
                "UID        PID  PPID  C STIME TTY          TIME CMD\n"
                "user      1234  1230  0 12:00 pts/0    00:00:01 bash\n"
            ),
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-f")
        result = cmd.execute(context)

        assert result.success
        assert "UID" in result.raw_output
        assert "PPID" in result.raw_output
        assert "bash" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_long_format(self, mock_get_backend, context):
        """Test ps -l long format listing"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            (
                "F   UID   PID  PPID PRI  NI    VSZ   RSS WCHAN  STAT TTY        TIME COMMAND\n"
                "4     0  1234  1230  20   0   1234   456 -      Ss   pts/0      0:01 bash\n"
            ),
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-l")
        result = cmd.execute(context)

        assert result.success
        assert "VSZ" in result.raw_output
        assert "RSS" in result.raw_output
        assert "STAT" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_user_processes(self, mock_get_backend, context):
        """Test ps -u showing user-oriented format"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            (
                "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n"
                "user      1234  0.0  0.1   1234   456 pts/0    Ss   12:00   0:01 bash\n"
            ),
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-u")
        result = cmd.execute(context)

        assert result.success
        assert "%CPU" in result.raw_output
        assert "%MEM" in result.raw_output
        assert "START" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_process_tree(self, mock_get_backend, context):
        """Test ps -H showing process hierarchy"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            "  PID TTY          TIME CMD\n 1230 ?        00:00:01 init\n  1234 pts/0    00:00:01  bash\n",
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-H")
        result = cmd.execute(context)

        assert result.success
        assert "init" in result.raw_output
        assert "bash" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_by_pid(self, mock_get_backend, context):
        """Test ps -p filtering by specific PID"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "  PID TTY          TIME CMD\n 1234 pts/0    00:00:01 bash\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-p").with_option("1234")
        result = cmd.execute(context)

        assert result.success
        assert "1234" in result.raw_output
        assert "bash" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_by_command_name(self, mock_get_backend, context):
        """Test ps -C filtering by command name"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "  PID TTY          TIME CMD\n 1234 pts/0    00:00:01 bash\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-C").with_option("bash")
        result = cmd.execute(context)

        assert result.success
        assert "bash" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_sort_by_memory(self, mock_get_backend, context):
        """Test ps --sort=-%mem sorting by memory usage"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            "  PID TTY          TIME CMD\n 5678 pts/0    00:00:01 memory_hungry\n 1234 pts/0    00:00:01 bash\n",
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("--sort=-%mem")
        result = cmd.execute(context)

        assert result.success
        assert "memory_hungry" in result.raw_output
        assert "bash" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_no_processes_found(self, mock_get_backend, context):
        """Test ps when filtering results in no matches"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "")
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-p").with_option("99999")  # Non-existent PID
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert result.raw_output == ""

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_ps_invalid_option(self, mock_get_backend, context):
        """Test ps with invalid option"""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "ps: invalid option -- 'z'")
        mock_get_backend.return_value = mock_backend

        cmd = PsCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message
