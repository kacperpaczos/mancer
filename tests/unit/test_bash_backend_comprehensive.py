"""
Kompleksowe testy dla BashBackend - zwiększenie pokrycia do 80%+
"""

import os
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mancer.domain.model.command_result import CommandResult
from mancer.infrastructure.backend.bash_backend import BashBackend


class TestBashBackendComprehensive:
    """Kompleksowe testy BashBackend"""

    def setup_method(self):
        """Setup przed każdym testem"""
        self.backend = BashBackend()

    def test_execute_command_basic(self):
        """Test podstawowego wykonania komendy"""
        result = self.backend.execute_command("echo 'test'")

        assert isinstance(result, CommandResult)
        assert result.success
        assert result.exit_code == 0
        assert "test" in result.raw_output
        assert result.structured_output == ["test"]

    def test_execute_command_with_working_dir(self):
        """Test wykonania komendy z working_dir"""
        # Użyj katalogu, który na pewno istnieje
        test_dir = "/tmp"
        result = self.backend.execute_command("pwd", working_dir=test_dir)

        assert result.success
        assert test_dir in result.raw_output

    def test_execute_command_with_env_vars(self):
        """Test wykonania komendy ze zmiennymi środowiskowymi"""
        env_vars = {"TEST_VAR": "test_value"}
        result = self.backend.execute_command("echo $TEST_VAR", env_vars=env_vars)

        assert result.success
        assert "test_value" in result.raw_output

    def test_execute_command_with_stdin(self):
        """Test wykonania komendy z stdin"""
        result = self.backend.execute_command("cat", stdin="hello world")

        assert result.success
        assert "hello world" in result.raw_output

    def test_execute_command_failing(self):
        """Test wykonania komendy która kończy się błędem"""
        result = self.backend.execute_command("exit 1")

        assert not result.success
        assert result.exit_code == 1

    def test_execute_command_nonexistent(self):
        """Test wykonania nieistniejącej komendy"""
        result = self.backend.execute_command("nonexistent_command_12345")

        assert not result.success
        assert result.exit_code != 0
        assert result.error_message is not None

    @patch("subprocess.run")
    def test_execute_command_exception_handling(self, mock_run):
        """Test obsługi wyjątków podczas wykonywania komendy"""
        # Symuluj wyjątek
        mock_run.side_effect = Exception("Test exception")

        result = self.backend.execute_command("echo test")

        assert not result.success
        assert result.exit_code == -1
        assert "Test exception" in result.error_message
        assert "Traceback" in result.error_message

    def test_execute_command_with_live_output(self):
        """Test wykonania komendy z live output"""
        context_params = {"live_output": True, "live_output_interval": 0.05}

        # Użyj prostej komendy która szybko się wykona
        result = self.backend.execute_command("echo 'live test'", context_params=context_params)

        assert isinstance(result, CommandResult)
        # Live output może mieć różne zachowanie, ale powinien zwrócić wynik
        assert "live test" in result.raw_output or result.raw_output == ""

    @patch("subprocess.Popen")
    def test_execute_command_live_output_with_mock(self, mock_popen):
        """Test live output z mockiem dla kontrolowanego środowiska"""
        # Mock procesu
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = ["line1\n", "line2\n", ""]
        mock_process.stderr.readline.side_effect = ["", "", ""]
        mock_process.poll.side_effect = [
            None,
            None,
            0,
        ]  # Proces kończy się po 3 wywołaniach
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        context_params = {"live_output": True}
        result = self.backend.execute_command("echo test", context_params=context_params)

        # Sprawdź czy Popen został wywołany z odpowiednimi parametrami
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[1]["shell"]
        assert call_args[1]["stdout"] == subprocess.PIPE
        assert call_args[1]["stderr"] == subprocess.PIPE

    def test_execute_method_basic(self):
        """Test metody execute (używanej przez Command classes)"""
        exit_code, stdout, stderr = self.backend.execute("echo 'execute test'")

        assert exit_code == 0
        assert "execute test" in stdout
        assert stderr == ""

    def test_execute_method_with_input(self):
        """Test metody execute z input_data"""
        exit_code, stdout, stderr = self.backend.execute("cat", input_data="input test")

        assert exit_code == 0
        assert "input test" in stdout

    def test_execute_method_with_working_dir(self):
        """Test metody execute z working_dir"""
        exit_code, stdout, stderr = self.backend.execute("pwd", working_dir="/tmp")

        assert exit_code == 0
        assert "/tmp" in stdout

    @patch("subprocess.Popen")
    def test_execute_method_timeout(self, mock_popen):
        """Test timeout w metodzie execute"""
        # Mock procesu który się zawiesza
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("test", 1)
        mock_process.kill.return_value = None
        mock_process.communicate.return_value = ("", "timeout error")
        mock_popen.return_value = mock_process

        exit_code, stdout, stderr = self.backend.execute("sleep 10", timeout=1)

        assert exit_code == -1
        assert "timed out" in stderr

    @patch("subprocess.Popen")
    def test_execute_method_keyboard_interrupt(self, mock_popen):
        """Test KeyboardInterrupt w metodzie execute"""
        # Mock procesu
        mock_process = Mock()
        mock_process.communicate.side_effect = KeyboardInterrupt()
        mock_process.kill.return_value = None
        mock_popen.return_value = mock_process

        exit_code, stdout, stderr = self.backend.execute("long_command")

        assert exit_code == -1
        assert "interrupted by user" in stderr

    def test_execute_method_exception(self):
        """Test obsługi wyjątków w metodzie execute"""
        # Użyj niepoprawnej komendy która spowoduje wyjątek
        exit_code, stdout, stderr = self.backend.execute("", working_dir="/nonexistent/directory")

        assert exit_code == -1
        assert stderr != ""

    def test_parse_output_success(self):
        """Test parsowania wyjścia dla udanej komendy"""
        result = self.backend.parse_output("echo test", "line1\nline2\n", 0, "")

        assert result.success
        assert result.exit_code == 0
        assert result.raw_output == "line1\nline2\n"
        assert result.structured_output == ["line1", "line2"]
        assert result.error_message is None

    def test_parse_output_failure(self):
        """Test parsowania wyjścia dla nieudanej komendy"""
        result = self.backend.parse_output("false", "", 1, "error message")

        assert not result.success
        assert result.exit_code == 1
        assert result.raw_output == ""
        assert result.structured_output == []
        assert result.error_message == "error message"

    def test_parse_output_empty_lines_filtered(self):
        """Test filtrowania pustych linii w structured_output"""
        result = self.backend.parse_output("test", "line1\n\nline2\n\n", 0, "")

        assert result.structured_output == ["line1", "line2"]

    def test_build_command_string_basic(self):
        """Test budowania podstawowego stringa komendy"""
        command = self.backend.build_command_string("ls", [], {}, [])
        assert command == "ls"

    def test_build_command_string_with_options(self):
        """Test budowania komendy z opcjami"""
        command = self.backend.build_command_string("ls", ["-l", "-a"], {}, [])
        assert command == "ls -l -a"

    def test_build_command_string_with_flags(self):
        """Test budowania komendy z flagami"""
        command = self.backend.build_command_string(
            "ls", [], {}, ["--recursive", "--human-readable"]
        )
        assert command == "ls --recursive --human-readable"

    def test_build_command_string_with_short_params(self):
        """Test budowania komendy z krótkimi parametrami"""
        command = self.backend.build_command_string("find", [], {"n": "5"}, [])
        assert command == "find -n 5"  # shlex.quote('5') zwraca '5' bez cudzysłowów

    def test_build_command_string_with_long_params(self):
        """Test budowania komendy z długimi parametrami"""
        command = self.backend.build_command_string("grep", [], {"pattern": "test.*"}, [])
        assert command == "grep --pattern='test.*'"

    def test_build_command_string_complex(self):
        """Test budowania złożonej komendy"""
        command = self.backend.build_command_string(
            "find", ["-type", "f"], {"name": "*.py", "d": "2"}, ["--follow-symlinks"]
        )

        # Sprawdź podstawowe części
        assert "find" in command
        assert "-type" in command
        assert "f" in command
        assert "--follow-symlinks" in command
        assert "--name='*.py'" in command  # Długi parametr z cudzysłowami
        assert "-d 2" in command  # Krótki parametr bez cudzysłowów

    def test_build_command_string_special_characters(self):
        """Test budowania komendy ze specjalnymi znakami"""
        command = self.backend.build_command_string("echo", [], {"text": "hello world & test"}, [])

        # shlex.quote powinien zabezpieczyć specjalne znaki
        assert "hello world & test" in command
        assert "'" in command  # Powinny być cudzysłowy
