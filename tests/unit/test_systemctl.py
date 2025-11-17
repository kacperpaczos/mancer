"""
Unit tests for systemctl command - all scenarios in one focused file
"""

from unittest.mock import patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.command.system.systemctl_command import SystemctlCommand


class TestSystemctlCommand:
    """Unit tests for systemctl command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_status_service(self, mock_execute, context):
        """Test systemctl status for specific service"""
        mock_execute.return_value = CommandResult(
            raw_output="● ssh.service - OpenSSH Daemon\n   Loaded: loaded (/lib/systemd/system/ssh.service; enabled)\n   Active: active (running) since Mon 2024-01-01 10:00:00 UTC; 1h 30min ago\n",
            success=True,
            exit_code=0,
        )

        cmd = SystemctlCommand().with_option("status").with_option("ssh.service")
        result = cmd.execute(context)

        assert result.success
        assert "ssh.service" in result.raw_output
        assert "Active: active" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_start_service(self, mock_execute, context):
        """Test systemctl start service"""
        mock_execute.return_value = CommandResult(raw_output="", success=True, exit_code=0)

        cmd = SystemctlCommand().with_option("start").with_option("apache2.service")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_stop_service(self, mock_execute, context):
        """Test systemctl stop service"""
        mock_execute.return_value = CommandResult(raw_output="", success=True, exit_code=0)

        cmd = SystemctlCommand().with_option("stop").with_option("apache2.service")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_restart_service(self, mock_execute, context):
        """Test systemctl restart service"""
        mock_execute.return_value = CommandResult(raw_output="", success=True, exit_code=0)

        cmd = SystemctlCommand().with_option("restart").with_option("nginx.service")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_enable_service(self, mock_execute, context):
        """Test systemctl enable service"""
        mock_execute.return_value = CommandResult(
            raw_output="Created symlink /etc/systemd/system/multi-user.target.wants/myapp.service → /lib/systemd/system/myapp.service.\n",
            success=True,
            exit_code=0,
        )

        cmd = SystemctlCommand().with_option("enable").with_option("myapp.service")
        result = cmd.execute(context)

        assert result.success
        assert "Created symlink" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_disable_service(self, mock_execute, context):
        """Test systemctl disable service"""
        mock_execute.return_value = CommandResult(
            raw_output="Removed /etc/systemd/system/multi-user.target.wants/myapp.service.\n", success=True, exit_code=0
        )

        cmd = SystemctlCommand().with_option("disable").with_option("myapp.service")
        result = cmd.execute(context)

        assert result.success
        assert "Removed" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_list_units(self, mock_execute, context):
        """Test systemctl list-units"""
        mock_execute.return_value = CommandResult(
            raw_output="UNIT                           LOAD   ACTIVE SUB     DESCRIPTION\nssh.service                    loaded active running OpenSSH Daemon\napache2.service                loaded active running The Apache HTTP Server\n",
            success=True,
            exit_code=0,
        )

        cmd = SystemctlCommand().with_option("list-units")
        result = cmd.execute(context)

        assert result.success
        assert "UNIT" in result.raw_output
        assert "ssh.service" in result.raw_output
        assert "apache2.service" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_list_unit_files(self, mock_execute, context):
        """Test systemctl list-unit-files"""
        mock_execute.return_value = CommandResult(
            raw_output="UNIT FILE                     STATE\nssh.service                    enabled\napache2.service                disabled\n",
            success=True,
            exit_code=0,
        )

        cmd = SystemctlCommand().with_option("list-unit-files")
        result = cmd.execute(context)

        assert result.success
        assert "UNIT FILE" in result.raw_output
        assert "ssh.service" in result.raw_output
        assert "enabled" in result.raw_output
        assert "disabled" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_is_active(self, mock_execute, context):
        """Test systemctl is-active"""
        mock_execute.return_value = CommandResult(raw_output="active\n", success=True, exit_code=0)

        cmd = SystemctlCommand().with_option("is-active").with_option("ssh.service")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output.strip() == "active"

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_is_enabled(self, mock_execute, context):
        """Test systemctl is-enabled"""
        mock_execute.return_value = CommandResult(raw_output="enabled\n", success=True, exit_code=0)

        cmd = SystemctlCommand().with_option("is-enabled").with_option("ssh.service")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output.strip() == "enabled"

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_daemon_reload(self, mock_execute, context):
        """Test systemctl daemon-reload"""
        mock_execute.return_value = CommandResult(raw_output="", success=True, exit_code=0)

        cmd = SystemctlCommand().with_option("daemon-reload")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_show_service(self, mock_execute, context):
        """Test systemctl show service details"""
        mock_execute.return_value = CommandResult(
            raw_output="Id=ssh.service\nNames=ssh.service\nDescription=OpenSSH Daemon\nLoadState=loaded\nActiveState=active\n",
            success=True,
            exit_code=0,
        )

        cmd = SystemctlCommand().with_option("show").with_option("ssh.service")
        result = cmd.execute(context)

        assert result.success
        assert "Id=ssh.service" in result.raw_output
        assert "ActiveState=active" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_service_not_found(self, mock_execute, context):
        """Test systemctl with non-existent service"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="Unit nonexistent.service could not be found."
        )

        cmd = SystemctlCommand().with_option("status").with_option("nonexistent.service")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "could not be found" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_permission_denied(self, mock_execute, context):
        """Test systemctl when permission denied"""
        mock_execute.return_value = CommandResult(
            raw_output="",
            success=False,
            exit_code=1,
            error_message="Access denied. You need to be root to perform this operation.",
        )

        cmd = SystemctlCommand().with_option("start").with_option("system.service")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "Access denied" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_systemctl_invalid_option(self, mock_execute, context):
        """Test systemctl with invalid option"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=1, error_message="systemctl: invalid option -- 'z'"
        )

        cmd = SystemctlCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.backend.bash_backend.Bash_backend.BashBackend.execute_command")
    def test_systemctl_mask_service(self, mock_execute, context):
        """Test systemctl mask service"""
        mock_execute.return_value = CommandResult(
            raw_output="Created symlink /etc/systemd/system/bad.service → /dev/null.\n", success=True, exit_code=0
        )

        cmd = SystemctlCommand().with_option("mask").with_option("bad.service")
        result = cmd.execute(context)

        assert result.success
        assert "Created symlink" in result.raw_output
