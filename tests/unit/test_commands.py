"""
Testy unit dla core komend frameworka Mancer
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.backend.bash_backend import BashBackend
from mancer.infrastructure.factory.command_factory import CommandFactory


class TestCommandFactory:
    """Testy unit dla CommandFactory"""

    def test_command_factory_initialization(self):
        """Test inicjalizacji CommandFactory"""
        factory = CommandFactory("bash")
        assert factory.backend_type == "bash"
        assert factory._command_types is not None
        assert len(factory._command_types) > 0

    def test_create_ls_command(self):
        """Test tworzenia komendy ls"""
        factory = CommandFactory("bash")
        ls_cmd = factory.create_command("ls")

        assert ls_cmd is not None
        assert hasattr(ls_cmd, "build_command")
        assert hasattr(ls_cmd, "execute")

    def test_create_echo_command(self):
        """Test tworzenia komendy echo"""
        factory = CommandFactory("bash")
        echo_cmd = factory.create_command("echo")

        assert echo_cmd is not None
        assert hasattr(echo_cmd, "text")
        assert hasattr(echo_cmd, "build_command")

    def test_create_hostname_command(self):
        """Test tworzenia komendy hostname"""
        factory = CommandFactory("bash")
        hostname_cmd = factory.create_command("hostname")

        assert hostname_cmd is not None
        assert hasattr(hostname_cmd, "build_command")
        assert hasattr(hostname_cmd, "execute")

    def test_create_df_command(self):
        """Test tworzenia komendy df"""
        factory = CommandFactory("bash")
        df_cmd = factory.create_command("df")

        assert df_cmd is not None
        assert hasattr(df_cmd, "human_readable")
        assert hasattr(df_cmd, "build_command")

    def test_create_ps_command(self):
        """Test tworzenia komendy ps"""
        factory = CommandFactory("bash")
        ps_cmd = factory.create_command("ps")

        assert ps_cmd is not None
        assert hasattr(ps_cmd, "build_command")
        assert hasattr(ps_cmd, "execute")

    def test_create_nonexistent_command(self):
        """Test tworzenia nieistniejącej komendy"""
        factory = CommandFactory("bash")
        nonexistent_cmd = factory.create_command("nonexistent_command_123")

        assert nonexistent_cmd is None

    def test_command_types_registration(self):
        """Test czy wszystkie podstawowe typy komend są zarejestrowane"""
        factory = CommandFactory("bash")

        expected_commands = ["ls", "echo", "hostname", "df", "ps", "cat", "grep"]

        for cmd_type in expected_commands:
            cmd = factory.create_command(cmd_type)
            assert cmd is not None, f"Komenda {cmd_type} nie została zarejestrowana"


class TestBashBackend:
    """Testy unit dla BashBackend"""

    def test_bash_backend_initialization(self):
        """Test inicjalizacji BashBackend"""
        backend = BashBackend()
        assert backend is not None
        assert hasattr(backend, "execute_command")

    @patch("subprocess.run")
    def test_execute_simple_command(self, mock_run):
        """Test wykonania prostej komendy"""
        # Mock subprocess.run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        backend = BashBackend()
        result = backend.execute_command("echo test")

        assert isinstance(result, CommandResult)
        assert result.success
        assert result.exit_code == 0
        assert "test output" in result.raw_output

    @patch("subprocess.run")
    def test_execute_failing_command(self, mock_run):
        """Test wykonania komendy która kończy się błędem"""
        # Mock subprocess.run for failing command
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "command not found"
        mock_run.return_value = mock_result

        backend = BashBackend()
        result = backend.execute_command("nonexistent_command")

        assert isinstance(result, CommandResult)
        assert not result.success
        assert result.exit_code == 1
        assert "command not found" in result.error_message

    @patch("subprocess.run")
    def test_execute_command_with_working_dir(self, mock_run):
        """Test wykonania komendy z określonym katalogiem roboczym"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/tmp"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        backend = BashBackend()
        result = backend.execute_command("pwd", working_dir="/tmp")

        assert result.success
        # Sprawdź czy subprocess.run został wywołany z odpowiednim cwd
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1].get("cwd") == "/tmp"

    @patch("subprocess.run")
    def test_execute_command_with_env_vars(self, mock_run):
        """Test wykonania komendy ze zmiennymi środowiskowymi"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test_value"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        backend = BashBackend()
        env_vars = {"TEST_VAR": "test_value"}
        result = backend.execute_command("echo $TEST_VAR", env_vars=env_vars)

        assert result.success
        # Sprawdź czy subprocess.run został wywołany z odpowiednim env
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        env = call_args[1].get("env")
        assert env is not None
        assert "TEST_VAR" in env
        assert env["TEST_VAR"] == "test_value"


class TestCoreCommands:
    """Testy unit dla core komend frameworka"""

    def test_ls_command_building(self):
        """Test budowania komendy ls"""
        factory = CommandFactory("bash")
        ls_cmd = factory.create_command("ls")

        # Test podstawowej komendy ls
        basic_command = ls_cmd.build_command()
        assert basic_command == "ls"

        # Test ls z flagami
        if hasattr(ls_cmd, "long"):
            ls_long = ls_cmd.long()
            assert ls_long.build_command() == "ls -l"

        if hasattr(ls_cmd, "all"):
            ls_all = ls_cmd.all()
            assert ls_all.build_command() in ["ls -a", "ls -la", "ls -al"]

    def test_echo_command_building(self):
        """Test budowania komendy echo"""
        factory = CommandFactory("bash")
        echo_cmd = factory.create_command("echo")

        # Test echo z tekstem
        if hasattr(echo_cmd, "text"):
            echo_with_text = echo_cmd.text("hello world")
            command = echo_with_text.build_command()
            assert "echo" in command
            assert "hello world" in command

    def test_hostname_command_building(self):
        """Test budowania komendy hostname"""
        factory = CommandFactory("bash")
        hostname_cmd = factory.create_command("hostname")

        basic_command = hostname_cmd.build_command()
        assert basic_command == "hostname"

        # Test hostname z flagami jeśli dostępne
        if hasattr(hostname_cmd, "fqdn"):
            hostname_fqdn = hostname_cmd.fqdn()
            fqdn_command = hostname_fqdn.build_command()
            assert "hostname" in fqdn_command
            assert "-f" in fqdn_command or "--fqdn" in fqdn_command

    def test_df_command_building(self):
        """Test budowania komendy df"""
        factory = CommandFactory("bash")
        df_cmd = factory.create_command("df")

        basic_command = df_cmd.build_command()
        assert basic_command == "df -h"  # df command domyślnie używa -h flag

        # Test df z human readable jeśli dostępne
        if hasattr(df_cmd, "human_readable"):
            df_human = df_cmd.human_readable()
            human_command = df_human.build_command()
            assert "df" in human_command
            assert "-h" in human_command

    def test_ps_command_building(self):
        """Test budowania komendy ps"""
        factory = CommandFactory("bash")
        ps_cmd = factory.create_command("ps")

        basic_command = ps_cmd.build_command()
        assert basic_command == "ps"

        # Test ps z flagami jeśli dostępne
        if hasattr(ps_cmd, "aux"):
            ps_aux = ps_cmd.aux()
            aux_command = ps_aux.build_command()
            assert "ps" in aux_command
            assert "aux" in aux_command


class TestCommandExecution:
    """Testy unit dla wykonywania komend"""

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_command_execution_flow(self, mock_execute):
        """Test przepływu wykonywania komendy"""
        # Mock backend execution
        mock_result = CommandResult(
            raw_output="test output",
            success=True,
            structured_output=["test output"],
            exit_code=0,
        )
        mock_execute.return_value = mock_result

        factory = CommandFactory("bash")
        echo_cmd = factory.create_command("echo")

        if hasattr(echo_cmd, "text"):
            echo_cmd = echo_cmd.text("test")

        # Stwórz mock context
        context = CommandContext()

        # Wykonaj komendę
        result = echo_cmd.execute(context)

        assert isinstance(result, CommandResult)
        assert result.success
        assert result.exit_code == 0
        assert "test output" in result.raw_output

        # Sprawdź czy backend został wywołany
        mock_execute.assert_called_once()


class TestCommandContext:
    """Testy unit dla CommandContext"""

    def test_command_context_initialization(self):
        """Test inicjalizacji CommandContext"""
        context = CommandContext()

        assert context is not None
        assert hasattr(context, "current_directory")
        assert hasattr(context, "environment_variables")

    def test_command_context_with_directory(self):
        """Test CommandContext z określonym katalogiem"""
        context = CommandContext(current_directory="/tmp")

        assert context.current_directory == "/tmp"

    def test_command_context_with_env_vars(self):
        """Test CommandContext ze zmiennymi środowiskowymi"""
        env_vars = {"TEST_VAR": "test_value"}
        context = CommandContext(environment_variables=env_vars)

        assert context.environment_variables == env_vars
        assert context.environment_variables["TEST_VAR"] == "test_value"
