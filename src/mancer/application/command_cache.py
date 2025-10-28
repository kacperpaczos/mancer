import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..domain.model.command_result import CommandResult


class CommandCache:
    """
    Klasa implementująca cache dla wyników komend ShellRunner.
    Przechowuje historię wykonanych komend, ich wyniki oraz metadane.
    Umożliwia wizualizację stanu i informacji zebranych podczas wykonywania komend.
    """

    def __init__(self, max_size: int = 100, auto_refresh: bool = False, refresh_interval: int = 5):
        """
        Inicjalizuje cache komend.

        Args:
            max_size: Maksymalna liczba przechowywanych wyników komend
            auto_refresh: Czy automatycznie odświeżać cache
            refresh_interval: Interwał odświeżania w sekundach (jeśli auto_refresh=True)
        """
        self._cache: Dict[str, Tuple[CommandResult, datetime, Dict[str, Any]]] = {}
        self._history: List[Tuple[str, datetime, bool]] = []  # (command_id, timestamp, success)
        self._max_size = max_size
        self._auto_refresh = auto_refresh
        self._refresh_interval = refresh_interval
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        self._lock = threading.RLock()

        # Jeśli włączono auto-refresh, uruchom wątek odświeżający
        if self._auto_refresh:
            self._start_refresh_thread()

    def _start_refresh_thread(self):
        """Uruchamia wątek odświeżający cache"""
        self._stop_refresh.clear()
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        if self._refresh_thread:
            self._refresh_thread.start()

    def _refresh_loop(self):
        """Pętla odświeżająca cache"""
        while not self._stop_refresh.is_set():
            # Tutaj można dodać logikę odświeżania cache
            # np. ponowne wykonanie komend, które mają flagę auto_refresh
            time.sleep(self._refresh_interval)

    def stop_refresh(self):
        """Zatrzymuje wątek odświeżający cache"""
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._stop_refresh.set()
            self._refresh_thread.join(timeout=2.0)

    def store(
        self,
        command_id: str,
        command_str: str,
        result: CommandResult,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Zapisuje wynik komendy w cache.

        Args:
            command_id: Unikalny identyfikator komendy
            command_str: Tekstowa reprezentacja komendy
            result: Wynik wykonania komendy
            metadata: Dodatkowe metadane (np. parametry wykonania)
        """
        with self._lock:
            timestamp = datetime.now()

            # Zapisz w cache
            self._cache[command_id] = (
                result,
                timestamp,
                {"command": command_str, "metadata": metadata or {}},
            )

            # Dodaj do historii
            self._history.append((command_id, timestamp, result.is_success()))

            # Jeśli przekroczono rozmiar, usuń najstarsze wpisy
            if len(self._cache) > self._max_size:
                oldest_id = self._history[0][0]
                del self._cache[oldest_id]
                self._history.pop(0)

    def get(self, command_id: str) -> Optional[CommandResult]:
        """
        Pobiera wynik komendy z cache.

        Args:
            command_id: Identyfikator komendy

        Returns:
            Wynik komendy lub None, jeśli nie znaleziono
        """
        with self._lock:
            if command_id in self._cache:
                return self._cache[command_id][0]
            return None

    def get_with_metadata(
        self, command_id: str
    ) -> Optional[Tuple[CommandResult, datetime, Dict[str, Any]]]:
        """
        Pobiera wynik komendy wraz z metadanymi.

        Args:
            command_id: Identyfikator komendy

        Returns:
            Krotka (wynik, timestamp, metadane) lub None, jeśli nie znaleziono
        """
        with self._lock:
            return self._cache.get(command_id)

    def get_history(
        self, limit: Optional[int] = None, success_only: bool = False
    ) -> List[Tuple[str, datetime, bool]]:
        """
        Pobiera historię wykonanych komend.

        Args:
            limit: Maksymalna liczba zwracanych wpisów (od najnowszych)
            success_only: Czy zwracać tylko komendy zakończone sukcesem

        Returns:
            Lista krotek (command_id, timestamp, success)
        """
        with self._lock:
            history = self._history
            if success_only:
                history = [entry for entry in history if entry[2]]

            if limit is not None:
                return history[-limit:]
            return history.copy()

    def clear(self) -> None:
        """Czyści cache"""
        with self._lock:
            self._cache.clear()
            self._history.clear()

    def set_auto_refresh(self, enabled: bool, interval: Optional[int] = None) -> None:
        """
        Włącza lub wyłącza automatyczne odświeżanie cache.

        Args:
            enabled: Czy włączyć auto-refresh
            interval: Nowy interwał odświeżania w sekundach (opcjonalnie)
        """
        with self._lock:
            if interval is not None:
                self._refresh_interval = interval

            # Jeśli zmieniono stan auto-refresh
            if enabled != self._auto_refresh:
                self._auto_refresh = enabled

                if enabled:
                    self._start_refresh_thread()
                else:
                    self.stop_refresh()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Zwraca statystyki cache.

        Returns:
            Słownik ze statystykami
        """
        with self._lock:
            success_count = sum(1 for _, _, success in self._history if success)
            return {
                "total_commands": len(self._history),
                "success_count": success_count,
                "error_count": len(self._history) - success_count,
                "cache_size": len(self._cache),
                "max_size": self._max_size,
                "auto_refresh": self._auto_refresh,
                "refresh_interval": self._refresh_interval,
            }

    def export_data(self, include_results: bool = True) -> Dict[str, Any]:
        """
        Eksportuje dane cache do formatu JSON.

        Args:
            include_results: Czy dołączać pełne wyniki komend

        Returns:
            Słownik z danymi cache
        """
        with self._lock:
            export: Dict[str, Any] = {
                "history": [
                    (cmd_id, ts.isoformat(), success) for cmd_id, ts, success in self._history
                ],
                "statistics": self.get_statistics(),
            }

            if include_results:
                export["results"] = {}
                for cmd_id, (result, ts, meta) in self._cache.items():
                    export["results"][cmd_id] = {
                        "timestamp": ts.isoformat(),
                        "success": result.is_success(),
                        "exit_code": result.exit_code,
                        "raw_output": result.raw_output,
                        "structured_output": result.structured_output,
                        "error_message": result.error_message,
                        "metadata": meta,
                    }

            return export

    def __len__(self) -> int:
        """Zwraca liczbę elementów w cache"""
        return len(self._cache)
