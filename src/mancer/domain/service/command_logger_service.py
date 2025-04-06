import logging
import os
import sys
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json
import threading

class CommandLoggerService:
    """
    Uniwersalny serwis logowania komend w Mancer.
    
    Zapewnia jednolite logowanie wszystkich komend oraz ich wyników.
    Umożliwia łatwe konfigurowanie poziomu logowania oraz lokalizacji plików logów.
    """
    
    # Singleton - jedna instancja serwisu
    _instance = None
    _lock = threading.RLock()
    
    # Domyślna konfiguracja
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_LOG_FORMAT = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    DEFAULT_LOG_DIR = 'logs'
    DEFAULT_LOG_FILE = 'mancer_commands.log'
    
    @staticmethod
    def get_instance():
        """Zwraca singleton instancję serwisu logowania"""
        with CommandLoggerService._lock:
            if CommandLoggerService._instance is None:
                CommandLoggerService._instance = CommandLoggerService()
            return CommandLoggerService._instance
    
    def __init__(self):
        """Inicjalizuje serwis logowania - powinien być wywołany tylko przez get_instance()"""
        self._loggers = {}
        self._log_level = self.DEFAULT_LOG_LEVEL
        self._log_format = self.DEFAULT_LOG_FORMAT
        self._log_dir = self.DEFAULT_LOG_DIR
        self._log_file = self.DEFAULT_LOG_FILE
        self._console_enabled = True
        self._file_enabled = False
        self._initialized = False
        self._command_history = []
    
    def initialize(self, log_level: Optional[Union[int, str]] = None,
                  log_format: Optional[str] = None,
                  log_dir: Optional[str] = None,
                  log_file: Optional[str] = None,
                  console_enabled: bool = True,
                  file_enabled: bool = False) -> None:
        """
        Inicjalizuje serwis logowania z podaną konfiguracją.
        
        Args:
            log_level: Poziom logowania (domyślnie INFO)
            log_format: Format logów
            log_dir: Katalog z logami
            log_file: Nazwa pliku logu
            console_enabled: Czy logować do konsoli
            file_enabled: Czy logować do pliku
        """
        with self._lock:
            # Ustaw poziom logowania
            if log_level is not None:
                if isinstance(log_level, str):
                    level_map = {
                        'debug': logging.DEBUG,
                        'info': logging.INFO,
                        'warning': logging.WARNING,
                        'error': logging.ERROR,
                        'critical': logging.CRITICAL
                    }
                    self._log_level = level_map.get(log_level.lower(), logging.INFO)
                else:
                    self._log_level = log_level
            
            # Ustaw pozostałe parametry
            if log_format is not None:
                self._log_format = log_format
            if log_dir is not None:
                self._log_dir = log_dir
            if log_file is not None:
                self._log_file = log_file
                
            self._console_enabled = console_enabled
            self._file_enabled = file_enabled
            
            # Utwórz katalog logów, jeśli nie istnieje
            if self._file_enabled and not os.path.exists(self._log_dir):
                os.makedirs(self._log_dir, exist_ok=True)
            
            # Ustaw flagę inicjalizacji
            self._initialized = True
    
    def _get_logger(self, name: str) -> logging.Logger:
        """
        Pobiera lub tworzy logger o podanej nazwie.
        
        Args:
            name: Nazwa loggera (najczęściej nazwa klasy komendy)
            
        Returns:
            Obiekt loggera
        """
        with self._lock:
            if name in self._loggers:
                return self._loggers[name]
            
            # Stwórz nowy logger
            logger = logging.getLogger(f"mancer.command.{name}")
            logger.setLevel(self._log_level)
            logger.propagate = False  # Wyłącz propagację do nadrzędnych loggerów
            
            # Usuń istniejące handlery
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # Dodaj handler konsoli, jeśli włączony
            if self._console_enabled:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(self._log_level)
                console_handler.setFormatter(logging.Formatter(self._log_format))
                logger.addHandler(console_handler)
            
            # Dodaj handler pliku, jeśli włączony
            if self._file_enabled:
                log_path = os.path.join(self._log_dir, self._log_file)
                file_handler = logging.FileHandler(log_path, encoding='utf-8')
                file_handler.setLevel(self._log_level)
                file_handler.setFormatter(logging.Formatter(self._log_format))
                logger.addHandler(file_handler)
            
            # Zapisz logger w cache
            self._loggers[name] = logger
            return logger
    
    def log_command_start(self, command_name: str, command_string: str, 
                        context_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Loguje rozpoczęcie wykonania komendy.
        
        Args:
            command_name: Nazwa komendy (np. ls, grep, itp.)
            command_string: Pełna komenda do wykonania (np. 'ls -la /tmp')
            context_params: Dodatkowe parametry kontekstu
            
        Returns:
            Słownik z informacjami o rozpoczętej komendzie (do użycia w log_command_end)
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        # Przygotuj informacje o komendzie
        command_info = {
            'command_name': command_name,
            'command_string': command_string,
            'context': context_params or {},
            'start_time': start_time,
            'start_timestamp': timestamp,
            'execution_id': f"{command_name}_{int(start_time * 1000)}"
        }
        
        # Pobierz logger dla tej komendy
        logger = self._get_logger(command_name)
        
        # Zaloguj rozpoczęcie
        logger.info(f"Command started: {command_string}")
        if context_params and self._log_level <= logging.DEBUG:
            logger.debug(f"Context: {json.dumps(context_params, default=str)}")
        
        # Dodaj do historii
        with self._lock:
            self._command_history.append({
                'command': command_info,
                'completed': False
            })
        
        return command_info
    
    def log_command_end(self, command_info: Dict[str, Any], 
                      success: bool, exit_code: int, 
                      output: Optional[str] = None, 
                      error: Optional[str] = None,
                      execution_time: Optional[float] = None) -> None:
        """
        Loguje zakończenie wykonania komendy.
        
        Args:
            command_info: Informacje z log_command_start
            success: Czy komenda zakończyła się sukcesem
            exit_code: Kod wyjścia komendy
            output: Wyjście komendy (opcjonalne)
            error: Błąd komendy (opcjonalne)
            execution_time: Czas wykonania w sekundach (opcjonalne, obliczane automatycznie)
        """
        # Oblicz czas wykonania, jeśli nie podano
        if execution_time is None and 'start_time' in command_info:
            execution_time = time.time() - command_info['start_time']
        
        # Pobierz logger dla tej komendy
        command_name = command_info.get('command_name', 'unknown')
        logger = self._get_logger(command_name)
        
        # Zaloguj zakończenie
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Command {status} [{command_name}] (exit: {exit_code}) in {execution_time:.3f}s")
        
        # Zaloguj szczegóły na poziomie DEBUG
        if self._log_level <= logging.DEBUG:
            if error and not success:
                logger.debug(f"Error: {error[:500]}")
            if output and len(output) < 1000:  # Nie loguj zbyt długich wyników
                logger.debug(f"Output: {output}")
        
        # Zaktualizuj historię
        with self._lock:
            for entry in self._command_history:
                if entry.get('command', {}).get('execution_id') == command_info.get('execution_id'):
                    entry['completed'] = True
                    entry['result'] = {
                        'success': success,
                        'exit_code': exit_code,
                        'execution_time': execution_time,
                        'end_timestamp': datetime.now().isoformat()
                    }
                    break
    
    def get_command_history(self, limit: Optional[int] = None, 
                           success_only: bool = False) -> List[Dict[str, Any]]:
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
                history = [entry for entry in history 
                          if entry.get('completed', False) and entry.get('result', {}).get('success', False)]
            
            if limit is not None and limit > 0:
                return history[-limit:]
            
            return history.copy()
    
    def export_history(self, filepath: Optional[str] = None) -> str:
        """
        Eksportuje historię komend do pliku JSON.
        
        Args:
            filepath: Ścieżka do pliku (opcjonalna, generowana automatycznie)
            
        Returns:
            Ścieżka do utworzonego pliku
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(self._log_dir, f'command_history_{timestamp}.json')
        
        # Upewnij się, że katalog istnieje
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Zapisz historię do pliku
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.get_command_history(), f, indent=2, default=str)
        
        return filepath
    
    def clear_history(self) -> None:
        """Czyści historię komend"""
        with self._lock:
            self._command_history.clear() 