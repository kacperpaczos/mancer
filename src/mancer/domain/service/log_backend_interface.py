from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class LogLevel(Enum):
    """Poziomy logowania obsługiwane przez system."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogBackendInterface(ABC):
    """
    Interfejs dla backendów logowania.
    Każdy backend musi implementować te metody.
    """

    @abstractmethod
    def initialize(self, **kwargs) -> None:
        """
        Inicjalizuje backend loggera.

        Args:
            **kwargs: Parametry specyficzne dla danego backendu
        """
        pass

    @abstractmethod
    def log(
        self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Loguje wiadomość z określonym poziomem.

        Args:
            level: Poziom logowania
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        pass

    @abstractmethod
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje wiadomość debug.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        pass

    @abstractmethod
    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje wiadomość informacyjną.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        pass

    @abstractmethod
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje ostrzeżenie.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        pass

    @abstractmethod
    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje błąd.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        pass

    @abstractmethod
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje błąd krytyczny.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        pass

    @abstractmethod
    def log_input(self, command_name: str, data: Any) -> None:
        """
        Loguje dane wejściowe komendy (dla pipeline).

        Args:
            command_name: Nazwa komendy
            data: Dane wejściowe
        """
        pass

    @abstractmethod
    def log_output(self, command_name: str, data: Any) -> None:
        """
        Loguje dane wyjściowe komendy (dla pipeline).

        Args:
            command_name: Nazwa komendy
            data: Dane wyjściowe
        """
        pass

    @abstractmethod
    def log_command_chain(self, chain_description: List[Dict[str, Any]]) -> None:
        """
        Loguje łańcuch komend.

        Args:
            chain_description: Opis łańcucha komend
        """
        pass
