import os
from typing import List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class CdCommand(BaseCommand):
    """Komenda cd - zmienia aktualny katalog"""
    
    def __init__(self):
        super().__init__("cd")
    
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę cd - zmienia katalog w kontekście"""
        # Pobieramy ścieżkę docelową
        target_path = None
        
        # Jeśli otrzymaliśmy wynik z poprzedniej komendy
        if input_result and input_result.is_success() and "directory" not in self.parameters:
            # Próbujemy znaleźć katalog w structured_output
            if input_result.structured_output:
                if isinstance(input_result.structured_output[0], dict) and "name" in input_result.structured_output[0]:
                    # Jeśli mamy listę słowników (np. z ls), bierzemy pierwszy element
                    target_path = input_result.structured_output[0]["name"]
                elif isinstance(input_result.structured_output[0], str):
                    # Jeśli mamy listę stringów, bierzemy pierwszy
                    target_path = input_result.structured_output[0]
        
        # Jeśli nie znaleźliśmy ścieżki w wyniku, sprawdzamy parametry
        if target_path is None:
            target_path = self.parameters.get("directory", ".")
        
        # Budujemy pełną ścieżkę względem bieżącego katalogu
        if not os.path.isabs(target_path):
            full_path = os.path.normpath(os.path.join(context.current_directory, target_path))
        else:
            full_path = target_path
        
        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)
        
        # W przypadku zdalnego wykonania, musimy sprawdzić, czy katalog istnieje
        if context.is_remote():
            # Wykonujemy komendę "test -d <path>" na zdalnym hoście
            test_cmd = f"test -d {full_path} && echo 'exists' || echo 'not_exists'"
            test_result = backend.execute_command(test_cmd)
            
            if "not_exists" in test_result.raw_output:
                return CommandResult(
                    raw_output="",
                    success=False,
                    structured_output=[],
                    exit_code=1,
                    error_message=f"cd: {target_path}: Nie ma takiego pliku ani katalogu"
                )
        else:
            # Lokalnie sprawdzamy, czy katalog istnieje
            if not os.path.isdir(full_path):
                return CommandResult(
                    raw_output="",
                    success=False,
                    structured_output=[],
                    exit_code=1,
                    error_message=f"cd: {target_path}: Nie ma takiego pliku ani katalogu"
                )
        
        # Aktualizujemy kontekst
        context.change_directory(full_path)
        
        # Zwracamy sukces
        return CommandResult(
            raw_output="",
            success=True,
            structured_output=[full_path],
            exit_code=0
        )
    
    def _get_additional_args(self) -> List[str]:
        """Dodaje ścieżkę docelową, jeśli jest ustawiona"""
        if "directory" in self.parameters:
            return [self.parameters["directory"]]
        return []
    
    def to_directory(self, directory: str) -> 'CdCommand':
        """Ustawia katalog docelowy"""
        return self.with_param("directory", directory)
