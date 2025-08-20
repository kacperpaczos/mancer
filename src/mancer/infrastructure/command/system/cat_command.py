from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class CatCommand(BaseCommand):
    """Implementacja komendy 'cat' do wyświetlania zawartości plików"""
    
    # Zdefiniuj nazwę narzędzia
    tool_name = "cat"
    
    def __init__(self, file_path=None):
        super().__init__("cat")
        
        if file_path:
            self._args.append(file_path)
    
    def execute(self, context: CommandContext, 
                input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę cat"""
        # Wywołaj metodę bazową aby sprawdzić wersję narzędzia
        super().execute(context, input_result)
        
        # Zbuduj string komendy
        command_str = self.build_command()
        
        # Pobierz odpowiedni backend
        backend = self._get_backend(context)
        
        # Wykonaj komendę
        exit_code, output, error = backend.execute(command_str)
        
        # Sprawdź czy komenda się powiodła
        success = exit_code == 0
        error_message = error if error and not success else None
        
        # Dodaj ostrzeżenia o wersji do metadanych
        metadata = {}
        warnings = context.get_parameter("warnings", [])
        if warnings:
            metadata["version_warnings"] = warnings
        
        # Utwórz i zwróć wynik
        return self._prepare_result(
            raw_output=output,
            success=success,
            exit_code=exit_code,
            error_message=error_message,
            metadata=metadata
        )
    
    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parsuje wyjście komendy cat do formatu strukturalnego"""
        lines = raw_output.strip().split('\n')
        results = []
        
        for i, line in enumerate(lines):
            results.append({
                'line_number': i + 1,
                'text': line
            })
        
        return results 