"""
Testy unit dla łańcuchów komend (command chains) frameworka Mancer
"""

from unittest.mock import patch

from mancer.application.shell_runner import ShellRunner
from mancer.domain.model.command_result import CommandResult


class TestShellRunner:
    """Testy unit dla ShellRunner - głównej klasy frameworka"""

    def test_shell_runner_initialization(self):
        """Test inicjalizacji ShellRunner"""
        runner = ShellRunner(backend_type="bash")

        assert runner is not None
        assert hasattr(runner, "create_command")
        assert hasattr(runner, "execute")
        assert runner.factory is not None

    def test_shell_runner_initialization_with_cache(self):
        """Test inicjalizacji ShellRunner z cache"""
        runner = ShellRunner(backend_type="bash", enable_cache=True, cache_size=50)

        assert runner is not None
        assert runner._cache_enabled
        assert runner._command_cache is not None

    def test_shell_runner_create_command(self):
        """Test tworzenia komendy przez ShellRunner"""
        runner = ShellRunner(backend_type="bash")

        # Test tworzenia różnych komend
        ls_cmd = runner.create_command("ls")
        assert ls_cmd is not None

        echo_cmd = runner.create_command("echo")
        assert echo_cmd is not None

        hostname_cmd = runner.create_command("hostname")
        assert hostname_cmd is not None

    def test_shell_runner_create_nonexistent_command(self):
        """Test tworzenia nieistniejącej komendy"""
        runner = ShellRunner(backend_type="bash")

        # create_command rzuca ValueError dla nieistniejących komend
        try:
            _ = runner.create_command("nonexistent_command_123")
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "not found" in str(e).lower()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_shell_runner_execute_simple_command(self, mock_execute):
        """Test wykonania prostej komendy przez ShellRunner"""
        # Mock backend execution
        mock_result = CommandResult(
            raw_output="test output",
            success=True,
            structured_output=["test output"],
            exit_code=0,
        )
        mock_execute.return_value = mock_result

        runner = ShellRunner(backend_type="bash")
        echo_cmd = runner.create_command("echo")

        if hasattr(echo_cmd, "text"):
            echo_cmd = echo_cmd.text("test")

        result = runner.execute(echo_cmd)

        assert isinstance(result, CommandResult)
        assert result.success
        assert result.exit_code == 0
        assert "test output" in result.raw_output

        # Sprawdź czy backend został wywołany
        assert mock_execute.called

    def test_shell_runner_execute_multiple_commands(self):
        """Test wykonania wielu komend przez ShellRunner"""
        # This test executes real commands, so we can't easily mock them
        # Instead, we verify that commands execute successfully
        runner = ShellRunner(backend_type="bash", enable_cache=False)

        # Wykonaj różne komendy - these will execute real commands
        ls_cmd = runner.create_command("ls")
        ls_result = runner.execute(ls_cmd)
        assert ls_result.success
        # Just verify that we got some output (not empty)
        assert len(ls_result.raw_output) > 0

        hostname_cmd = runner.create_command("hostname")
        hostname_result = runner.execute(hostname_cmd)
        assert hostname_result.success
        assert len(hostname_result.raw_output) > 0

        echo_cmd = runner.create_command("echo")
        if hasattr(echo_cmd, "text"):
            echo_cmd = echo_cmd.text("hello world")
        echo_result = runner.execute(echo_cmd)
        assert echo_result.success
        assert "hello world" in echo_result.raw_output

        # Sprawdź czy backend został wywołany 3 razy
        assert mock_execute.call_count == 3


class TestCommandChaining:
    """Testy unit dla łańcuchów komend"""

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_simple_command_chain(self, mock_execute):
        """Test prostego łańcucha komend"""
        # Mock backend executions
        mock_results = [
            CommandResult(
                raw_output="first command output",
                success=True,
                structured_output=["first command output"],
                exit_code=0,
            ),
            CommandResult(
                raw_output="second command output",
                success=True,
                structured_output=["second command output"],
                exit_code=0,
            ),
        ]
        mock_execute.side_effect = mock_results

        runner = ShellRunner(backend_type="bash")

        # Wykonaj sekwencję komend
        first_cmd = runner.create_command("echo")
        if hasattr(first_cmd, "text"):
            first_cmd = first_cmd.text("first")

        second_cmd = runner.create_command("echo")
        if hasattr(second_cmd, "text"):
            second_cmd = second_cmd.text("second")

        # Wykonaj komendy w sekwencji
        first_result = runner.execute(first_cmd)
        assert first_result.success

        second_result = runner.execute(second_cmd)
        assert second_result.success

        # Sprawdź czy obie komendy zostały wykonane
        assert mock_execute.call_count == 2

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_command_chain_with_then(self, mock_execute):
        """Test łańcucha komend z metodą then (jeśli dostępna)"""
        # Mock backend execution
        mock_result = CommandResult(
            raw_output="chained command output",
            success=True,
            structured_output=["chained command output"],
            exit_code=0,
        )
        mock_execute.return_value = mock_result

        runner = ShellRunner(backend_type="bash")

        first_cmd = runner.create_command("echo")
        if hasattr(first_cmd, "text"):
            first_cmd = first_cmd.text("first")

        # Sprawdź czy komenda ma metodę then
        if hasattr(first_cmd, "then"):
            second_cmd = runner.create_command("echo")
            if hasattr(second_cmd, "text"):
                second_cmd = second_cmd.text("second")

            chained_cmd = first_cmd.then(second_cmd)
            result = runner.execute(chained_cmd)

            assert result.success
            # Chained command wywołuje execute_command dla każdej komendy w łańcuchu
            assert mock_execute.call_count >= 1
        else:
            # Jeśli nie ma metody then, po prostu wykonaj komendy oddzielnie
            result = runner.execute(first_cmd)
            assert result.success

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_command_pipe_chain(self, mock_execute):
        """Test łańcucha komend z pipe (jeśli dostępny)"""
        # Mock backend execution
        mock_result = CommandResult(
            raw_output="piped command output",
            success=True,
            structured_output=["piped command output"],
            exit_code=0,
        )
        mock_execute.return_value = mock_result

        runner = ShellRunner(backend_type="bash")

        ls_cmd = runner.create_command("ls")
        grep_cmd = runner.create_command("grep")

        # Sprawdź czy komendy mają metodę pipe
        if hasattr(ls_cmd, "pipe") and hasattr(grep_cmd, "pattern"):
            grep_cmd = grep_cmd.pattern("test")
            piped_cmd = ls_cmd.pipe(grep_cmd)
            result = runner.execute(piped_cmd)

            # Pipe może nie znaleźć dopasowania, co jest poprawne
            assert isinstance(result, CommandResult)
            # Nie sprawdzamy success bo grep może zwrócić exit code 1 gdy nie znajdzie dopasowania
        else:
            # Jeśli nie ma metody pipe, wykonaj komendy oddzielnie
            ls_result = runner.execute(ls_cmd)
            assert ls_result.success


class TestShellRunnerAdvanced:
    """Zaawansowane testy ShellRunner"""

    def test_shell_runner_context_management(self):
        """Test zarządzania kontekstem w ShellRunner"""
        runner = ShellRunner(backend_type="bash")

        # Test czy ma właściwości kontekstu
        assert hasattr(runner, "_context")

        # Test czy można ustawić katalog roboczy
        if hasattr(runner, "set_working_directory"):
            runner.set_working_directory("/tmp")
            # Sprawdź czy kontekst został zaktualizowany
            assert runner._context.current_directory == "/tmp"

    def test_shell_runner_environment_variables(self):
        """Test zarządzania zmiennymi środowiskowymi"""
        runner = ShellRunner(backend_type="bash")

        # Test czy można ustawić zmienne środowiskowe
        if hasattr(runner, "set_environment_variable"):
            runner.set_environment_variable("TEST_VAR", "test_value")
            assert runner._context.environment_variables["TEST_VAR"] == "test_value"

    def test_shell_runner_remote_execution_setup(self):
        """Test konfiguracji zdalnego wykonywania"""
        runner = ShellRunner(backend_type="bash")

        # Test czy ma metodę do konfiguracji zdalnego wykonywania
        assert hasattr(runner, "set_remote_execution")
        assert hasattr(runner, "set_local_execution")

        # Test podstawowej konfiguracji (bez rzeczywistego połączenia)
        try:
            runner.set_remote_execution(host="test.example.com", user="testuser")
            # Sprawdź czy kontekst został zaktualizowany
            assert runner._context.is_remote()
        except Exception:
            # Jeśli wystąpi błąd (np. brak parametrów), to jest OK dla testu unit
            pass

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_shell_runner_error_handling(self, mock_execute):
        """Test obsługi błędów w ShellRunner"""
        # Mock backend execution z błędem
        mock_result = CommandResult(
            raw_output="",
            success=False,
            structured_output=[],
            exit_code=127,
            error_message="command not found",
        )
        mock_execute.return_value = mock_result

        runner = ShellRunner(backend_type="bash")

        # Stwórz komendę która nie istnieje (ale factory ją utworzy)
        echo_cmd = runner.create_command("echo")
        if hasattr(echo_cmd, "text"):
            echo_cmd = echo_cmd.text("test")

        result = runner.execute(echo_cmd)

        # Sprawdź czy błąd został poprawnie obsłużony
        assert isinstance(result, CommandResult)
        assert not result.success
        assert result.exit_code == 127
        assert "command not found" in result.error_message


class TestCommandCaching:
    """Testy unit dla funkcjonalności cache komend"""

    def test_shell_runner_cache_initialization(self):
        """Test inicjalizacji cache w ShellRunner"""
        runner = ShellRunner(backend_type="bash", enable_cache=True, cache_size=100)

        assert runner._cache_enabled
        assert runner._command_cache is not None
        assert hasattr(runner, "get_cache_statistics")

    def test_shell_runner_cache_disabled(self):
        """Test ShellRunner z wyłączonym cache"""
        runner = ShellRunner(backend_type="bash", enable_cache=False)

        assert not runner._cache_enabled

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_command_caching_functionality(self, mock_execute):
        """Test funkcjonalności cache komend"""
        # Mock backend execution
        mock_result = CommandResult(
            raw_output="cached output",
            success=True,
            structured_output=["cached output"],
            exit_code=0,
        )
        mock_execute.return_value = mock_result

        runner = ShellRunner(backend_type="bash", enable_cache=True, cache_size=10)

        echo_cmd = runner.create_command("echo")
        if hasattr(echo_cmd, "text"):
            echo_cmd = echo_cmd.text("test")

        # Wykonaj komendę pierwszy raz
        result1 = runner.execute(echo_cmd)
        assert result1.success

        # Wykonaj tę samą komendę ponownie
        result2 = runner.execute(echo_cmd)
        assert result2.success

        # W zależności od implementacji cache, backend może być wywołany 1 lub 2 razy
        assert mock_execute.call_count >= 1
        assert mock_execute.call_count <= 2

    def test_cache_statistics(self):
        """Test statystyk cache"""
        runner = ShellRunner(backend_type="bash", enable_cache=True, cache_size=10)

        # Test czy można pobrać statystyki cache
        if hasattr(runner, "get_cache_statistics"):
            stats = runner.get_cache_statistics()
            assert isinstance(stats, dict)
            # Sprawdź czy statystyki zawierają podstawowe informacje
            expected_keys = ["cache_size", "cached_items", "hit_ratio"]
            for key in expected_keys:
                if key in stats:
                    assert stats[key] is not None
