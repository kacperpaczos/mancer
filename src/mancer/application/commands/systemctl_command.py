from typing import Optional, cast
from .base_command import BaseCommand

class SystemctlCommand(BaseCommand):
    """Klasa do obsługi komend systemctl"""
    
    def __init__(self):
        super().__init__("systemctl")
    
    def with_sudo(self, password: Optional[str] = None) -> 'SystemctlCommand':
        """
        Dodaje sudo do komendy.
        
        Args:
            password: Hasło do sudo (opcjonalnie)
            
        Returns:
            self: Instancja komendy (do łańcuchowania metod)
        """
        if password:
            return cast(SystemctlCommand, self.with_param("sudo_password", password))
        return cast(SystemctlCommand, self.with_option("sudo"))
    
    def status(self, service: str) -> 'SystemctlCommand':
        """Sprawdza status usługi"""
        return cast(SystemctlCommand, self.with_param("command", "status").with_param("service", service))
    
    def start(self, service: str) -> 'SystemctlCommand':
        """Uruchamia usługę"""
        return cast(SystemctlCommand, self.with_param("command", "start").with_param("service", service))
    
    def stop(self, service: str) -> 'SystemctlCommand':
        """Zatrzymuje usługę"""
        return cast(SystemctlCommand, self.with_param("command", "stop").with_param("service", service))
    
    def restart(self, service: str) -> 'SystemctlCommand':
        """Restartuje usługę"""
        return cast(SystemctlCommand, self.with_param("command", "restart").with_param("service", service))
    
    def reload(self, service: str) -> 'SystemctlCommand':
        """Przeładowuje konfigurację usługi"""
        return cast(SystemctlCommand, self.with_param("command", "reload").with_param("service", service))
    
    def enable(self, service: str) -> 'SystemctlCommand':
        """Włącza usługę do uruchamiania przy starcie systemu"""
        return cast(SystemctlCommand, self.with_param("command", "enable").with_param("service", service))
    
    def disable(self, service: str) -> 'SystemctlCommand':
        """Wyłącza usługę z uruchamiania przy starcie systemu"""
        return cast(SystemctlCommand, self.with_param("command", "disable").with_param("service", service))
    
    def is_active(self, service: str) -> 'SystemctlCommand':
        """Sprawdza czy usługa jest aktywna"""
        return cast(SystemctlCommand, self.with_param("command", "is-active").with_param("service", service))
    
    def is_enabled(self, service: str) -> 'SystemctlCommand':
        """Sprawdza czy usługa jest włączona do uruchamiania przy starcie systemu"""
        return cast(SystemctlCommand, self.with_param("command", "is-enabled").with_param("service", service))
    
    def list_units(self) -> 'SystemctlCommand':
        """Wyświetla listę jednostek"""
        return cast(SystemctlCommand, self.with_param("command", "list-units"))
    
    def build_command(self) -> str:
        """
        Buduje pełną komendę z parametrami.
        
        Returns:
            str: Pełna komenda gotowa do wykonania
        """
        parts = [self._command_name]
        
        # Dodaj komendę
        if "command" in self._params:
            parts.append(str(self._params["command"]))
        
        # Dodaj opcje
        for option in self._options:
            if len(option) == 1:
                parts.append(f"-{option}")
            else:
                parts.append(f"--{option}")
        
        # Dodaj usługę na końcu (jeśli istnieje)
        if "service" in self._params:
            parts.append(str(self._params["service"]))
        
        # Dodaj pozostałe parametry (poza command i service)
        for name, value in self._params.items():
            if name in ["command", "service", "sudo_password"]:
                continue
                
            if isinstance(value, bool):
                if value:
                    parts.append(f"--{name}")
            else:
                parts.append(f"--{name}")
                parts.append(str(value))
        
        command = " ".join(parts)
        
        # Dodaj sudo jeśli wymagane
        if "sudo_password" in self._params:
            password = self._params["sudo_password"]
            command = f"echo '{password}' | sudo -S {command}"
        elif "sudo" in self._options:
            command = f"sudo {command}"
            
        return command 