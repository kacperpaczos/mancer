import pytest
from mancer import systemd
from unittest.mock import patch

@pytest.mark.integration
class TestSystemdIntegration:
    @pytest.mark.privileged
    def test_list_units_integration(self):
        result = systemd.list_units().run()
        assert result.return_code == 0
        assert len(result.stdout) > 0

    @pytest.mark.privileged
    def test_service_operations(self):
        # Test statusu usługi z mockowaniem
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "● ssh.service - OpenBSD Secure Shell server\n   Active: active (running)"
            mock_run.return_value.returncode = 0
            
            result = systemd.status("ssh").run()
            assert result.return_code == 0
            assert "Active: active" in result.stdout

        # Test restartu usługi
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = PermissionError("Operation not permitted")
            result = systemd.restart("ssh").run()
            assert result.return_code == 1
            assert "Operation not permitted" in result.stderr 