"""Abstrakcja dostępu do zawartości plików (lokalnych lub zdalnych).

Umożliwia warstwie domain użycie dostawcy bez zależności od infrastructure.
"""

from typing import Optional, Protocol


class FileContentProvider(Protocol):
    """Protokół dostępu do zawartości pliku (odczyt, zapis, backup). Implementacje w infrastructure."""

    def get_content(self, path: str) -> str:
        """Pobiera zawartość pliku."""
        ...

    def set_content(self, path: str, content: str) -> bool:
        """Zapisuje zawartość do pliku. Zwraca True jeśli sukces."""
        ...

    def backup_file(self, path: str, suffix: Optional[str] = None) -> Optional[str]:
        """Tworzy kopię zapasową pliku. Zwraca ścieżkę do backupu lub None."""
        ...
