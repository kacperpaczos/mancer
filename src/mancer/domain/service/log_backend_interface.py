from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Union

import polars as pl
from typing_extensions import TypeAlias

# Type for log data
LogData: TypeAlias = Union[str, pl.DataFrame, Dict[str, object], List[object], None]


class LogLevel(Enum):
    """Poziomy logowania obsługiwane przez system."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LoggingConfigDict(TypedDict, total=False):
    """TypedDict for logging backend configuration parameters."""

    log_level: Union[LogLevel, str]
    log_format: str
    log_dir: str
    log_file: str
    console_enabled: bool
    file_enabled: bool
    use_utc: bool
    force_standard: bool  # Only for MancerLogger
    ic_prefix: str  # Only for IcecreamBackend
    ic_include_context: bool  # Only for IcecreamBackend


class LogBackendInterface(ABC):
    """
    Interfejs dla backendów logowania.
    Każdy backend musi implementować te metody.
    """

    @abstractmethod
    def initialize(self, **kwargs: Any) -> None:
        """
        Inicjalizuje backend loggera.

        Args:
            **kwargs: Parametry konfiguracji logowania
        """
        pass

    @abstractmethod
    def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None) -> None:
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
    def log_input(self, command_name: str, data: LogData) -> None:
        """
        Loguje dane wejściowe komendy (dla pipeline).

        Args:
            command_name: Nazwa komendy
            data: Dane wejściowe
        """
        pass

    @abstractmethod
    def log_output(self, command_name: str, data: LogData) -> None:
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
