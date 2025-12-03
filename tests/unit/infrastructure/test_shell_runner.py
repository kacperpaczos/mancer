from __future__ import annotations

from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from mancer.application.shell_runner import ShellRunner
from mancer.domain.model.command_context import ExecutionMode
from mancer.domain.model.command_result import CommandResult


def _result(value: str) -> CommandResult:
    return CommandResult(
        raw_output=value,
        success=True,
        structured_output=pl.DataFrame({"value": [value]}),
        exit_code=0,
    )


class DummyCommand:
    def __init__(self, name: str = "dummy"):
        self.name = name
        self.calls = 0

    def __call__(self, context):
        self.calls += 1
        context.add_to_history(f"{self.name}:{self.calls}")
        return _result(f"{self.name}:{self.calls}")

    execute = __call__

    def build_command(self) -> str:
        return f"{self.name} --flag"

    def clone(self) -> "DummyCommand":
        return DummyCommand(self.name)

    def __str__(self) -> str:
        return self.build_command()


@pytest.fixture(autouse=True)
def mock_logger(monkeypatch):
    fake_logger = MagicMock()
    fake_logger.initialize.return_value = None
    fake_logger.info.return_value = None
    fake_logger.get_command_history.return_value = []
    monkeypatch.setattr("mancer.application.shell_runner.MancerLogger.get_instance", lambda: fake_logger)
    return fake_logger


class TestShellRunner:
    def test_execute_uses_cache_when_enabled(self):
        runner = ShellRunner(enable_cache=True, enable_command_logging=False)
        command = DummyCommand("cached")

        first = runner.execute(command)
        second = runner.execute(command)

        assert first is second
        assert command.calls == 1  # cached result reused

    def test_execute_live_output_bypasses_cache(self):
        runner = ShellRunner(enable_cache=True, enable_command_logging=False)
        command = DummyCommand("live")

        runner.execute(command, live_output=True)
        runner.execute(command, live_output=True)

        assert command.calls == 2  # no caching in live mode

    def test_register_and_get_command_returns_clone(self):
        runner = ShellRunner(enable_command_logging=False)
        stored = DummyCommand("preconfigured")

        runner.register_command("my-command", stored)
        retrieved = runner.get_command("my-command")

        assert isinstance(retrieved, DummyCommand)
        assert retrieved is not stored
        assert retrieved.build_command() == stored.build_command()

    def test_set_remote_execution_and_get_backend(self, mock_logger):
        runner = ShellRunner(enable_command_logging=False)
        with patch("mancer.application.shell_runner.SshBackendFactory.create_backend") as mock_backend:
            backend_instance = object()
            mock_backend.return_value = backend_instance

            runner.set_remote_execution(host="example.com", user="dev", port=44)
            backend = runner.get_backend()

        assert backend is backend_instance
        assert runner._context.execution_mode == ExecutionMode.REMOTE
        mock_logger.info.assert_called()

