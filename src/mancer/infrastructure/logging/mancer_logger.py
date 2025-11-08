import os
import threading
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Type, Union, cast

from ...domain.service.log_backend_interface import LogBackendInterface, LogLevel
from .icecream_backend import ICECREAM_AVAILABLE, IcecreamBackend
from .standard_backend import StandardBackend


class MancerLogger:
    """
    Główna fasada do logowania w frameworku Mancer.

    Zapewnia jednolite API do logowania niezależnie od wybranego backendu.
    Automatycznie wykrywa dostępność Icecream i wybiera odpowiedni backend.
    """

    # Singleton - jedna instancja dla całej aplikacji
    _instance: ClassVar[Optional["MancerLogger"]] = None
    _lock: ClassVar[threading.RLock] = threading.RLock()

    @classmethod
    def get_instance(cls) -> "MancerLogger":
        """
        Pobiera singleton instancję MancerLogger.

        Returns:
            Instancja MancerLogger
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = MancerLogger()
            return cls._instance

    def __init__(self):
        """
        Inicjalizuje logger. Nie należy wywoływać bezpośrednio - użyj get_instance().
        """
        self._backend = self._create_backend()
        self._initialized = False
        self._command_history = []
        self._pipeline_data = {}

    def _create_backend(self) -> LogBackendInterface:
        """
        Tworzy odpowiedni backend logowania na podstawie dostępności Icecream.

        Returns:
            Backend logowania
        """
        if ICECREAM_AVAILABLE:
            return IcecreamBackend()
        return StandardBackend()

    def initialize(self, **kwargs: Any) -> None:
        """
        Inicjalizuje system logowania z podanymi parametrami.

        Args:
                log_level: Poziom logowania (LogLevel lub string 'debug', 'info', itd.)
                log_format: Format wiadomości
                log_dir: Katalog logów
                log_file: Nazwa pliku logu
                console_enabled: Czy logować do konsoli
                file_enabled: Czy logować do pliku
            use_utc: Czy używać UTC
                force_standard: Czy wymusić użycie standardowego backendu
            ic_prefix: Prefiks dla Icecream
            ic_include_context: Czy włączyć kontekst w Icecream
        """
        with self._lock:
            # Sprawdź, czy mamy wymusić standardowy backend
            if force_standard and isinstance(self._backend, IcecreamBackend):
                self._backend = StandardBackend()

            # Konwersja poziomu logowania z stringa jeśli potrzeba
            if isinstance(log_level, str):
                level_map = {
                    "debug": LogLevel.DEBUG,
                    "info": LogLevel.INFO,
                    "warning": LogLevel.WARNING,
                    "error": LogLevel.ERROR,
                    "critical": LogLevel.CRITICAL,
                }
                converted_log_level = level_map.get(log_level.lower(), LogLevel.INFO)
            else:
                converted_log_level = log_level

            # Inicjalizuj backend
            self._backend.initialize(
                log_level=converted_log_level,
                log_format=log_format,
                log_dir=log_dir,
                log_file=log_file,
                console_enabled=console_enabled,
                file_enabled=file_enabled,
                use_utc=use_utc,
                force_standard=force_standard,
                ic_prefix=ic_prefix,
                ic_include_context=ic_include_context,
            )
            self._initialized = True

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje wiadomość debug.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        self._ensure_initialized()
        self._backend.debug(message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje wiadomość informacyjną.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        self._ensure_initialized()
        self._backend.info(message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje ostrzeżenie.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        self._ensure_initialized()
        self._backend.warning(message, context)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje błąd.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        self._ensure_initialized()
        self._backend.error(message, context)

    def critical(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje błąd krytyczny.

        Args:
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        self._ensure_initialized()
        self._backend.critical(message, context)

    def log_command_start(
        self,
        command_name: str,
        command_string: str,
        context_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Loguje rozpoczęcie wykonania komendy.

        Args:
            command_name: Nazwa komendy
            command_string: Pełna komenda do wykonania
            context_params: Dodatkowe parametry kontekstu

        Returns:
            Słownik z informacjami o rozpoczętej komendzie (do użycia w log_command_end)
        """
        self._ensure_initialized()

        import time
        from datetime import datetime

        # Przygotuj informacje o komendzie
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        execution_id = f"{command_name}_{int(start_time * 1000)}"

        command_info = {
            "command_name": command_name,
            "command_string": command_string,
            "context": context_params or {},
            "start_time": start_time,
            "start_timestamp": timestamp,
            "execution_id": execution_id,
        }

        # Zaloguj rozpoczęcie
        self.info(
            f"Command started: {command_string}",
            {"command_name": command_name, "execution_id": execution_id},
        )

        # Dodaj do historii
        with self._lock:
            self._command_history.append({"command": command_info, "completed": False})

        return command_info

    def log_command_end(
        self,
        command_info: Dict[str, Any],
        success: bool,
        exit_code: int,
        output: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Loguje zakończenie wykonania komendy.

        Args:
            command_info: Informacje z log_command_start
            success: Czy komenda zakończyła się sukcesem
            exit_code: Kod wyjścia komendy
            output: Wyjście komendy (opcjonalne)
            error: Błąd komendy (opcjonalne)
        """
        self._ensure_initialized()

        import time

        # Oblicz czas wykonania
        execution_time = time.time() - command_info.get("start_time", time.time())
        command_name = command_info.get("command_name", "unknown")
        execution_id = command_info.get("execution_id", "")

        # Zaloguj zakończenie
        status = "SUCCESS" if success else "FAILED"
        self.info(
            f"Command {status}: {command_name} (exit: {exit_code}) in {execution_time:.3f}s",
            {
                "command_name": command_name,
                "execution_id": execution_id,
                "exit_code": exit_code,
                "execution_time": execution_time,
            },
        )

        # Zaloguj błąd, jeśli wystąpił
        if error and not success:
            self.error(
                f"Command error: {error}",
                {"command_name": command_name, "execution_id": execution_id},
            )

        # Zaktualizuj historię
        with self._lock:
            for entry in self._command_history:
                if entry.get("command", {}).get("execution_id") == execution_id:
                    entry["completed"] = True
                    entry["result"] = {
                        "success": success,
                        "exit_code": exit_code,
                        "execution_time": execution_time,
                        "end_timestamp": datetime.now().isoformat(),
                    }
                    break

    def log_command_input(self, command_name: str, data: Any) -> None:
        """
        Loguje dane wejściowe komendy (dla pipeline).

        Args:
            command_name: Nazwa komendy
            data: Dane wejściowe
        """
        self._ensure_initialized()
        self._backend.log_input(command_name, data)

        # Zapisz dane wejściowe do śledzenia pipeline'a
        with self._lock:
            if command_name not in self._pipeline_data:
                self._pipeline_data[command_name] = {}
            self._pipeline_data[command_name]["input"] = data

    def log_command_output(self, command_name: str, data: Any) -> None:
        """
        Loguje dane wyjściowe komendy (dla pipeline).

        Args:
            command_name: Nazwa komendy
            data: Dane wyjściowe
        """
        self._ensure_initialized()
        self._backend.log_output(command_name, data)

        # Zapisz dane wyjściowe do śledzenia pipeline'a
        with self._lock:
            if command_name not in self._pipeline_data:
                self._pipeline_data[command_name] = {}
            self._pipeline_data[command_name]["output"] = data

    def log_command_chain(self, chain: List[Dict[str, Any]]) -> None:
        """
        Loguje łańcuch komend.

        Args:
            chain: Lista kroków w łańcuchu komend
        """
        self._ensure_initialized()
        self._backend.log_command_chain(chain)

    def get_command_history(self, limit: Optional[int] = None, success_only: bool = False) -> List[Dict[str, Any]]:
        """
        Pobiera historię wykonanych komend.

        Args:
            limit: Maksymalna liczba zwracanych wpisów (od najnowszych)
            success_only: Czy zwracać tylko komendy zakończone sukcesem

        Returns:
            Lista słowników z informacjami o komendach
        """
        with self._lock:
            history = self._command_history

            if success_only:
                history = [
                    entry
                    for entry in history
                    if entry.get("completed", False) and entry.get("result", {}).get("success", False)
                ]

            if limit is not None and limit > 0:
                return history[-limit:]

            return history.copy()

    def get_pipeline_data(self, command_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Pobiera dane pipeline'a dla określonej komendy lub wszystkich komend.

        Args:
            command_name: Nazwa komendy (None dla wszystkich komend)

        Returns:
            Słownik z danymi wejściowymi i wyjściowymi dla komendy
        """
        with self._lock:
            if command_name:
                return cast(Dict[str, Any], self._pipeline_data.get(command_name, {}))
            return self._pipeline_data.copy()

    def clear_pipeline_data(self) -> None:
        """Czyści wszystkie dane pipeline'a."""
        with self._lock:
            self._pipeline_data.clear()

    def clear_history(self) -> None:
        """Czyści historię komend."""
        with self._lock:
            self._command_history.clear()

    def export_history(self, filepath: Optional[str] = None) -> str:
        """
        Eksportuje historię komend do pliku JSON.

        Args:
            filepath: Ścieżka do pliku (jeśli None, generowana automatycznie)

        Returns:
            Ścieżka do utworzonego pliku
        """
        import json
        from datetime import datetime

        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join("logs", f"command_history_{timestamp}.json")

        # Upewnij się, że katalog istnieje
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Zapisz historię do pliku
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.get_command_history(), f, indent=2, default=str)

        self.info(f"Command history exported to: {filepath}")
        return filepath

    def _ensure_initialized(self) -> None:
        """
        Upewnia się, że logger został zainicjalizowany.
        Jeśli nie, inicjalizuje go z domyślnymi parametrami.
        """
        if not self._initialized:
            self.initialize()

    @property
    def backend(self) -> LogBackendInterface:
        """Zwraca aktualnie używany backend logowania."""
        return self._backend

    def set_backend(self, backend_type: Type[LogBackendInterface]) -> None:
        """
        Zmienia backend logowania.

        Args:
            backend_type: Klasa nowego backendu
        """
        with self._lock:
            # Zapamiętaj ustawienia starego backendu
            self._backend = backend_type()

            # Inicjalizuj nowy backend
            self._backend.initialize()
            self._initialized = True
