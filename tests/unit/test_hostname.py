"""
Unit tests for hostname command - all scenarios in one focused file
"""

from unittest.mock import patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.system.hostname_command import HostnameCommand


class TestHostnameCommand:
    """Unit tests for hostname command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_basic(self, mock_execute, context):
        """Test basic hostname command"""
        mock_execute.return_value = CommandResult(raw_output="myhost\n", success=True, exit_code=0)

        cmd = HostnameCommand()
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output.strip() == "myhost"
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_short_name(self, mock_execute, context):
        """Test hostname -s showing short hostname"""
        mock_execute.return_value = CommandResult(raw_output="myhost\n", success=True, exit_code=0)

        cmd = HostnameCommand().short()
        result = cmd.execute(context)

        assert result.success
        assert "myhost" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_domain_name(self, mock_execute, context):
        """Test hostname -d showing domain name"""
        mock_execute.return_value = CommandResult(raw_output="example.com\n", success=True, exit_code=0)

        cmd = HostnameCommand().domain()
        result = cmd.execute(context)

        assert result.success
        assert "example.com" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_fqdn(self, mock_execute, context):
        """Test hostname -f showing fully qualified domain name"""
        mock_execute.return_value = CommandResult(raw_output="myhost.example.com\n", success=True, exit_code=0)

        cmd = HostnameCommand().fqdn()
        result = cmd.execute(context)

        assert result.success
        assert "myhost.example.com" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_ip_address(self, mock_execute, context):
        """Test hostname -i showing IP address"""
        mock_execute.return_value = CommandResult(raw_output="192.168.1.100\n", success=True, exit_code=0)

        cmd = HostnameCommand().ip_address()
        result = cmd.execute(context)

        assert result.success
        assert "192.168.1.100" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_all_ip_addresses(self, mock_execute, context):
        """Test hostname -I showing all IP addresses"""
        mock_execute.return_value = CommandResult(raw_output="192.168.1.100 10.0.0.50\n", success=True, exit_code=0)

        cmd = HostnameCommand().all_ip_addresses()
        result = cmd.execute(context)

        assert result.success
        assert "192.168.1.100" in result.raw_output
        assert "10.0.0.50" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_aliases(self, mock_execute, context):
        """Test hostname -a showing aliases"""
        mock_execute.return_value = CommandResult(raw_output="alias1 alias2\n", success=True, exit_code=0)

        cmd = HostnameCommand().aliases()
        result = cmd.execute(context)

        assert result.success
        assert "alias1" in result.raw_output
        assert "alias2" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_nis_domain(self, mock_execute, context):
        """Test hostname -y showing NIS domain name"""
        mock_execute.return_value = CommandResult(raw_output="nisdomain\n", success=True, exit_code=0)

        cmd = HostnameCommand().nis_domain()
        result = cmd.execute(context)

        assert result.success
        assert "nisdomain" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_boot_id(self, mock_execute, context):
        """Test hostname -b showing boot ID (if supported)"""
        mock_execute.return_value = CommandResult(raw_output="boot-id-123\n", success=True, exit_code=0)

        cmd = HostnameCommand().boot_id()
        result = cmd.execute(context)

        assert result.success
        assert "boot-id-123" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_set_hostname(self, mock_execute, context):
        """Test hostname setting new hostname"""
        mock_execute.return_value = CommandResult(raw_output="", success=True, exit_code=0)

        cmd = HostnameCommand("newhostname")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_permission_denied(self, mock_execute, context):
        """Test hostname when permission denied for setting"""
        mock_execute.return_value = CommandResult(
            raw_output="",
            success=False,
            exit_code=1,
            error_message="hostname: you must be root to change the host name",
        )

        cmd = HostnameCommand("newhostname")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "you must be root" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_hostname_invalid_option(self, mock_execute, context):
        """Test hostname with invalid option"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="hostname: invalid option -- 'z'"
        )

        cmd = HostnameCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message
