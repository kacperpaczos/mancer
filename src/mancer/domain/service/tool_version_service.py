import logging
import subprocess
from typing import List, Optional, Tuple

from ..model.config_manager import ConfigManager
from ..model.tool_version import ToolVersion, ToolVersionRegistry

logger = logging.getLogger(__name__)

class ToolVersionService:
    """Serwis do sprawdzania wersji narzędzi systemowych"""
    
    def __init__(self):
        self.registry = ToolVersionRegistry()
        self.config_manager = ConfigManager()
        self._initialize_from_config()
    
    def _initialize_from_config(self) -> None:
        """
        Inicjalizuje rejestr wersji na podstawie konfiguracji
        """
        # Sprawdź, czy weryfikacja wersji jest włączona
        if not self.config_manager.get_setting("version_checking.enabled", True):
            logger.info("Weryfikacja wersji narzędzi jest wyłączona w konfiguracji")
            return
        
        # Pobierz wszystkie narzędzia z konfiguracji
        tools_config = self.config_manager._config["tool_versions"].get("tools", {})
        
        # Zarejestruj wersje dla każdego narzędzia
        for tool_name, versions in tools_config.items():
            logger.debug(f"Ładowanie dozwolonych wersji dla {tool_name}: {versions}")
            self.registry.register_allowed_versions(tool_name, versions)
    
    def detect_tool_version(self, tool_name: str) -> Optional[ToolVersion]:
        """
        Wykrywa wersję narzędzia systemowego
        
        Args:
            tool_name: Nazwa narzędzia
            
        Returns:
            Obiekt ToolVersion z informacjami o wykrytej wersji lub None w przypadku błędu
        """
        # Najpierw sprawdź, czy wersja jest już w buforze
        cached_version = self.registry.get_detected_version(tool_name)
        if cached_version:
            return cached_version
        
        # Spróbuj wykryć wersję narzędzia
        try:
            # Sprawdź, czy narzędzie jest dostępne
            if not self._is_tool_available(tool_name):
                logger.warning(f"Narzędzie {tool_name} nie jest dostępne w systemie")
                return None
            
            # Wykonaj komendę z opcją --version
            result = subprocess.run(
                [tool_name, "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                timeout=5  # Timeout 5 sekund
            )
            
            # Jeśli komenda zwróciła błąd, spróbuj z opcją -v
            if result.returncode != 0:
                result = subprocess.run(
                    [tool_name, "-v"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
            
            # Jeśli nadal błąd, zwróć None
            if result.returncode != 0:
                logger.warning(f"Nie udało się uzyskać informacji o wersji dla {tool_name}")
                return None
            
            # Parsuj wyjście komendy
            version_output = result.stdout if result.stdout else result.stderr
            tool_version = ToolVersion.parse_version_output(tool_name, version_output)
            
            # Zapisz wykrytą wersję w buforze
            self.registry.update_detected_version(tool_version)
            
            return tool_version
            
        except subprocess.TimeoutExpired:
            logger.error(f"Przekroczono limit czasu podczas wykrywania wersji {tool_name}")
            return None
        except Exception as e:
            logger.error(f"Błąd podczas wykrywania wersji {tool_name}: {str(e)}")
            return None
    
    def _is_tool_available(self, tool_name: str) -> bool:
        """
        Sprawdza, czy narzędzie jest dostępne w systemie
        
        Args:
            tool_name: Nazwa narzędzia
            
        Returns:
            True, jeśli narzędzie jest dostępne, False w przeciwnym razie
        """
        return subprocess.run(
            ["which", tool_name], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        ).returncode == 0
    
    def is_version_allowed(self, tool_name: str) -> Tuple[bool, str]:
        """
        Sprawdza, czy wykryta wersja narzędzia jest dozwolona
        
        Args:
            tool_name: Nazwa narzędzia
            
        Returns:
            Krotka (is_allowed, message): 
            - is_allowed: True, jeśli wersja jest dozwolona, False w przeciwnym razie
            - message: Komunikat informacyjny
        """
        # Sprawdź, czy weryfikacja wersji jest włączona
        if not self.config_manager.get_setting("version_checking.enabled", True):
            return True, f"Weryfikacja wersji jest wyłączona, akceptuję wersję narzędzia {tool_name}"
            
        # Wykryj wersję narzędzia
        tool_version = self.detect_tool_version(tool_name)
        
        # Jeśli nie udało się wykryć wersji, zwróć odpowiedni komunikat
        if not tool_version:
            warn_on_missing = self.config_manager.get_setting("version_checking.warn_on_missing", True)
            if warn_on_missing:
                return False, f"Nie można wykryć wersji narzędzia {tool_name}"
            else:
                return True, f"Nie można wykryć wersji narzędzia {tool_name}, ale ostrzeżenia są wyłączone"
        
        # Sprawdź, czy wersja jest dozwolona
        is_allowed = self.registry.is_version_allowed(tool_name, tool_version.version)
        
        # Jeśli wersja jest dozwolona, zwróć True
        if is_allowed:
            return True, f"Wersja {tool_version.version} narzędzia {tool_name} jest dozwolona"
        else:
            # Jeśli wersja nie jest dozwolona, sprawdź czy ostrzeżenia są włączone
            warn_on_mismatch = self.config_manager.get_setting("version_checking.warn_on_mismatch", True)
            if warn_on_mismatch:
                allowed_versions = self.registry.allowed_versions.get(tool_name, set())
                allowed_str = ", ".join(allowed_versions) if allowed_versions else "brak zdefiniowanych wersji"
                return False, f"Wersja {tool_version.version} narzędzia {tool_name} nie jest dozwolona (dozwolone wersje: {allowed_str})"
            else:
                return True, f"Wersja {tool_version.version} narzędzia {tool_name} nie jest dozwolona, ale ostrzeżenia są wyłączone"
    
    def register_allowed_version(self, tool_name: str, version: str) -> None:
        """
        Rejestruje dozwoloną wersję narzędzia
        
        Args:
            tool_name: Nazwa narzędzia
            version: Wersja narzędzia
        """
        # Zarejestruj w rejestrze w pamięci
        self.registry.register_allowed_version(tool_name, version)
        
        # Zapisz do konfiguracji
        self.config_manager.add_allowed_tool_version(tool_name, version)
    
    def register_allowed_versions(self, tool_name: str, versions: List[str]) -> None:
        """
        Rejestruje wiele dozwolonych wersji narzędzia
        
        Args:
            tool_name: Nazwa narzędzia
            versions: Lista dozwolonych wersji
        """
        # Zarejestruj w rejestrze w pamięci
        self.registry.register_allowed_versions(tool_name, versions)
        
        # Zapisz do konfiguracji
        self.config_manager.set_allowed_tool_versions(tool_name, versions) 