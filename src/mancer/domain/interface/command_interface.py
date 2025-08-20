from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from ..service.command_chain_service import CommandChain

from ..model.command_context import CommandContext
from ..model.command_result import CommandResult

T = TypeVar('T', bound='CommandInterface')

class CommandInterface(ABC, Generic[T]):
    """Interfejs dla wszystkich komend"""
    
    @abstractmethod
    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę w danym kontekście z opcjonalnym wejściem"""
        pass
    
    @abstractmethod
    def build_command(self) -> str:
        """Buduje string komendy na podstawie konfiguracji"""
        pass
    
    @abstractmethod
    def clone(self) -> T:
        """Tworzy kopię komendy z tą samą konfiguracją"""
        pass
    
    @abstractmethod
    def with_option(self, option: str) -> T:
        """Dodaje opcję do komendy"""
        pass
    
    @abstractmethod
    def with_param(self, name: str, value: Any) -> T:
        """Ustawia parametr komendy"""
        pass
    
    def then(self, next_command: 'CommandInterface') -> 'CommandChain':
        """Tworzy łańcuch komend z bieżącą i następną komendą"""
        from ..service.command_chain_service import CommandChain
        return CommandChain(self).then(next_command)
    
    def pipe(self, next_command: 'CommandInterface') -> 'CommandChain':
        """Tworzy potok pomiędzy bieżącą i następną komendą"""
        from ..service.command_chain_service import CommandChain
        return CommandChain(self).pipe(next_command)
