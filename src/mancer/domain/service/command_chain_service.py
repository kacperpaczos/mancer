from typing import List, Optional, Any
from ..model.command_result import CommandResult
from ..model.command_context import CommandContext
from ..interface.command_interface import CommandInterface

class CommandChain:
    """Klasa reprezentująca łańcuch komend"""
    
    def __init__(self, first_command: CommandInterface):
        self.commands = [first_command]
        self.is_pipeline = [False]  # Pierwszy element jest zawsze False
    
    def then(self, next_command: CommandInterface) -> 'CommandChain':
        """Dodaje kolejną komendę do łańcucha (sekwencyjnie)"""
        self.commands.append(next_command)
        self.is_pipeline.append(False)
        return self
    
    def pipe(self, next_command: CommandInterface) -> 'CommandChain':
        """Dodaje komendę jako potok (stdout -> stdin)"""
        self.commands.append(next_command)
        self.is_pipeline.append(True)
        return self
    
    def execute(self, context: CommandContext) -> CommandResult:
        """Wykonuje cały łańcuch komend"""
        if not self.commands:
            raise ValueError("Łańcuch komend jest pusty")
        
        result = None
        current_context = context
        
        for i, command in enumerate(self.commands):
            # Pierwszy element nie ma poprzedniego wyniku
            if i == 0:
                result = command.execute(current_context)
            else:
                # Jeśli potok, przekazujemy wynik jako wejście
                if self.is_pipeline[i]:
                    result = command.execute(current_context, result)
                else:
                    # Jeśli sekwencja, używamy bieżącego kontekstu
                    result = command.execute(current_context)
            
            # Aktualizujemy kontekst po każdej komendzie
            if result and result.is_success():
                current_context.add_to_history(command.build_command())
                
                # Zakładamy, że cd aktualizuje current_directory w kontekście
                if command.__class__.__name__ == "CdCommand" and result.is_success():
                    # Nie trzeba robić nic więcej, bo komenda cd sama aktualizuje kontekst
                    pass
        
        return result
