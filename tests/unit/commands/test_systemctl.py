"""
Unit tests for systemctl command - all scenarios in one focused file
"""

from unittest.mock import MagicMock, patch

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

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_status_service(self, mock_get_backend, context):
        """Test systemctl status for specific service"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output=(
                "● ssh.service - OpenSSH Daemon\n"
                "   Loaded: loaded (/lib/systemd/system/ssh.service; enabled)\n"
                "   Active: active (running) since Mon 2024-01-01 10:00:00 UTC; 1h 30min ago\n"
            ),
            success=True,
            structured_output=[
                "● ssh.service - OpenSSH Daemon",
                "   Loaded: loaded (/lib/systemd/system/ssh.service; enabled)",
                "   Active: active (running) since Mon 2024-01-01 10:00:00 UTC; 1h 30min ago",
            ],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("status").with_option("ssh.service")
        result = cmd.execute(context)

        assert result.success
        assert "ssh.service" in result.raw_output
        assert "Active: active" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_start_service(self, mock_get_backend, context):
        """Test systemctl start service"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="",
            success=True,
            structured_output=[],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("start").with_option("apache2.service")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_stop_service(self, mock_get_backend, context):
        """Test systemctl stop service"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="",
            success=True,
            structured_output=[],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("stop").with_option("apache2.service")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_restart_service(self, mock_get_backend, context):
        """Test systemctl restart service"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="",
            success=True,
            structured_output=[],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("restart").with_option("nginx.service")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_enable_service(self, mock_get_backend, context):
        """Test systemctl enable service"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output=(
                "Created symlink /etc/systemd/system/multi-user.target.wants/myapp.service → "
                "/lib/systemd/system/myapp.service.\n"
            ),
            success=True,
            structured_output=[
                (
                    "Created symlink /etc/systemd/system/multi-user.target.wants/myapp.service "
                    "→ /lib/systemd/system/myapp.service."
                )
            ],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("enable").with_option("myapp.service")
        result = cmd.execute(context)

        assert result.success
        assert "Created symlink" in result.raw_output
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_disable_service(self, mock_get_backend, context):
        """Test systemctl disable service"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="Removed /etc/systemd/system/multi-user.target.wants/myapp.service.\n",
            success=True,
            structured_output=["Removed /etc/systemd/system/multi-user.target.wants/myapp.service."],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("disable").with_option("myapp.service")
        result = cmd.execute(context)

        assert result.success
        assert "Removed" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_list_units(self, mock_get_backend, context):
        """Test systemctl list-units"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output=(
                "UNIT                           LOAD   ACTIVE SUB     DESCRIPTION\n"
                "ssh.service                    loaded active running OpenSSH Daemon\n"
                "apache2.service                loaded active running The Apache HTTP Server\n"
            ),
            success=True,
            structured_output=[
                "UNIT                           LOAD   ACTIVE SUB     DESCRIPTION",
                "ssh.service                    loaded active running OpenSSH Daemon",
                "apache2.service                loaded active running The Apache HTTP Server",
            ],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("list-units")
        result = cmd.execute(context)

        assert result.success
        assert "UNIT" in result.raw_output
        assert "ssh.service" in result.raw_output
        assert "apache2.service" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_list_unit_files(self, mock_get_backend, context):
        """Test systemctl list-unit-files"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output=(
                "UNIT FILE                     STATE\n"
                "ssh.service                    enabled\n"
                "apache2.service                disabled\n"
            ),
            success=True,
            structured_output=[
                "UNIT FILE                     STATE",
                "ssh.service                    enabled",
                "apache2.service                disabled",
            ],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("list-unit-files")
        result = cmd.execute(context)

        assert result.success
        assert "UNIT FILE" in result.raw_output
        assert "ssh.service" in result.raw_output
        assert "enabled" in result.raw_output
        assert "disabled" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_is_active(self, mock_get_backend, context):
        """Test systemctl is-active"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="active\n",
            success=True,
            structured_output=["active"],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("is-active").with_option("ssh.service")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output.strip() == "active"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_is_enabled(self, mock_get_backend, context):
        """Test systemctl is-enabled"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="enabled\n",
            success=True,
            structured_output=["enabled"],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("is-enabled").with_option("ssh.service")
        result = cmd.execute(context)

        assert result.success
        assert result.raw_output.strip() == "enabled"

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_daemon_reload(self, mock_get_backend, context):
        """Test systemctl daemon-reload"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="",
            success=True,
            structured_output=[],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("daemon-reload")
        result = cmd.execute(context)

        assert result.success
        assert result.exit_code == 0

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_show_service(self, mock_get_backend, context):
        """Test systemctl show service details"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output=(
                "Id=ssh.service\nNames=ssh.service\nDescription=OpenSSH Daemon\n"
                "LoadState=loaded\nActiveState=active\n"
            ),
            success=True,
            structured_output=[
                "Id=ssh.service",
                "Names=ssh.service",
                "Description=OpenSSH Daemon",
                "LoadState=loaded",
                "ActiveState=active",
            ],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("show").with_option("ssh.service")
        result = cmd.execute(context)

        assert result.success
        assert "Id=ssh.service" in result.raw_output
        assert "ActiveState=active" in result.raw_output

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_service_not_found(self, mock_get_backend, context):
        """Test systemctl with non-existent service"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="",
            success=False,
            structured_output=[],
            exit_code=1,
            error_message="Unit nonexistent.service could not be found.",
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("status").with_option("nonexistent.service")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "could not be found" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_permission_denied(self, mock_get_backend, context):
        """Test systemctl when permission denied"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="",
            success=False,
            structured_output=[],
            exit_code=1,
            error_message="Access denied. You need to be root to perform this operation.",
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("start").with_option("system.service")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "Access denied" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_invalid_option(self, mock_get_backend, context):
        """Test systemctl with invalid option"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="",
            success=False,
            structured_output=[],
            exit_code=1,
            error_message="systemctl: invalid option -- 'z'",
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("-z")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1
        assert "invalid option" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_systemctl_mask_service(self, mock_get_backend, context):
        """Test systemctl mask service"""
        mock_backend = MagicMock()
        mock_backend.execute_command.return_value = CommandResult(
            raw_output="Created symlink /etc/systemd/system/bad.service → /dev/null.\n",
            success=True,
            structured_output=["Created symlink /etc/systemd/system/bad.service → /dev/null."],
            exit_code=0,
        )
        mock_get_backend.return_value = mock_backend

        cmd = SystemctlCommand().with_option("mask").with_option("bad.service")
        result = cmd.execute(context)

        assert result.success
        assert "Created symlink" in result.raw_output
