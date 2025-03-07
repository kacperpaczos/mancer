"""Wrapper na komendę find."""
import subprocess
from typing import Dict, List, Optional, Any

from mancer.core.interfaces.command import CommandBuilder


class Find(CommandBuilder['Find']):
    """Wrapper na komendę find."""

    def __init__(self) -> None:
        """Inicjalizacja komendy find."""
        self.path: str = "."
        self.name: Optional[str] = None
        self.type: Optional[str] = None
        self.max_depth: Optional[int] = None
        self.min_size: Optional[str] = None
        self.max_size: Optional[str] = None
        
    def in_path(self, path: str) -> 'Find':
        """Ustaw ścieżkę do przeszukania.
        
        Args:
            path: Ścieżka do przeszukania
        """
        self.path = path
        return self
        
    def by_name(self, pattern: str) -> 'Find':
        """Szukaj po nazwie.
        
        Args:
            pattern: Wzorzec nazwy pliku
        """
        self.name = pattern
        return self
        
    def of_type(self, type_: str) -> 'Find':
        """Szukaj plików określonego typu.
        
        Args:
            type_: Typ pliku (f - zwykły plik, d - katalog)
        """
        self.type = type_
        return self
        
    def max_depth(self, depth: int) -> 'Find':
        """Ustaw maksymalną głębokość przeszukiwania.
        
        Args:
            depth: Maksymalna głębokość
        """
        self.max_depth = depth
        return self
        
    def size_range(self, min_size: Optional[str] = None, max_size: Optional[str] = None) -> 'Find':
        """Ustaw zakres rozmiaru plików.
        
        Args:
            min_size: Minimalny rozmiar (np. "1M", "500k")
            max_size: Maksymalny rozmiar (np. "10M", "1G")
        """
        self.min_size = min_size
        self.max_size = max_size
        return self

    def build_command(self) -> List[str]:
        """Zbuduj komendę find."""
        cmd = ["find", self.path]
        
        if self.name:
            cmd.extend(["-name", self.name])
            
        if self.type:
            cmd.extend(["-type", self.type])
            
        if self.max_depth is not None:
            cmd.extend(["-maxdepth", str(self.max_depth)])
            
        if self.min_size:
            cmd.extend(["-size", f"+{self.min_size}"])
            
        if self.max_size:
            cmd.extend(["-size", f"-{self.max_size}"])
            
        return cmd

    def validate(self) -> Dict[str, str]:
        """Sprawdź poprawność parametrów."""
        errors = {}
        
        if self.type and self.type not in ['f', 'd', 'l', 'b', 'c', 'p', 's']:
            errors["type"] = f"Nieprawidłowy typ pliku: {self.type}"
            
        return errors

    def _execute(self) -> Any:
        """Wykonaj komendę find."""
        cmd = self.build_command()
        return subprocess.run(cmd, check=True, text=True, capture_output=True) 