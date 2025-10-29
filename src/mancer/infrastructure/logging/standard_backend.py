import logging
import os
import sys
import time
from pprint import pformat
from typing import Any, Dict, List, Optional

from ...domain.service.log_backend_interface import LogBackendInterface, LogLevel


class StandardBackend(LogBackendInterface):
    """
    Standardowy backend logowania oparty na module logging Pythona.

    Używany jako fallback, gdy Icecream nie jest dostępny.
    """

    def __init__(self) -> None:
        """Inicjalizuje standardowy backend logowania."""
        self._logger = logging.getLogger("mancer")
        self._logger.setLevel(logging.DEBUG)
        self._log_level = LogLevel.INFO
        self._log_format = "%(asctime)sZ [%(levelname)s] %(message)s"
        self._log_dir = os.path.join(os.getcwd(), "logs")
        self._log_file = "mancer_commands.log"
        self._console_enabled = True
        self._file_enabled = False
        self._use_utc = True

    def initialize(self, **kwargs) -> None:
        """
        Inicjalizuje backend loggera.

        Args:
            **kwargs: Parametry konfiguracji logowania
                log_level: Poziom logowania
                log_format: Format wiadomości logowania
                log_dir: Katalog dla plików logów
                log_file: Nazwa pliku logu
                console_enabled: Czy logować do konsoli
                file_enabled: Czy logować do pliku
        """
        # Parametry konfiguracyjne
        log_level = kwargs.get("log_level", LogLevel.INFO)
        log_format = kwargs.get("log_format", self._log_format)
        log_dir = kwargs.get("log_dir", self._log_dir)
        log_file = kwargs.get("log_file", self._log_file)
        console_enabled = kwargs.get("console_enabled", True)
        file_enabled = kwargs.get("file_enabled", False)
        use_utc = kwargs.get("use_utc", True)

        # Zastosuj konfigurację
        self._log_level = log_level
        self._log_format = log_format
        self._log_dir = log_dir
        self._log_file = log_file
        self._console_enabled = console_enabled
        self._file_enabled = file_enabled
        self._use_utc = use_utc

        # Utwórz directory dla logów, jeśli nie istnieje
        if self._file_enabled and not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir, exist_ok=True)

        # Skonfiguruj logger
        self._configure_logger()

    def _configure_logger(self) -> None:
        """Konfiguruje logger Pythona."""
        # Usuń istniejące handlery
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # Ustaw nowy poziom logowania
        python_log_level = self._get_python_log_level(self._log_level)
        self._logger.setLevel(python_log_level)

        # Opcjonalnie wymuś UTC na formaterach
        formatter = logging.Formatter(self._log_format)
        if self._use_utc:
            formatter.converter = time.gmtime

        # Dodaj handler konsoli, jeśli włączony
        if self._console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(python_log_level)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

        # Dodaj handler pliku, jeśli włączony
        if self._file_enabled:
            log_path = os.path.join(self._log_dir, self._log_file)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(python_log_level)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    def _get_python_log_level(self, level: LogLevel) -> int:
        """Konwertuje LogLevel do poziomów logowania Pythona."""
        mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(level, logging.INFO)

    def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje wiadomość z określonym poziomem.

        Args:
            level: Poziom logowania
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        # Sprawdź czy poziom jest wystarczający
        if level.value < self._log_level.value:
            return

        # Konwersja poziomu logowania
        python_level = self._get_python_log_level(level)

        # Przygotuj wiadomość z kontekstem, jeśli istnieje
        if context:
            context_str = pformat(context, indent=2, width=100)
            log_message = f"{message}\nContext: {context_str}"
        else:
            log_message = message

        # Zaloguj wiadomość
        self._logger.log(python_level, log_message)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Loguje wiadomość debug."""
        self.log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Loguje wiadomość informacyjną."""
        self.log(LogLevel.INFO, message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Loguje ostrzeżenie."""
        self.log(LogLevel.WARNING, message, context)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Loguje błąd."""
        self.log(LogLevel.ERROR, message, context)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Loguje błąd krytyczny."""
        self.log(LogLevel.CRITICAL, message, context)

    def log_input(self, command_name: str, data: Any) -> None:
        """
        Loguje dane wejściowe komendy (dla pipeline).

        Args:
            command_name: Nazwa komendy
            data: Dane wejściowe
        """
        formatted_data = pformat(data, indent=2, width=100)
        self._logger.debug(f"► INPUT [{command_name}]:\n{formatted_data}")

    def log_output(self, command_name: str, data: Any) -> None:
        """
        Loguje dane wyjściowe komendy (dla pipeline).

        Args:
            command_name: Nazwa komendy
            data: Dane wyjściowe
        """
        formatted_data = pformat(data, indent=2, width=100)
        self._logger.debug(f"◄ OUTPUT [{command_name}]:\n{formatted_data}")

    def log_command_chain(self, chain_description: List[Dict[str, Any]]) -> None:
        """
        Loguje łańcuch komend.

        Args:
            chain_description: Opis łańcucha komend
        """
        # Przygotuj graficzną reprezentację łańcucha
        chain_steps = []
        for i, step in enumerate(chain_description):
            step_name = step.get("name", f"Step {i + 1}")
            step_type = step.get("type", "Unknown")
            connection = step.get("connection", "then")

            if i > 0:
                if connection == "pipe":
                    connector = " │ "
                else:
                    connector = " → "
            else:
                connector = ""

            chain_steps.append(f"{connector}{step_name} ({step_type})")

        chain_display = "\n".join(chain_steps)

        # Loguj łańcuch komend
        self._logger.info(f"Command chain:\n{chain_display}")
