import logging
import sys
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
from pprint import pformat

# Importuję interfejs backendu logowania
from ...domain.service.log_backend_interface import LogBackendInterface, LogLevel

# Próbujemy importować icecream, ale jeśli nie jest dostępny, definiujemy fallback
try:
    from icecream import ic
    ICECREAM_AVAILABLE = True
except ImportError:
    # Icecream nie jest dostępny, tworzymy fallback
    ICECREAM_AVAILABLE = False
    
    def ic(*args, **kwargs):
        """Fallback dla icecream, który po prostu wypisuje argumenty."""
        if not args and not kwargs:
            return
        
        output_parts = []
        for arg in args:
            output_parts.append(str(arg))
        for key, value in kwargs.items():
            output_parts.append(f"{key}={value}")
        
        print("[IC]", " | ".join(output_parts))
        return args[0] if len(args) == 1 else args


class IcecreamBackend(LogBackendInterface):
    """
    Backend logowania wykorzystujący Icecream do formatowania i wyświetlania logów.
    
    Jeśli Icecream nie jest dostępny, używany jest prosty fallback.
    """
    
    def __init__(self) -> None:
        """Inicjalizuje backend Icecream."""
        self._console_logger = logging.getLogger("mancer.icecream")
        self._console_logger.setLevel(logging.DEBUG)
        self._file_logger = None
        self._log_level = LogLevel.INFO
        self._log_format = '%(asctime)s [%(levelname)s] %(message)s'
        self._log_dir = os.path.join(os.getcwd(), 'logs')
        self._log_file = 'mancer_commands.log'
        self._console_enabled = True
        self._file_enabled = False
        
        # Możemy skonfigurować wygląd icecream, jeśli jest dostępny
        if ICECREAM_AVAILABLE:
            ic.configureOutput(prefix='[Mancer] ', includeContext=True)
    
    def initialize(self, **kwargs) -> None:
        """
        Inicjalizuje backend loggera Icecream.
        
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
        log_level = kwargs.get('log_level', LogLevel.INFO)
        log_format = kwargs.get('log_format', self._log_format)
        log_dir = kwargs.get('log_dir', self._log_dir)
        log_file = kwargs.get('log_file', self._log_file)
        console_enabled = kwargs.get('console_enabled', True)
        file_enabled = kwargs.get('file_enabled', False)
        
        # Zastosuj konfigurację
        self._log_level = log_level
        self._log_format = log_format
        self._log_dir = log_dir
        self._log_file = log_file
        self._console_enabled = console_enabled
        self._file_enabled = file_enabled
        
        # Utwórz directory dla logów, jeśli nie istnieje
        if self._file_enabled and not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir, exist_ok=True)
        
        # Skonfiguruj loggery konsolowy i plikowy
        self._configure_loggers()
        
        # Jeśli Icecream jest dostępny, możemy skonfigurować dodatkowe opcje
        if ICECREAM_AVAILABLE:
            output_prefix = kwargs.get('ic_prefix', '[Mancer] ')
            include_context = kwargs.get('ic_include_context', True)
            ic.configureOutput(prefix=output_prefix, includeContext=include_context)
    
    def _configure_loggers(self) -> None:
        """Konfiguruje loggery dla konsoli i pliku."""
        # Usuń istniejące handlery
        for handler in self._console_logger.handlers[:]:
            self._console_logger.removeHandler(handler)
        
        # Ustaw nowy poziom logowania
        python_log_level = self._get_python_log_level(self._log_level)
        self._console_logger.setLevel(python_log_level)
        
        # Dodaj handler konsoli, jeśli włączony
        if self._console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(python_log_level)
            console_handler.setFormatter(logging.Formatter(self._log_format))
            self._console_logger.addHandler(console_handler)
        
        # Dodaj handler pliku, jeśli włączony
        if self._file_enabled:
            log_path = os.path.join(self._log_dir, self._log_file)
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(python_log_level)
            file_handler.setFormatter(logging.Formatter(self._log_format))
            self._console_logger.addHandler(file_handler)
    
    def _get_python_log_level(self, level: LogLevel) -> int:
        """Konwertuje LogLevel do poziomów logowania Pythona."""
        mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        return mapping.get(level, logging.INFO)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formatuje kontekst do formatu czytelnego dla człowieka."""
        if not context:
            return ""
        
        try:
            return pformat(context, indent=2, width=100)
        except Exception:
            return str(context)
    
    def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Loguje wiadomość z określonym poziomem.
        
        Args:
            level: Poziom logowania
            message: Wiadomość do zalogowania
            context: Opcjonalny kontekst (dane dodatkowe)
        """
        # Sprawdź, czy poziom jest wystarczający
        if level.value < self._log_level.value:
            return
        
        # Przygotuj dane kontekstowe
        context_str = self._format_context(context) if context else None
        
        # Loguj do Icecream lub fallbacku
        log_prefix = f"[{level.name}]"
        if context_str:
            ic(log_prefix, message, context_str)
        else:
            ic(log_prefix, message)
        
        # Loguj również do standardowego loggera
        python_level = self._get_python_log_level(level)
        if context_str:
            self._console_logger.log(python_level, f"{message}\nContext: {context_str}")
        else:
            self._console_logger.log(python_level, message)
    
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
        ic(f"➡️ INPUT [{command_name}]", data)
        self._console_logger.debug(f"Command input [{command_name}]: {pformat(data)}")
    
    def log_output(self, command_name: str, data: Any) -> None:
        """
        Loguje dane wyjściowe komendy (dla pipeline).
        
        Args:
            command_name: Nazwa komendy
            data: Dane wyjściowe
        """
        ic(f"⬅️ OUTPUT [{command_name}]", data)
        self._console_logger.debug(f"Command output [{command_name}]: {pformat(data)}")
    
    def log_command_chain(self, chain_description: List[Dict[str, Any]]) -> None:
        """
        Loguje łańcuch komend.
        
        Args:
            chain_description: Opis łańcucha komend
        """
        # Przygotuj graficzną reprezentację łańcucha
        chain_steps = []
        for i, step in enumerate(chain_description):
            step_name = step.get('name', f'Step {i+1}')
            step_type = step.get('type', 'Unknown')
            connection = step.get('connection', 'then')
            
            if i > 0:
                if connection == 'pipe':
                    connector = " │ "
                else:
                    connector = " → "
            else:
                connector = ""
                
            chain_steps.append(f"{connector}{step_name} ({step_type})")
        
        chain_display = "\n".join(chain_steps)
        
        # Loguj łańcuch komend
        ic("📊 COMMAND CHAIN:")
        ic(chain_display)
        
        # Loguj również do standardowego loggera
        self._console_logger.info(f"Command chain:\n{chain_display}") 