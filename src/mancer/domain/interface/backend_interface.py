from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..model.command_result import CommandResult


class BackendInterface(ABC):
    """Interfejs dla backendów wykonujących komendy"""
    
    @abstractmethod
    def execute_command(self, command: str, working_dir: Optional[str] = None, 
                       env_vars: Optional[Dict[str, str]] = None) -> CommandResult:
        """Wykonuje komendę na danym backendzie"""
        pass
    
    @abstractmethod
    def parse_output(self, command: str, raw_output: str, exit_code: int, 
                    error_output: str = "") -> CommandResult:
        """Parsuje wyjście komendy do standardowego formatu"""
        pass
    
    @abstractmethod
    def build_command_string(self, command_name: str, options: List[str], 
                           params: Dict[str, Any], flags: List[str]) -> str:
        """Buduje string komendy zgodny z danym backendem"""
        pass
