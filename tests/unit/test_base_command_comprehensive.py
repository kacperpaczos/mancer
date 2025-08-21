"""
Kompleksowe testy dla BaseCommand - zwiększenie pokrycia do 85%+
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from mancer.application.commands.base_command import BaseCommand
from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult


class TestBaseCommandComprehensive:
    """Kompleksowe testy BaseCommand"""

    def setup_method(self):
        """Setup przed każdym testem"""
        self.command = BaseCommand("test_cmd")
        self.context = CommandContext()

        # Przykładowy CommandResult do testów
        self.sample_result = CommandResult(
            raw_output="test output",
            success=True,
            structured_output=["test", "output"],
            exit_code=0,
        )

    def test_base_command_initialization(self):
        """Test podstawowej inicjalizacji BaseCommand"""
        cmd = BaseCommand("ls")

        assert cmd._command_name == "ls"
        assert cmd._params == {}
        assert cmd._options == []

    def test_with_param_basic(self):
        """Test dodawania podstawowego parametru"""
        result = self.command.with_param("name", "value")

        # Sprawdź fluent interface (zwraca self)
        assert result is self.command
        assert self.command._params["name"] == "value"

    def test_with_param_chaining(self):
        """Test łańcuchowania parametrów"""
        result = (
            self.command.with_param("param1", "value1")
            .with_param("param2", "value2")
            .with_param("param3", 123)
        )

        assert result is self.command
        assert self.command._params["param1"] == "value1"
        assert self.command._params["param2"] == "value2"
        assert self.command._params["param3"] == 123

    def test_with_param_overwrite(self):
        """Test nadpisywania parametru"""
        self.command.with_param("name", "old_value")
        self.command.with_param("name", "new_value")

        assert self.command._params["name"] == "new_value"

    def test_with_option_basic(self):
        """Test dodawania podstawowej opcji"""
        result = self.command.with_option("verbose")

        assert result is self.command
        assert "verbose" in self.command._options

    def test_with_option_chaining(self):
        """Test łańcuchowania opcji"""
        result = self.command.with_option("v").with_option("verbose").with_option("force")

        assert result is self.command
        assert "v" in self.command._options
        assert "verbose" in self.command._options
        assert "force" in self.command._options

    def test_with_option_duplicates(self):
        """Test dodawania duplikatów opcji"""
        self.command.with_option("verbose")
        self.command.with_option("verbose")

        # Duplikaty powinny być dodane (BaseCommand nie filtruje)
        assert self.command._options.count("verbose") == 2

    def test_build_command_basic(self):
        """Test budowania podstawowej komendy"""
        cmd = BaseCommand("ls")
        result = cmd.build_command()

        assert result == "ls"

    def test_build_command_with_single_char_options(self):
        """Test budowania komendy z opcjami jednoznaczkowymi"""
        cmd = BaseCommand("ls").with_option("l").with_option("a")
        result = cmd.build_command()

        assert result == "ls -l -a"

    def test_build_command_with_long_options(self):
        """Test budowania komendy z długimi opcjami"""
        cmd = BaseCommand("ls").with_option("long").with_option("all")
        result = cmd.build_command()

        assert result == "ls --long --all"

    def test_build_command_with_mixed_options(self):
        """Test budowania komendy z mieszanymi opcjami"""
        cmd = BaseCommand("find").with_option("L").with_option("name")
        result = cmd.build_command()

        assert result == "find -L --name"

    def test_build_command_with_command_param(self):
        """Test budowania komendy z parametrem 'command'"""
        cmd = BaseCommand("apt").with_param("command", "install")
        result = cmd.build_command()

        assert result == "apt install"

    def test_build_command_with_boolean_params_true(self):
        """Test budowania komendy z parametrami boolean (True)"""
        cmd = BaseCommand("apt").with_param("yes", True).with_param("quiet", True)
        result = cmd.build_command()

        assert "--yes" in result
        assert "--quiet" in result

    def test_build_command_with_boolean_params_false(self):
        """Test budowania komendy z parametrami boolean (False)"""
        cmd = BaseCommand("apt").with_param("yes", False).with_param("quiet", False)
        result = cmd.build_command()

        # False boolean params nie powinny być dodane
        assert "--yes" not in result
        assert "--quiet" not in result
        assert result == "apt"

    def test_build_command_with_package_param(self):
        """Test budowania komendy z parametrem 'package'"""
        cmd = BaseCommand("apt").with_param("command", "install").with_param("package", "nginx")
        result = cmd.build_command()

        assert result == "apt install nginx"

    def test_build_command_with_query_param(self):
        """Test budowania komendy z parametrem 'query'"""
        cmd = BaseCommand("grep").with_param("query", "pattern")
        result = cmd.build_command()

        assert result == "grep pattern"

    def test_build_command_with_regular_params(self):
        """Test budowania komendy z regularnymi parametrami"""
        cmd = BaseCommand("find").with_param("type", "f").with_param("name", "*.py")
        result = cmd.build_command()

        assert "--type f" in result
        assert "--name *.py" in result

    def test_build_command_complex(self):
        """Test budowania złożonej komendy"""
        cmd = (
            BaseCommand("find")
            .with_param("command", "search")
            .with_option("L")
            .with_option("follow-symlinks")
            .with_param("type", "f")
            .with_param("name", "*.py")
            .with_param("recursive", True)
            .with_param("quiet", False)
        )

        result = cmd.build_command()

        assert result.startswith("find search")
        assert "-L" in result
        assert "--follow-symlinks" in result
        assert "--type f" in result
        assert "--name *.py" in result
        assert "--recursive" in result
        assert "--quiet" not in result

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend")
    def test_execute_local_command(self, mock_bash_backend):
        """Test wykonania komendy lokalnie"""
        # Mock backend
        mock_backend_instance = Mock()
        mock_backend_instance.execute_command.return_value = self.sample_result
        mock_bash_backend.return_value = mock_backend_instance

        # Mock context methods
        self.context.is_remote = Mock(return_value=False)
        self.context.add_to_history = Mock()

        result = self.command.execute(self.context)

        assert result == self.sample_result
        self.context.add_to_history.assert_called_once_with("test_cmd")
        mock_backend_instance.execute_command.assert_called_once()

    @patch("mancer.infrastructure.backend.ssh_backend.SshBackend")
    def test_execute_remote_command(self, mock_ssh_backend):
        """Test wykonania komendy zdalnie"""
        # Mock backend
        mock_backend_instance = Mock()
        mock_backend_instance.execute_command.return_value = self.sample_result
        mock_ssh_backend.return_value = mock_backend_instance

        # Mock context dla remote
        self.context.is_remote = Mock(return_value=True)
        self.context.add_to_history = Mock()

        # Mock remote host
        mock_remote_host = Mock()
        mock_remote_host.host = "example.com"
        mock_remote_host.user = "testuser"
        mock_remote_host.port = 22
        mock_remote_host.key_file = None
        mock_remote_host.password = "password"
        mock_remote_host.use_sudo = False
        mock_remote_host.sudo_password = None
        self.context.remote_host = mock_remote_host

        result = self.command.execute(self.context)

        assert result == self.sample_result
        self.context.add_to_history.assert_called_once_with("test_cmd")

        # Sprawdź czy SSH backend został utworzony z odpowiednimi parametrami
        mock_ssh_backend.assert_called_once_with(
            host="example.com",
            user="testuser",
            port=22,
            key_file=None,
            password="password",
            use_sudo=False,
            sudo_password=None,
        )

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend")
    def test_execute_with_input_result(self, mock_bash_backend):
        """Test wykonania komendy z wynikiem wejściowym"""
        # Mock backend
        mock_backend_instance = Mock()
        mock_backend_instance.execute_command.return_value = self.sample_result
        mock_bash_backend.return_value = mock_backend_instance

        # Mock context
        self.context.is_remote = Mock(return_value=False)
        self.context.add_to_history = Mock()

        # Input result
        input_result = CommandResult(
            raw_output="input data",
            success=True,
            structured_output=["input"],
            exit_code=0,
        )

        result = self.command.execute(self.context, input_result)

        # Sprawdź czy stdin został przekazany
        call_args = mock_backend_instance.execute_command.call_args
        assert call_args[0][4] == "input data"  # stdin parameter

    def test_clone_basic(self):
        """Test podstawowego klonowania komendy"""
        original = BaseCommand("ls")
        cloned = original.clone()

        assert cloned is not original
        assert cloned._command_name == original._command_name
        assert cloned._params == original._params
        assert cloned._options == original._options

    def test_clone_with_params_and_options(self):
        """Test klonowania komendy z parametrami i opcjami"""
        original = (
            BaseCommand("find")
            .with_param("type", "f")
            .with_param("name", "*.py")
            .with_option("L")
            .with_option("follow-symlinks")
        )

        cloned = original.clone()

        assert cloned is not original
        assert cloned._command_name == "find"
        assert cloned._params == {"type": "f", "name": "*.py"}
        assert cloned._options == ["L", "follow-symlinks"]

        # Sprawdź czy są to niezależne kopie
        cloned.with_param("new_param", "value")
        assert "new_param" not in original._params

    def test_clone_independence(self):
        """Test niezależności sklonowanej komendy"""
        original = BaseCommand("test").with_param("original", "value")
        cloned = original.clone()

        # Modyfikuj sklonowaną komendę
        cloned.with_param("cloned", "new_value")
        cloned.with_option("cloned_option")

        # Oryginał nie powinien być zmieniony
        assert "cloned" not in original._params
        assert "cloned_option" not in original._options

        # Sklonowana powinna mieć oba zestawy
        assert cloned._params["original"] == "value"
        assert cloned._params["cloned"] == "new_value"
        assert "cloned_option" in cloned._options

    def test_str_method(self):
        """Test metody __str__"""
        cmd = BaseCommand("ls").with_option("l").with_param("type", "f")
        str_result = str(cmd)

        assert str_result == cmd.build_command()
        assert "ls" in str_result
        assert "-l" in str_result
        assert "--type f" in str_result
