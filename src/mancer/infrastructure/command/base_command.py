from abc import abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Type
from copy import deepcopy
from ...domain.interface.command_interface import CommandInterface
from ...domain.model.command_result import CommandResult
from ...domain.model.command_context import CommandContext

T = TypeVar('T', bound='BaseCommand')

class BaseCommand(CommandInterface):
    """Bazowa implementacja komendy"""
    
    def __init__(self, name: str):
        self.name = name
        self.options: List[str] = []
        self.parameters: Dict[str, Any] = {}
        self.flags: List[str] = []
    
    def with_option(self, option: str) -> T:
        """Dodaje opcję do komendy"""
        new_instance = self.clone()
        new_instance.options.append(option)
        return new_instance
    
    def with_param(self, name: str, value: Any) -> T:
        """Ustawia parametr komendy"""
        new_instance = self.clone()
        new_instance.parameters[name] = value
        return new_instance
    
    def with_flag(self, flag: str) -> T:
        """Dodaje flagę do komendy"""
        new_instance = self.clone()
        new_instance.flags.append(flag)
        return new_instance
    
    def clone(self) -> T:
        """Tworzy kopię komendy z tą samą konfiguracją"""
        new_instance = self.__class__()
        new_instance.options = deepcopy(self.options)
        new_instance.parameters = deepcopy(self.parameters)
        new_instance.flags = deepcopy(self.flags)
        return new_instance
    
    def build_command(self) -> str:
        """Buduje string komendy na podstawie konfiguracji"""
        cmd_parts = [self.name]
        
        # Dodajemy opcje (np. -l, -a)
        cmd_parts.extend(self.options)
        
        # Dodajemy flagi (np. --recursive)
        cmd_parts.extend(self.flags)
        
        # Dodajemy parametry
        for name, value in self.parameters.items():
            # Sprawdzamy, czy parametr ma specjalną obsługę
            param_str = self._format_parameter(name, value)
            if param_str:
                cmd_parts.append(param_str)
        
        # Dodajemy pozostałe argumenty specyficzne dla danej komendy
        additional_args = self._get_additional_args()
        if additional_args:
            cmd_parts.extend(additional_args)
        
        return " ".join(cmd_parts)
    
    @abstractmethod
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Implementacja wykonania komendy - do zaimplementowania w podklasach"""
        pass
    
    def _format_parameter(self, name: str, value: Any) -> str:
        """
        Formatuje pojedynczy parametr komendy.
        Można nadpisać w podklasach dla specjalnego formatowania.
        """
        return f"--{name}={value}"
    
    def _get_additional_args(self) -> List[str]:
        """
        Zwraca dodatkowe argumenty specyficzne dla podklasy.
        Do nadpisania w podklasach.
        """
        return []
    
    def _parse_output(self, raw_output: str) -> List[Any]:
        """
        Parsuje surowe wyjście komendy do struktury.
        Do nadpisania w podklasach.
        """
        return [raw_output]
