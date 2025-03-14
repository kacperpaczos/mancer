from typing import List, Any, Optional, Dict
from ..base_command import BaseCommand
from ...backend.bash_backend import BashBackend
from ....domain.model.command_result import CommandResult
from ....domain.model.command_context import CommandContext

class EchoCommand(BaseCommand):
    """Komenda echo - wyświetla tekst"""
    
    def __init__(self):
        super().__init__("echo")
    
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę echo"""
        # Budujemy komendę
        cmd_str = self.build_command()
        
        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)
        
        # Wykonujemy komendę
        result = backend.execute_command(
            cmd_str, 
            working_dir=context.current_directory
        )
        
        # Parsujemy wynik - dla echo jest to po prostu tekst
        if result.success:
            result.structured_output = [{'text': result.raw_output.strip()}]
        
        return result
    
    # Metody specyficzne dla echo
    
    def text(self, message: str) -> 'EchoCommand':
        """Ustawia tekst do wyświetlenia"""
        return self.add_arg(message)
    
    def no_newline(self) -> 'EchoCommand':
        """Opcja -n - nie dodaje znaku nowej linii na końcu"""
        return self.with_option("-n")
    
    def enable_backslash_escapes(self) -> 'EchoCommand':
        """Opcja -e - włącza interpretację sekwencji escape z backslashem"""
        return self.with_option("-e")
    
    def disable_backslash_escapes(self) -> 'EchoCommand':
        """Opcja -E - wyłącza interpretację sekwencji escape z backslashem"""
        return self.with_option("-E")
    
    def to_file(self, file_path: str, append: bool = False) -> 'EchoCommand':
        """
        Przekierowuje wyjście do pliku
        
        Args:
            file_path: Ścieżka do pliku
            append: Czy dopisać do pliku (True) czy nadpisać (False)
        """
        new_instance = self.clone()
        # Dodajemy przekierowanie do pliku
        if append:
            new_instance.pipeline = f">> {file_path}"
        else:
            new_instance.pipeline = f"> {file_path}"
        return new_instance
        
    def clone(self) -> 'EchoCommand':
        """Tworzy kopię komendy z tą samą konfiguracją"""
        new_instance = super().clone()
        return new_instance 