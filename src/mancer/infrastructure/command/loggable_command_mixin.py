from typing import Any, Dict, Optional

from ...domain.model.command_context import CommandContext
from ...domain.model.command_result import CommandResult
from ..logging.mancer_logger import MancerLogger


class LoggableCommandMixin:
    """
    Mixin dodający funkcjonalność logowania do komend.

    Automatycznie loguje rozpoczęcie i zakończenie wykonania komendy,
    a także zapisuje wyniki w historii komend.
    """

    def _get_logger(self) -> MancerLogger:
        """Pobiera instancję MancerLogger."""
        return MancerLogger.get_instance()

    def _log_command_start(
        self, command_string: str, context: CommandContext
    ) -> Dict[str, Any]:
        """
        Loguje rozpoczęcie wykonania komendy.

        Args:
            command_string: Pełna komenda do wykonania
            context: Kontekst wykonania komendy

        Returns:
            Informacje o rozpoczętej komendzie do użycia w _log_command_end
        """
        # Pobierz nazwę komendy (nazwę klasy lub atrybut name)
        command_name = self.__class__.__name__
        if hasattr(self, "name"):
            command_name = getattr(self, "name")

        # Przygotuj parametry kontekstu do logowania
        context_params = {
            "current_directory": context.current_directory,
            "execution_mode": str(context.execution_mode),
        }

        # Dodaj informacje o hoście zdalnym, jeśli istnieją
        if context.remote_host:
            context_params["remote_host"] = str(context.remote_host)

        # Zaloguj dodatkowe parametry z kontekstu
        for key, value in context.parameters.items():
            # Pomijamy duże obiekty i poufne dane
            if isinstance(value, (str, int, float, bool)) and key.lower() not in (
                "password",
                "secret",
                "token",
                "key",
            ):
                context_params[key] = value

        # Loguj rozpoczęcie komendy
        return self._get_logger().log_command_start(
            command_name=command_name,
            command_string=command_string,
            context_params=context_params,
        )

    def _log_command_end(
        self, command_info: Dict[str, Any], result: CommandResult
    ) -> None:
        """
        Loguje zakończenie wykonania komendy.

        Args:
            command_info: Informacje zwrócone przez _log_command_start
            result: Wynik wykonania komendy
        """
        self._get_logger().log_command_end(
            command_info=command_info,
            success=result.success,
            exit_code=result.exit_code,
            output=result.raw_output,
            error=result.error_message,
        )

        # Loguj dane wejściowe i wyjściowe dla pipeline'ów
        if hasattr(result, "command_name") and result.structured_output:
            self._get_logger().log_command_output(
                command_name=result.command_name, data=result.structured_output
            )

    def execute_with_logging(
        self,
        original_execute,
        context: CommandContext,
        input_result: Optional[CommandResult] = None,
    ) -> CommandResult:
        """
        Wykonuje komendę z logowaniem początku i końca.

        Args:
            original_execute: Oryginalna metoda execute komendy
            context: Kontekst wykonania komendy
            input_result: Opcjonalny wynik poprzedniej komendy

        Returns:
            Wynik wykonania komendy
        """
        # Budujemy komendę, aby zalogować
        command_string = (
            self.build_command() if hasattr(self, "build_command") else str(self)
        )

        # Logujemy rozpoczęcie
        command_info = self._log_command_start(command_string, context)

        # Jeśli mamy dane wejściowe, zaloguj je
        if input_result:
            command_name = self.__class__.__name__
            if hasattr(self, "name"):
                command_name = getattr(self, "name")

            self._get_logger().log_command_input(
                command_name=command_name, data=input_result.structured_output
            )

            # Dodaj nazwę komendy dla logowania danych wyjściowych
            if not hasattr(input_result, "command_name"):
                setattr(input_result, "command_name", command_name)

        try:
            # Wykonujemy oryginalną metodę
            result = original_execute(context, input_result)

            # Dodaj nazwę komendy dla logowania danych wyjściowych
            if not hasattr(result, "command_name"):
                command_name = self.__class__.__name__
                if hasattr(self, "name"):
                    command_name = getattr(self, "name")
                setattr(result, "command_name", command_name)

            # Logujemy zakończenie
            self._log_command_end(command_info, result)

            return result
        except Exception as e:
            # W przypadku wyjątku logujemy błąd
            error_result = CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=-1,
                error_message=str(e),
            )

            # Dodaj nazwę komendy dla logowania
            command_name = self.__class__.__name__
            if hasattr(self, "name"):
                command_name = getattr(self, "name")
            setattr(error_result, "command_name", command_name)

            self._log_command_end(command_info, error_result)

            # Przekazujemy wyjątek dalej
            raise
