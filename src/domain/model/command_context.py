from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class CommandContext:
    """Kontekst wykonania komendy"""
    current_directory: str = "."
    environment_variables: Dict[str, str] = field(default_factory=dict)
    command_history: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def change_directory(self, new_directory: str) -> None:
        """Zmienia bieżący katalog w kontekście"""
        self.current_directory = new_directory
        
    def add_to_history(self, command_string: str) -> None:
        """Dodaje komendę do historii"""
        self.command_history.append(command_string)
        
    def set_parameter(self, key: str, value: Any) -> None:
        """Ustawia parametr kontekstu"""
        self.parameters[key] = value
        
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Pobiera parametr kontekstu"""
        return self.parameters.get(key, default)
