from typing import Dict, Optional, Type

from ...domain.interface.command_interface import CommandInterface
from ..command.file.cat_command import CatCommand
from ..command.file.cd_command import CdCommand
from ..command.file.cp_command import CpCommand
from ..command.file.find_command import FindCommand
from ..command.file.grep_command import GrepCommand
from ..command.file.head_command import HeadCommand
from ..command.file.ls_command import LsCommand
from ..command.file.tail_command import TailCommand
from ..command.network.netstat_command import NetstatCommand
from ..command.system.df_command import DfCommand
from ..command.system.echo_command import EchoCommand
from ..command.system.hostname_command import HostnameCommand
from ..command.system.ps_command import PsCommand
from ..command.system.systemctl_command import SystemctlCommand


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
        self._command_types["grep"] = GrepCommand
        self._command_types["cat"] = CatCommand
        self._command_types["tail"] = TailCommand
        self._command_types["head"] = HeadCommand
        
        # Komendy systemowe
        self._command_types["ps"] = PsCommand
        self._command_types["systemctl"] = SystemctlCommand
        self._command_types["hostname"] = HostnameCommand
        self._command_types["df"] = DfCommand
        self._command_types["echo"] = EchoCommand
        
        # Komendy sieciowe
        self._command_types["netstat"] = NetstatCommand
    
    def create_command(self, command_name: str) -> Optional[CommandInterface]:
        """Tworzy nową instancję komendy"""
        if command_name not in self._command_types:
            return None
            
        # Tworzymy nową instancję
        return self._command_types[command_name]()
    
    def register_command(self, alias: str, command: CommandInterface) -> None:
        """Rejestruje prekonfigurowaną komendę pod aliasem"""
        self._configured_commands[alias] = command
    
    def get_command(self, alias: str) -> Optional[CommandInterface]:
        """Pobiera prekonfigurowaną komendę według aliasu"""
        if alias not in self._configured_commands:
            return None
            
        # Zwracamy kopię, aby uniknąć modyfikacji oryginalnej komendy
        return self._configured_commands[alias].clone()
