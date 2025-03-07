"""Wrapper na komendę ls."""
import subprocess
from typing import Dict, List, Optional, Any

from mancer.core.interfaces.command import CommandBuilder


class Ls(CommandBuilder['Ls']):
    """Wrapper na komendę ls."""

    def __init__(self) -> None:
        """Inicjalizacja komendy ls."""
        self.path: str = "."
        self.all: bool = False
        self.long: bool = False
        self.human: bool = False
        
    def in_path(self, path: str) -> 'Ls':
        """Ustaw ścieżkę do listowania.
        
        Args:
            path: Ścieżka do sprawdzenia
        """
        self.path = path
        return self
        
    def show_all(self) -> 'Ls':
        """Pokaż wszystkie pliki (włącznie z ukrytymi)."""
        self.all = True
        return self
        
    def long_format(self) -> 'Ls':
        """Użyj długiego formatu wyświetlania."""
        self.long = True
        return self
        
    def human_readable(self) -> 'Ls':
        """Pokaż rozmiary w czytelnym formacie."""
        self.human = True
        return self

    def build_command(self) -> List[str]:
        """Zbuduj komendę ls."""
        cmd = ["ls"]
        
        if self.all:
            cmd.append("-a")
            
        if self.long:
            cmd.append("-l")
            
        if self.human:
            cmd.append("-h")
            
        cmd.append(self.path)
        return cmd

    def validate(self) -> Dict[str, str]:
        """Sprawdź poprawność parametrów."""
        errors = {}
        return errors

    def _execute(self) -> Any:
        """Wykonaj komendę ls."""
        cmd = self.build_command()
        return subprocess.run(cmd, check=True, text=True, capture_output=True) 