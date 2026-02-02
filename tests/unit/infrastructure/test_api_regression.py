"""Testy regresyjne publicznego API po refaktorze DDD (ShellRunner, CommandFactory, domain bez infrastructure)."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from mancer.application.shell_runner import ShellRunner
from mancer.domain.interface.backend_interface import BackendInterface
from mancer.domain.shared.profile_producer import ProfileProducer
from mancer.infrastructure.factory.command_factory import CommandFactory


class TestCommandFactoryRegistry:
    """Rejestr komend – pełny zestaw i list_command_names."""

    def test_list_command_names_returns_sorted_names(self):
        factory = CommandFactory()
        names = factory.list_command_names()
        assert isinstance(names, list)
        assert names == sorted(names)
        assert "ls" in names
        assert "echo" in names
        assert "df" in names

    def test_registered_commands_include_file_system_network(self):
        factory = CommandFactory()
        names = factory.list_command_names()
        assert "mkdir" in names
        assert "mv" in names
        assert "rm" in names
        assert "touch" in names
        assert "ping" in names
        assert "curl" in names
        assert "wget" in names
        assert "ssh" in names
        assert "wc" in names
        assert "kill" in names

    def test_create_command_for_each_registered_name(self):
        factory = CommandFactory()
        for name in ["ls", "echo", "df", "mkdir", "ping"]:
            cmd = factory.create_command(name)
            assert cmd is not None, f"create_command({name!r}) should not return None"
            assert hasattr(cmd, "build_command")
            assert hasattr(cmd, "execute")


class TestShellRunnerPublicAPI:
    """ShellRunner – create_command i execute z fabryką."""

    @pytest.fixture(autouse=True)
    def _mock_logger(self, monkeypatch):
        fake = MagicMock()
        fake.initialize.return_value = None
        fake.info.return_value = None
        fake.get_command_history.return_value = []
        monkeypatch.setattr("mancer.application.shell_runner.MancerLogger.get_instance", lambda: fake)

    def test_create_command_via_runner_uses_factory(self):
        runner = ShellRunner(enable_command_logging=False)
        cmd = runner.create_command("echo")
        assert cmd is not None
        assert hasattr(cmd, "build_command")
        assert hasattr(cmd, "execute")

    def test_execute_echo_returns_success_result(self):
        runner = ShellRunner(enable_command_logging=False)
        cmd = runner.create_command("echo").add_arg("hello")
        result = runner.execute(cmd)
        assert result is not None
        assert result.success
        assert "hello" in (result.raw_output or "")


class TestProfileProducerNoInfrastructure:
    """ProfileProducer.get_connection_profile – domain bez importu infrastructure."""

    def test_get_connection_profile_returns_same_as_get_profile(self):
        producer = ProfileProducer()
        # get_connection_profile(name) powinno zwracać to samo co get_profile(name)
        profile1 = producer.get_connection_profile("nonexistent")
        profile2 = producer.get_profile("nonexistent")
        assert profile1 is profile2

    def test_profile_producer_module_does_not_import_infrastructure(self):
        import mancer.domain.shared.profile_producer as mod

        # Sprawdź, że moduł domain nie importuje pakietu infrastructure
        source = inspect.getsource(mod)
        assert "from " in source
        lines = [line.strip() for line in source.splitlines() if line.strip().startswith("from ") or line.strip().startswith("import ")]
        for line in lines:
            assert "infrastructure" not in line and "ssh_connecticer" not in line, f"domain should not import infrastructure: {line}"


class TestBackendInterfaceContract:
    """BackendInterface.execute_command – kontrakt z context_params i stdin."""

    def test_interface_execute_command_signature_includes_context_params_stdin(self):
        sig = inspect.signature(BackendInterface.execute_command)
        params = list(sig.parameters.keys())
        assert "context_params" in params
        assert "stdin" in params

    def test_bash_backend_accepts_context_params_stdin(self):
        from mancer.infrastructure.backend.bash_backend import BashBackend

        backend = BashBackend()
        # Wywołanie z dodatkowymi argumentami (zgodne z interfejsem)
        result = backend.execute_command(
            "echo ok",
            working_dir=None,
            env_vars=None,
            context_params={"live_output": False},
            stdin=None,
        )
        assert result is not None
        assert result.success
