"""
Unit tests for AptCommand (application layer).
"""

from unittest.mock import patch

import pytest

from mancer.application.commands.apt_command import AptCommand
from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult


class TestAptCommand:
    """Covers command building and execution wiring for AptCommand."""

    @pytest.fixture(autouse=True)
    def fake_state_file(self, tmp_path, monkeypatch):
        """Redirect state file operations to a temp directory to avoid touching the real FS."""
        monkeypatch.setattr(AptCommand, "APT_STATE_FILE", str(tmp_path / "apt_state.json"))
        monkeypatch.setattr(AptCommand, "_save_state", lambda self: None)

    @pytest.fixture  # type: ignore[misc]
    def context(self) -> CommandContext:
        return CommandContext(current_directory="/tmp")

    def _success(self):
        return CommandResult(raw_output="", success=True, structured_output=[])

    def _failure(self):
        return CommandResult(raw_output="", success=False, structured_output=[], exit_code=1, error_message="apt error")

    def _patch_backend(self, result):
        return patch(
            "mancer.infrastructure.backend.bash_backend.BashBackend.execute_command",
            return_value=result,
        )

    def test_apt_install_command(self, context):
        """install() should build apt install command with -y."""
        with self._patch_backend(self._success()) as mock_exec:
            cmd = AptCommand().install("nginx")
            result = cmd.execute(context)

        assert result.success
        executed = mock_exec.call_args[0][0]
        assert executed.startswith("apt install")
        assert "-y" in executed

    def test_apt_remove_command(self, context):
        """remove() should include package name and -y."""
        with self._patch_backend(self._success()) as mock_exec:
            _ = AptCommand().remove("vim").execute(context)

        executed = mock_exec.call_args[0][0]
        assert "remove" in executed and "vim" in executed and "-y" in executed

    def test_apt_update_sets_state_flag(self, context):
        """update() should include custom flag to refresh state."""
        cmd = AptCommand().update()
        assert cmd._params["command"] == "update"
        assert cmd._params.get("update_state") is True

    def test_apt_wait_if_locked_parameters(self, context):
        """wait_if_locked should pass parameters to backend."""
        with self._patch_backend(self._success()) as mock_exec:
            _ = AptCommand().wait_if_locked(max_attempts=3, sleep_time=1).execute(context)

        executed = mock_exec.call_args[0][0]
        assert "max_attempts=3" in executed
        assert "sleep_time=1" in executed

    def test_apt_check_lock_uses_custom_cmd(self, context):
        """check_if_locked should embed custom shell snippet."""
        with self._patch_backend(self._success()) as mock_exec:
            _ = AptCommand().check_if_locked().execute(context)

        executed = mock_exec.call_args[0][0]
        assert "lsof" in executed

    def test_apt_failure_propagates(self, context):
        """Command errors should be returned to the caller."""
        with self._patch_backend(self._failure()):
            result = AptCommand().install("broken").execute(context)

        assert not result.success
        assert result.error_message == "apt error"
