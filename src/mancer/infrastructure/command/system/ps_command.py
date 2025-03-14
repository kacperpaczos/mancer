from typing import List, Any, Optional, Dict
from ..base_command import BaseCommand
from ...backend.bash_backend import BashBackend
from ....domain.model.command_result import CommandResult
from ....domain.model.command_context import CommandContext

class PsCommand(BaseCommand):
    """Komenda ps - wyświetla informacje o procesach"""
    
    def __init__(self):
        super().__init__("ps")
    
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę ps"""
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
        """Parsuje wynik ps do listy słowników z informacjami o procesach"""
        result = []
        lines = raw_output.strip().split('\n')
        
        if len(lines) < 2:  # Musi być co najmniej nagłówek i jeden proces
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
                
            process_info = {}
            
            # Dla każdej kolumny, wyodrębnij jej wartość
            for j in range(len(col_positions)):
                start = col_positions[j]
                end = col_positions[j+1] if j+1 < len(col_positions) else len(line)
                
                # Przytnij białe znaki
                value = line[start:end].strip()
                
                # Dodaj do informacji o procesie
                process_info[col_names[j].lower()] = value
            
            result.append(process_info)
        
        return result
    
    # Metody specyficzne dla ps
    
    def all(self) -> 'PsCommand':
        """Opcja -e - pokazuje wszystkie procesy"""
        return self.with_option("-e")
    
    def full_format(self) -> 'PsCommand':
        """Opcja -f - pełny format wyświetlania"""
        return self.with_option("-f")
    
    def long_format(self) -> 'PsCommand':
        """Opcja -l - długi format wyświetlania"""
        return self.with_option("-l")
    
    def user(self, username: str) -> 'PsCommand':
        """Opcja -u - pokazuje procesy określonego użytkownika"""
        return self.with_param("u", username)
    
    def search(self, pattern: str) -> 'PsCommand':
        """Wyszukuje procesy według wzorca, wykorzystując grep"""
        new_instance = self.clone()
        # Dodanie opcji do komendy ps, która przekazuje wynik do grep
        new_instance.pipeline = f"grep {pattern}"
        return new_instance
        
    def aux(self) -> 'PsCommand':
        """Opcja aux - pokazuje wszystkie procesy dla wszystkich użytkowników z dodatkowymi informacjami"""
        return self.with_option("aux")