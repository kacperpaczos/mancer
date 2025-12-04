from __future__ import annotations

from unittest.mock import Mock, patch

import polars as pl
import pytest

from mancer.application.commands.base_command import BaseCommand
from mancer.domain.model.command_context import CommandContext, ExecutionMode
from mancer.domain.model.command_result import CommandResult

"""Testy jednostkowe dla BaseCommand w nowym pakiecie tests/unit."""


@pytest.fixture()  # type: ignore[misc]
def context() -> CommandContext:
    return CommandContext()


def _command_result(output: str = "test output") -> CommandResult:
    return CommandResult(
        raw_output=output,
        success=True,
        structured_output=pl.DataFrame({"value": [output]}),
        exit_code=0,
    )


class TestBaseCommand:
    def setup_method(self) -> None:
        self.command = BaseCommand("test_cmd")

    def test_initialization_sets_defaults(self) -> None:
        cmd = BaseCommand("ls")
        assert cmd._command_name == "ls"
        assert cmd._params == {}
        assert cmd._options == []

    def test_with_param_chaining(self) -> None:
        result = self.command.with_param("param1", "value1").with_param("param2", 123)
        assert result is self.command
        assert self.command._params["param1"] == "value1"
        assert self.command._params["param2"] == 123

    def test_with_option_allows_duplicates(self) -> None:
        cmd = BaseCommand("ls")
        cmd.with_option("l").with_option("l")
        assert cmd._options.count("l") == 2

    def test_build_command_variants(self) -> None:
        cmd = (
            BaseCommand("find")
            .with_option("L")
            .with_option("follow-symlinks")
            .with_param("type", "f")
            .with_param("name", "*.py")
            .with_param("quiet", False)
            .with_param("recursive", True)
            .with_param("command", "search")
        )
        built = cmd.build_command()
        assert built.startswith("find search")
        assert "-L" in built and "--follow-symlinks" in built
        assert "--type f" in built and "--name *.py" in built
        assert "--recursive" in built and "--quiet" not in built

    def test_build_command_with_regular_params(self) -> None:
        cmd = BaseCommand("apt").with_param("package", "nginx").with_param("command", "install")
        assert cmd.build_command() == "apt install nginx"

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend")
    def test_execute_local_command(self, mock_backend_cls: Mock, context: CommandContext) -> None:
        context.execution_mode = ExecutionMode.LOCAL
        context.add_to_history = Mock()
        backend_instance = Mock()
        backend_instance.execute_command.return_value = _command_result()
        mock_backend_cls.return_value = backend_instance

        result = self.command.execute(context)

        assert result.raw_output == "test output"
        context.add_to_history.assert_called_once_with("test_cmd")
        backend_instance.execute_command.assert_called_once()

    @patch("mancer.infrastructure.backend.ssh_backend.SshBackendFactory.create_backend")
    def test_execute_remote_command(self, mock_backend_factory: Mock, context: CommandContext) -> None:
        context.execution_mode = ExecutionMode.REMOTE
        context.add_to_history = Mock()
        remote = Mock()
        remote.host = "example.com"
        remote.user = "test"
        remote.port = 22
        remote.key_file = None
        remote.password = "pw"
        remote.use_sudo = False
        remote.sudo_password = None
        context.remote_host = remote

        backend = Mock()
        backend.execute_command.return_value = _command_result("remote")
        mock_backend_factory.return_value = backend

        result = self.command.execute(context)

        assert result.raw_output == "remote"
        context.add_to_history.assert_called_once_with("test_cmd")
        mock_backend_factory.assert_called_once_with(
            hostname="example.com", username="test", port=22, key_filename=None, password="pw"
        )

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend")
    def test_execute_with_input_result(self, mock_backend_cls: Mock, context: CommandContext) -> None:
        context.execution_mode = ExecutionMode.LOCAL
        context.add_to_history = Mock()
        backend = Mock()
        backend.execute_command.return_value = _command_result()
        mock_backend_cls.return_value = backend

        stdin_result = CommandResult(
            raw_output="input data",
            success=True,
            structured_output=pl.DataFrame({"value": ["input data"]}),
            exit_code=0,
        )

        self.command.execute(context, input_result=stdin_result)

        backend.execute_command.assert_called_once()
        _, _, _, _, stdin = backend.execute_command.call_args[0]
        assert stdin == "input data"

    def test_clone_creates_independent_copy(self) -> None:
        original = BaseCommand("find").with_param("type", "f").with_option("L")
        cloned = original.clone()
        cloned.with_param("new", "value").with_option("follow")

        assert cloned is not original
        assert cloned._params != original._params
        assert "follow" in cloned._options
        assert "follow" not in original._options

    def test_str_returns_built_command(self) -> None:
        cmd = BaseCommand("ls").with_option("l").with_param("type", "f")
        assert str(cmd) == cmd.build_command()
