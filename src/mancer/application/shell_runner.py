from typing import Dict, Any, Optional
from ..domain.model.command_context import CommandContext
from ..domain.model.command_result import CommandResult
from ..domain.interface.command_interface import CommandInterface
from ..domain.service.command_chain_service import CommandChain
from ..infrastructure.factory.command_factory import CommandFactory

class ShellRunner:
    """Główna klasa aplikacji do uruchamiania komend"""
    
    def __init__(self, backend_type: str = "bash", working_dir: str = "."):
        self.backend_type = backend_type
        self.factory = CommandFactory(backend_type)
        self.context = CommandContext(current_directory=working_dir)
    
    def create_command(self, command_name: str) -> CommandInterface:
        """Tworzy nową instancję komendy"""
        return self.factory.create_command(command_name)
    
    def execute(self, command: CommandInterface, 
               context_params: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Wykonuje pojedynczą komendę lub łańcuch komend"""
        # Kopiujemy kontekst, aby nie modyfikować globalnego
        context = self._prepare_context(context_params)
        
        # Sprawdzamy, czy to łańcuch czy pojedyncza komenda
        if isinstance(command, CommandChain):
            return command.execute(context)
        else:
            return command.execute(context)
    
    def register_command(self, alias: str, command: CommandInterface) -> None:
        """Rejestruje prekonfigurowaną komendę pod aliasem"""
        self.factory.register_command(alias, command)
    
    def get_command(self, alias: str) -> CommandInterface:
        """Pobiera prekonfigurowaną komendę według aliasu"""
        return self.factory.get_command(alias)
    
    def _prepare_context(self, context_params: Optional[Dict[str, Any]] = None) -> CommandContext:
        """Przygotowuje kontekst wykonania komendy"""
        # Tworzymy kopię głównego kontekstu
        context = CommandContext(
            current_directory=self.context.current_directory,
            environment_variables=self.context.environment_variables.copy()
        )
        
        # Dodajemy parametry kontekstu, jeśli są
        if context_params:
            for key, value in context_params.items():
                context.set_parameter(key, value)
                
        return context
