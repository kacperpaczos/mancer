from __future__ import annotations

import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mancer.infrastructure.backend.bash_backend import BashBackend

"""Testy jednostkowe BashBackend z pełnym mockowaniem subprocess."""


class ImmediateThread:
    """Helper thread that runs target immediately for deterministic tests."""

    def __init__(self, target, args):
        self._target = target
        self._args = args
        self.daemon = False

    def start(self):
        self._target(*self._args)


class TestBashBackend:
    def setup_method(self) -> None:
        self.backend = BashBackend()

    @patch("mancer.infrastructure.backend.bash_backend.subprocess.run")
    def test_execute_command_standard_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

        result = self.backend.execute_command(
            "echo ok",
            working_dir="/tmp",
            env_vars={"FOO": "bar"},
            stdin="input",
        )

        assert result.success
        assert result.raw_output == "ok\n"
        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        assert kwargs["cwd"] == "/tmp"
        assert kwargs["input"] == "input"
        assert kwargs["shell"] is True

    @patch("mancer.infrastructure.backend.bash_backend.subprocess.run")
    def test_execute_command_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = SimpleNamespace(returncode=1, stdout="", stderr="boom")

        result = self.backend.execute_command("failing")

        assert not result.success
        assert result.exit_code == 1
        assert result.error_message == "boom"

    @patch("mancer.infrastructure.backend.bash_backend.subprocess.run")
    def test_execute_command_exception(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = RuntimeError("run failed")

        result = self.backend.execute_command("echo")

        assert not result.success
        assert result.exit_code == -1
        assert "run failed" in (result.error_message or "")

    @pytest.mark.skip(reason="Live output test requires complex threading mock - pending refactor")  # type: ignore[misc]
    def test_execute_command_live_output(self) -> None:
        """Test live output mode (complex threading - skipped for now)."""
        pass

    @patch("mancer.infrastructure.backend.bash_backend.subprocess.Popen")
    def test_execute_method_success(self, mock_popen: MagicMock) -> None:
        process = MagicMock()
        process.communicate.return_value = ("stdout", "")
        process.returncode = 0
        mock_popen.return_value = process

        exit_code, stdout, stderr = self.backend.execute("echo ok", input_data=None, working_dir="/tmp", timeout=5)

        assert exit_code == 0
        assert stdout == "stdout"
        assert stderr == ""
        mock_popen.assert_called_once()

    @patch("mancer.infrastructure.backend.bash_backend.subprocess.Popen")
    def test_execute_method_timeout(self, mock_popen: MagicMock) -> None:
        process = MagicMock()
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="sleep 10", timeout=1),
            ("", "after-timeout"),
        ]
        mock_popen.return_value = process

        exit_code, stdout, stderr = self.backend.execute("sleep 10", timeout=1)

        assert exit_code == -1
        assert stderr.startswith("Command timed out")
        process.kill.assert_called_once()
        assert stdout == ""

    @patch("mancer.infrastructure.backend.bash_backend.subprocess.Popen")
    def test_execute_method_keyboard_interrupt(self, mock_popen: MagicMock) -> None:
        process = MagicMock()
        process.communicate.side_effect = KeyboardInterrupt()
        mock_popen.return_value = process

        exit_code, stdout, stderr = self.backend.execute("long_command")

        assert exit_code == -1
        assert stderr == "Command interrupted by user"
        process.kill.assert_called_once()

    @patch("mancer.infrastructure.backend.bash_backend.subprocess.Popen")
    def test_execute_method_generic_exception(self, mock_popen: MagicMock) -> None:
        mock_popen.side_effect = OSError("popen failed")

        exit_code, stdout, stderr = self.backend.execute("cmd")

        assert exit_code == -1
        assert stdout == ""
        assert "popen failed" in stderr

    def test_parse_output_success(self) -> None:
        result = self.backend.parse_output("echo", "line1\nline2\n", 0, "")

        assert result.success
        assert result.structured_output == ["line1", "line2"]

    def test_parse_output_failure(self) -> None:
        result = self.backend.parse_output("echo", "", 2, "boom")

        assert not result.success
        assert result.error_message == "boom"

    def test_build_command_string(self) -> None:
        command = self.backend.build_command_string(
            "find",
            options=["-L"],
            params={"name": "*.py", "d": 2},
            flags=["--follow-symlinks"],
        )

        assert command.startswith("find")
        assert "-L" in command
        assert "--follow-symlinks" in command
        assert "--name='*.py'" in command
        assert "-d 2" in command
