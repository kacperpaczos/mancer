"""Wrapper na komendę sed."""
import subprocess
from typing import Dict, List, Optional, Any

from mancer.core.interfaces.command import CommandBuilder


class Sed(CommandBuilder['Sed']):
    """Wrapper na komendę sed."""

    def __init__(self) -> None:
        """Inicjalizacja komendy sed."""
        self.pattern: Optional[str] = None
        self.file: Optional[str] = None
        self.in_place: bool = False
        self.backup: Optional[str] = None
        self.global_replace: bool = False
        
    def replace(self, pattern: str) -> 'Sed':
        """Ustaw wzorzec zamiany.
        
        Args:
            pattern: Wzorzec zamiany (np. "s/stary/nowy/")
        """
        self.pattern = pattern
        return self
        
    def in_file(self, file: str) -> 'Sed':
        """Ustaw plik do edycji.
        
        Args:
            file: Ścieżka do pliku
        """
        self.file = file
        return self
        
    def edit_in_place(self, backup: Optional[str] = None) -> 'Sed':
        """Edytuj plik w miejscu.
        
        Args:
            backup: Rozszerzenie pliku kopii zapasowej
        """
        self.in_place = True
        self.backup = backup
        return self
        
    def globally(self) -> 'Sed':
        """Zamień wszystkie wystąpienia w linii."""
        self.global_replace = True
        return self

    def build_command(self) -> List[str]:
        """Zbuduj komendę sed."""
        cmd = ["sed"]
        
        if self.in_place:
            if self.backup:
                cmd.append(f"-i{self.backup}")
            else:
                cmd.append("-i")
                
        if self.pattern:
            if self.global_replace and not self.pattern.endswith('g'):
                cmd.append(self.pattern + 'g')
            else:
                cmd.append(self.pattern)
                
        if self.file:
            cmd.append(self.file)
            
        return cmd

    def validate(self) -> Dict[str, str]:
        """Sprawdź poprawność parametrów."""
        errors = {}
        
        if not self.pattern:
            errors["pattern"] = "Wzorzec jest wymagany"
            
        if not self.file:
            errors["file"] = "Plik jest wymagany"
            
        return errors

    def _execute(self) -> Any:
        """Wykonaj komendę sed."""
        cmd = self.build_command()
        return subprocess.run(cmd, check=True, text=True, capture_output=True) 