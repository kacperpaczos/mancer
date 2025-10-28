import re
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

from ...domain.interface.command_interface import CommandInterface
from ...domain.model.command_context import CommandContext
from ...domain.model.command_result import CommandResult

T = TypeVar("T", bound="CommandEnforcer")


class CommandEnforcer:
    """
    Klasa wzbogacająca mechanizm komend o zaawansowane funkcje wykonywania,
    walidację, retry logic i obsługę błędów.
    """

    def __init__(self, command: CommandInterface):
        """
        Inicjalizuje CommandEnforcer z istniejącą komendą.

        Args:
            command: Komenda do wzbogacenia
        """
        self.command = command
        self.max_retries = 0
        self.retry_delay = 1  # sekundy
        self.validators: List[Callable[[CommandResult], bool]] = []
        self.timeout: Optional[int] = None
        self.error_handlers: Dict[str, Callable[[CommandContext, Exception], None]] = {}
        self.success_handlers: List[Callable[[CommandResult], CommandResult]] = []

    def with_retry(self, max_retries: int, delay: int = 1) -> "CommandEnforcer":
        """
        Konfiguruje mechanizm ponawiania komendy.

        Args:
            max_retries: Maksymalna liczba ponowień
            delay: Opóźnienie między ponowieniami w sekundach

        Returns:
            CommandEnforcer: Zaktualizowana instancja
        """
        new_instance: CommandEnforcer = self._clone()
        new_instance.max_retries = max_retries
        new_instance.retry_delay = delay
        return new_instance

    def with_validator(self, validator_func: Callable[[CommandResult], bool]) -> "CommandEnforcer":
        """
        Dodaje funkcję walidacyjną, która sprawdza poprawność wyniku komendy.

        Args:
            validator_func: Funkcja walidująca przyjmująca CommandResult i zwracająca bool

        Returns:
            CommandEnforcer: Zaktualizowana instancja
        """
        new_instance: CommandEnforcer = self._clone()
        new_instance.validators.append(validator_func)
        return new_instance

    def with_timeout(self, timeout: int) -> "CommandEnforcer":
        """
        Ustawia timeout dla wykonania komendy.

        Args:
            timeout: Timeout w sekundach

        Returns:
            CommandEnforcer: Zaktualizowana instancja
        """
        new_instance: CommandEnforcer = self._clone()
        new_instance.timeout = timeout
        return new_instance

    def on_error(
        self,
        error_pattern: str,
        handler_func: Callable[[CommandResult, Exception], CommandResult],
    ) -> "CommandEnforcer":
        """
        Dodaje handler błędów, który zostanie wywołany, gdy błąd pasuje do wzorca.

        Args:
            error_pattern: Wzorzec błędu (regex)
            handler_func: Funkcja obsługująca błąd, przyjmująca CommandResult i Exception

        Returns:
            CommandEnforcer: Zaktualizowana instancja
        """
        new_instance: CommandEnforcer = self._clone()
        new_instance.error_handlers[error_pattern] = handler_func
        return new_instance

    def on_success(
        self, handler_func: Callable[[CommandResult], CommandResult]
    ) -> "CommandEnforcer":
        """
        Dodaje handler sukcesu, który zostanie wywołany po pomyślnym wykonaniu komendy.

        Args:
            handler_func: Funkcja obsługująca sukces, przyjmująca CommandResult

        Returns:
            CommandEnforcer: Zaktualizowana instancja
        """
        new_instance: CommandEnforcer = self._clone()
        new_instance.success_handlers.append(handler_func)  # type: ignore
        return new_instance

    def execute(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
        """
        Wykonuje komendę z obsługą retry, walidacją, timeoutem i obsługą błędów.

        Args:
            context: Kontekst wykonania komendy
            input_result: Opcjonalny wynik poprzedniej komendy

        Returns:
            CommandResult: Wynik wykonania komendy
        """
        retries = 0
        last_exception = None

        while retries <= self.max_retries:
            try:
                # Wykonanie komendy
                result = self.command(context, input_result)

                # Sprawdzenie wyników walidatorów
                valid = True
                for validator in self.validators:
                    if not validator(result):
                        valid = False
                        break

                # Jeśli komenda powiodła się i przeszła walidację
                if result.success and valid:
                    # Wywołanie handlerów sukcesu
                    for handler in self.success_handlers:
                        result = handler(result)
                    return result

                # Jeśli nie powiodło się, ale nie ma więcej prób
                if retries == self.max_retries:
                    return result

                # Przygotuj do ponowienia
                retries += 1
                time.sleep(self.retry_delay)

            except Exception as e:
                last_exception = e

                # Sprawdź, czy któryś handler pasuje do błędu
                handled = False
                for pattern, handler in self.error_handlers.items():
                    if re.search(pattern, str(e)):
                        error_result = CommandResult(
                            raw_output="",
                            success=False,
                            structured_output=[],
                            exit_code=-1,
                            error_message=str(e),
                        )
                        try:
                            # Wywołaj handler błędu
                            handler(context, e)
                        except Exception:
                            # Jeśli handler też rzucił wyjątek, kontynuuj normalną obsługę
                            pass
                        handled = True
                        break

                # Jeśli żaden handler nie obsłużył błędu i nie ma więcej prób
                if not handled and retries == self.max_retries:
                    return CommandResult(
                        raw_output="",
                        success=False,
                        structured_output=[],
                        exit_code=-1,
                        error_message=f"Command failed after {retries} retries: {str(e)}",
                    )

                # Przygotuj do ponowienia
                retries += 1
                time.sleep(self.retry_delay)

        # Zwrócenie wyniku w przypadku wyczerpania prób
        return CommandResult(
            raw_output="",
            success=False,
            structured_output=[],
            exit_code=-1,
            error_message=f"Command failed after {retries} retries: {str(last_exception)}",
        )

    def _clone(self) -> "CommandEnforcer":
        """
        Tworzy kopię instancji.

        Returns:
            CommandEnforcer: Nowa instancja z takimi samymi parametrami
        """
        new_instance: CommandEnforcer = CommandEnforcer(self.command)
        new_instance.max_retries = self.max_retries
        new_instance.retry_delay = self.retry_delay
        new_instance.validators = list(self.validators)
        new_instance.timeout = self.timeout
        new_instance.error_handlers = dict(self.error_handlers)
        new_instance.success_handlers = list(self.success_handlers)
        return new_instance

    def __call__(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
        """
        Umożliwia używanie CommandEnforcer jak normalnej komendy.

        Args:
            context: Kontekst wykonania komendy
            input_result: Opcjonalny wynik poprzedniej komendy

        Returns:
            CommandResult: Wynik wykonania komendy
        """
        return self.execute(context, input_result)

    # Statyczne metody pomocnicze

    @staticmethod
    def ensure_success_output_contains(pattern: str) -> Callable[[CommandResult], bool]:
        """
        Tworzy walidator sprawdzający, czy wynik zawiera określony tekst.

        Args:
            pattern: Wzorzec do sprawdzenia

        Returns:
            Callable: Funkcja walidująca
        """

        def validator(result: CommandResult) -> bool:
            if not result.success:
                return False
            return re.search(pattern, result.raw_output) is not None

        return validator

    @staticmethod
    def ensure_exit_code(exit_code: int) -> Callable[[CommandResult], bool]:
        """
        Tworzy walidator sprawdzający kod wyjścia.

        Args:
            exit_code: Oczekiwany kod wyjścia

        Returns:
            Callable: Funkcja walidująca
        """

        def validator(result: CommandResult) -> bool:
            return result.exit_code == exit_code

        return validator
