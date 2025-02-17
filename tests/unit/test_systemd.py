import pytest
from mancer.systemd import SystemdManager
from mancer.core import Command
from unittest.mock import patch

@pytest.fixture
def systemd():
    return SystemdManager()

class TestSystemd:
    def test_list_units_command(self, systemd):
        cmd = systemd.list_units()
        assert isinstance(cmd, Command)
        assert cmd.cmd == ["systemctl", "list-units"]

    def test_status_command(self, systemd):
        cmd = systemd.status("nginx")
        assert cmd.cmd == ["systemctl", "status", "nginx"]

    def test_restart_command(self, systemd):
        cmd = systemd.restart("nginx")
        assert cmd.cmd == ["systemctl", "restart", "nginx"] 