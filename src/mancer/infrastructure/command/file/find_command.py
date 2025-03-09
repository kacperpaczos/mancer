from typing import List, Any, Optional, Dict
from ..base_command import BaseCommand
from ...backend.bash_backend import BashBackend
from ....domain.model.command_result import CommandResult
from ....domain.model.command_context import CommandContext

class FindCommand(BaseCommand):
    """Komenda find - wyszukuje pliki i katalogi"""
    
    def __init__(self):
        super().__init__("find")
        self.backend = BashBackend()
    
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę find"""
        # Budujemy komendę z uwzględnieniem kontekstu
        cmd_str = self.build_command()
        
        # Jeśli nie ma ścieżki w parametrach, używamy bieżącego katalogu z kontekstu
        if "path" not in self.parameters:
            cmd_str = f"{cmd_str} {context.current_directory}"
        
        # Wykonujemy komendę
        result = self.backend.execute_command(
            cmd_str, 
            working_dir=context.current_directory
        )
        
        # Parsujemy wynik
        if result.success:
            result.structured_output = self._parse_output(result.raw_output)
        
        return result
    
    def _format_parameter(self, name: str, value: Any) -> str:
        """Specjalne formatowanie dla find"""
        if name == "path":
            return ""  # Ścieżka jest obsługiwana przez _get_additional_args
        elif name == "name":
            return f"-name \"{value}\""
        elif name == "type":
            return f"-type {value}"
        elif name == "size":
            return f"-size {value}"
        elif name == "mtime":
            return f"-mtime {value}"
        return super()._format_parameter(name, value)
    
    def _get_additional_args(self) -> List[str]:
        """Dodaje ścieżkę wyszukiwania, jeśli jest ustawiona"""
        if "path" in self.parameters:
            return [str(self.parameters["path"])]
        return []
    
    def _parse_output(self, raw_output: str) -> List[str]:
        """Parsuje wynik find do listy ścieżek"""
        if not raw_output.strip():
            return []
        
        # Wynik find to po prostu lista plików oddzielona nową linią
        return raw_output.strip().split('\n')
    
    # Metody specyficzne dla find
    
    def in_path(self, path: str) -> 'FindCommand':
        """Ustawia ścieżkę bazową do wyszukiwania"""
        return self.with_param("path", path)
    
    def with_name(self, pattern: str) -> 'FindCommand':
        """Wyszukuje pliki o podanej nazwie (może zawierać wzorce)"""
        return self.with_param("name", pattern)
    
    def with_type(self, type_char: str) -> 'FindCommand':
        """Wyszukuje pliki określonego typu (f - pliki, d - katalogi)"""
        return self.with_param("type", type_char)
    
    def with_size(self, size_expr: str) -> 'FindCommand':
        """Wyszukuje pliki określonego rozmiaru (np. +10M, -1G)"""
        return self.with_param("size", size_expr)
    
    def modified_days_ago(self, days: int) -> 'FindCommand':
        """Wyszukuje pliki zmodyfikowane określoną liczbę dni temu"""
        return self.with_param("mtime", str(days))
    
    def exec_command(self, command: str) -> 'FindCommand':
        """Dodaje opcję wykonania komendy dla każdego znalezionego pliku"""
        return self.with_param("exec", f"{command} {{}} \\;")
    
    def with_param(self, name: str, value: Any) -> 'FindCommand':
        """Nadpisana metoda with_param dla lepszej obsługi łańcuchów"""
        return super().with_param(name, value)
