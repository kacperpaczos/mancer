from typing import List, Any, Optional, Dict
from ..base_command import BaseCommand
from ...backend.bash_backend import BashBackend
from ....domain.model.command_result import CommandResult
from ....domain.model.command_context import CommandContext

class DfCommand(BaseCommand):
    """Komenda df - wyświetla informacje o systemie plików"""
    
    def __init__(self):
        super().__init__("df")
    
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę df"""
        # Budujemy komendę
        cmd_str = self.build_command()
        
        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)
        
        # Wykonujemy komendę
        result = backend.execute_command(
            cmd_str, 
            working_dir=context.current_directory
        )
        
        # Parsujemy wynik
        if result.success:
            result.structured_output = self._parse_output(result.raw_output)
        
        return result
    
    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parsuje wynik df do listy słowników z informacjami o systemie plików"""
        result = []
        lines = raw_output.strip().split('\n')
        
        if len(lines) < 2:  # Musi być co najmniej nagłówek i jeden system plików
            return result
        
        # Parsujemy nagłówek, aby znaleźć pozycje kolumn
        header = lines[0]
        # Znajdź indeksy początku każdej kolumny
        col_positions = []
        col_names = []
        in_space = True
        
        for i, char in enumerate(header):
            if char.isspace():
                in_space = True
            elif in_space:
                in_space = False
                col_positions.append(i)
                
                # Znajdź nazwę kolumny (od tej pozycji do następnej spacji)
                col_name = ""
                for j in range(i, len(header)):
                    if header[j].isspace():
                        break
                    col_name += header[j]
                col_names.append(col_name)
        
        # Parsujemy każdy wiersz danych
        for i in range(1, len(lines)):
            line = lines[i]
            if not line.strip():
                continue
                
            fs_info = {}
            
            # Dla każdej kolumny, wyodrębnij jej wartość
            for j in range(len(col_positions)):
                start = col_positions[j]
                end = col_positions[j+1] if j+1 < len(col_positions) else len(line)
                
                # Przytnij białe znaki
                value = line[start:end].strip()
                
                # Dodaj do informacji o systemie plików
                fs_info[col_names[j].lower()] = value
            
            result.append(fs_info)
        
        return result
    
    # Metody specyficzne dla df
    
    def human_readable(self) -> 'DfCommand':
        """Opcja -h - pokazuje rozmiary w formacie czytelnym dla człowieka"""
        return self.with_option("-h")
    
    def inodes(self) -> 'DfCommand':
        """Opcja -i - pokazuje informacje o i-węzłach zamiast o blokach"""
        return self.with_option("-i")
    
    def type(self, fs_type: str) -> 'DfCommand':
        """Opcja -t - pokazuje tylko systemy plików określonego typu"""
        return self.with_param("t", fs_type)
    
    def exclude_type(self, fs_type: str) -> 'DfCommand':
        """Opcja -x - wyklucza systemy plików określonego typu"""
        return self.with_param("x", fs_type)
    
    def filesystem(self, filesystem: str) -> 'DfCommand':
        """Określa konkretny system plików do wyświetlenia"""
        return self.add_arg(filesystem) 