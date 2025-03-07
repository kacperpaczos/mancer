"""Wrapper na komendę grep."""
import subprocess
from typing import Dict, List, Optional, Any

from mancer.core.interfaces.command import CommandBuilder


class Grep(CommandBuilder['Grep']):
    """Wrapper na komendę grep."""

    def __init__(self) -> None:
        """Inicjalizacja komendy grep."""
        self.pattern: Optional[str] = None
        self.file: Optional[str] = None
        self.recursive: bool = False
        self.ignore_case: bool = False
        self.line_number: bool = False
        
    def search(self, pattern: str) -> 'Grep':
        """Ustaw wzorzec do wyszukiwania.
        
        Args:
            pattern: Wzorzec do wyszukania
        """
        self.pattern = pattern
        return self
        
    def in_file(self, file: str) -> 'Grep':
        """Ustaw plik do przeszukania.
        
        Args:
            file: Ścieżka do pliku
        """
        self.file = file
        return self
        
    def recursively(self) -> 'Grep':
        """Przeszukuj rekurencyjnie."""
        self.recursive = True
        return self
        
    def case_insensitive(self) -> 'Grep':
        """Ignoruj wielkość liter."""
        self.ignore_case = True
        return self
        
    def with_line_numbers(self) -> 'Grep':
        """Pokaż numery linii."""
        self.line_number = True
        return self

    def build_command(self) -> List[str]:
        """Zbuduj komendę grep."""
        cmd = ["grep"]
        
        if self.recursive:
            cmd.append("-r")
            
        if self.ignore_case:
            cmd.append("-i")
            
        if self.line_number:
            cmd.append("-n")
            
        if self.pattern:
            cmd.append(self.pattern)
            
        if self.file:
            cmd.append(self.file)
            
        return cmd

    def validate(self) -> Dict[str, str]:
        """Sprawdź poprawność parametrów."""
        errors = {}
        
        if not self.pattern:
            errors["pattern"] = "Wzorzec jest wymagany"
            
        return errors

    def _execute(self) -> Any:
        """Wykonaj komendę grep."""
        cmd = self.build_command()
        return subprocess.run(cmd, check=True, text=True, capture_output=True) 