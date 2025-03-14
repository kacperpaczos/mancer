from typing import List, Any, Optional, Dict
from ..base_command import BaseCommand
from ...backend.bash_backend import BashBackend
from ....domain.model.command_result import CommandResult
from ....domain.model.command_context import CommandContext

class HeadCommand(BaseCommand):
    """Komenda head - wyświetla początkowe linie pliku"""
    
    def __init__(self):
        super().__init__("head")
    
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę head"""
        # Jeśli mamy dane wejściowe, używamy ich jako standardowego wejścia
        stdin_data = None
        if input_result and input_result.raw_output:
            stdin_data = input_result.raw_output
        
        # Budujemy komendę
        cmd_str = self.build_command()
        
        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)
        
        # Wykonujemy komendę
        result = backend.execute_command(
            cmd_str, 
            working_dir=context.current_directory,
            stdin_data=stdin_data
        )
        
        # Parsujemy wynik
        if result.success:
            result.structured_output = self._parse_output(result.raw_output)
        
        return result
    
    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parsuje wynik head do listy słowników z liniami pliku"""
        result = []
        lines = raw_output.split('\n')
        
        # Sprawdzamy, czy wynik zawiera nagłówki plików (gdy używamy wielu plików)
        has_headers = False
        for line in lines:
            if line.startswith("==> ") and line.endswith(" <=="):
                has_headers = True
                break
        
        if has_headers:
            # Parsowanie wyniku z wieloma plikami
            current_file = None
            line_number = 0
            
            for line in lines:
                if line.startswith("==> ") and line.endswith(" <=="):
                    # Znaleziono nagłówek pliku
                    current_file = line[4:-4]  # Wyodrębniamy nazwę pliku
                    line_number = 0
                else:
                    line_number += 1
                    result.append({
                        'file': current_file,
                        'line_number': line_number,
                        'content': line
                    })
        else:
            # Parsowanie wyniku z jednym plikiem
            for i, line in enumerate(lines):
                result.append({
                    'line_number': i + 1,
                    'content': line
                })
        
        return result
    
    # Metody specyficzne dla head
    
    def file(self, file_path: str) -> 'HeadCommand':
        """Ustawia plik do wyświetlenia"""
        return self.add_arg(file_path)
    
    def files(self, file_paths: List[str]) -> 'HeadCommand':
        """Ustawia wiele plików do wyświetlenia"""
        return self.add_args(file_paths)
    
    def lines(self, num_lines: int) -> 'HeadCommand':
        """Opcja -n - określa liczbę linii do wyświetlenia"""
        return self.with_param("n", str(num_lines))
    
    def bytes(self, num_bytes: int) -> 'HeadCommand':
        """Opcja -c - określa liczbę bajtów do wyświetlenia"""
        return self.with_param("c", str(num_bytes))
    
    def quiet(self) -> 'HeadCommand':
        """Opcja -q - nie wyświetla nagłówków plików"""
        return self.with_option("-q")
    
    def verbose(self) -> 'HeadCommand':
        """Opcja -v - zawsze wyświetla nagłówki plików"""
        return self.with_option("-v") 