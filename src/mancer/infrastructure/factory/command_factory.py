from typing import Dict, Type, Any, Optional
from ...domain.interface.command_interface import CommandInterface
from ..command.file.ls_command import LsCommand
from ..command.file.cp_command import CpCommand
from ..command.file.cd_command import CdCommand
from ..command.file.find_command import FindCommand
from ..command.system.ps_command import PsCommand
from ..command.system.systemctl_command import SystemctlCommand
from ..command.network.netstat_command import NetstatCommand

class CommandFactory:
    """Fabryka komend"""
    
    def __init__(self, backend_type: str = "bash"):
        self.backend_type = backend_type
        self._command_types: Dict[str, Type[CommandInterface]] = {}
        self._configured_commands: Dict[str, CommandInterface] = {}
        self._initialize_commands()
    
    def _initialize_commands(self) -> None:
        """Inicjalizuje dostępne typy komend"""
        # Komendy plikowe
        self._command_types["ls"] = LsCommand
        self._command_types["cp"] = CpCommand
        self._command_types["cd"] = CdCommand
        self._command_types["find"] = FindCommand
        
        # Komendy systemowe
        self._command_types["ps"] = PsCommand
        self._command_types["systemctl"] = SystemctlCommand
        
        # Komendy sieciowe
        self._command_types["netstat"] = NetstatCommand
    
    def create_command(self, command_name: str) -> CommandInterface:
        """Tworzy nową instancję komendy"""
        if command_name not in self._command_types:
            raise ValueError(f"Nieznana komenda: {command_name}")
            
        # Tworzymy nową instancję
        return self._command_types[command_name]()
    
    def register_command(self, alias: str, command: CommandInterface) -> None:
        """Rejestruje prekonfigurowaną komendę pod aliasem"""
        self._configured_commands[alias] = command
    
    def get_command(self, alias: str) -> CommandInterface:
        """Pobiera prekonfigurowaną komendę według aliasu"""
        if alias not in self._configured_commands:
            raise ValueError(f"Nie znaleziono komendy o aliasie: {alias}")
            
        # Zwracamy kopię, aby uniknąć modyfikacji oryginalnej komendy
        return self._configured_commands[alias].clone()
