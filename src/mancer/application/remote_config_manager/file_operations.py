"""
Moduł implementujący operacje na plikach i struktury danych związane z plikami.
"""

import difflib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class FileInfo:
    """
    Klasa przechowująca informacje o pliku konfiguracyjnym.
    """

    path: str
    rel_path: str
    content: str
    type: str
    size: int
    modified: str


@dataclass
class FileDiff:
    """
    Klasa przechowująca informacje o różnicach między plikami.
    """

    server_path: str
    cache_path: str
    rel_path: str
    differences: List[str]


class FileManager:
    """
    Klasa implementująca operacje na plikach konfiguracyjnych.
    """

    def get_file_content(self, path: Path) -> Optional[str]:
        """
        Odczytuje zawartość pliku.

        Args:
            path: Ścieżka do pliku

        Returns:
            Zawartość pliku lub None w przypadku błędu
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def save_file_content(self, path: Path, content: str) -> bool:
        """
        Zapisuje zawartość do pliku.

        Args:
            path: Ścieżka do pliku
            content: Zawartość do zapisania

        Returns:
            True jeśli zapis się powiódł, False w przeciwnym razie
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def get_file_info(self, path: Path, base_dir: Optional[Path] = None) -> Optional[FileInfo]:
        """
        Pobiera informacje o pliku.

        Args:
            path: Ścieżka do pliku
            base_dir: Opcjonalny katalog bazowy dla ścieżki względnej

        Returns:
            Obiekt FileInfo z informacjami o pliku lub None w przypadku błędu
        """
        try:
            content = self.get_file_content(path)
            if content is None:
                return None

            stat = path.stat()
            file_type = path.suffix.lstrip(".")

            if file_type == "":
                # Sprawdź nazwę pliku
                if path.name == "config.js":
                    file_type = "js"
                else:
                    file_type = "unknown"

            rel_path = str(path.relative_to(base_dir)) if base_dir else str(path)

            return FileInfo(
                path=str(path),
                rel_path=rel_path,
                content=content,
                type=file_type,
                size=stat.st_size,
                modified=str(stat.st_mtime),
            )
        except Exception:
            return None

    def compare_files(self, file1_path: Path, file2_path: Path) -> Tuple[bool, List[str]]:
        """
        Porównuje zawartość dwóch plików.

        Args:
            file1_path: Ścieżka do pierwszego pliku
            file2_path: Ścieżka do drugiego pliku

        Returns:
            Krotka (czy_różne, lista_różnic)
        """
        file1_content = self.get_file_content(file1_path)
        file2_content = self.get_file_content(file2_path)

        if file1_content is None or file2_content is None:
            return True, ["Błąd odczytu jednego z plików"]

        if file1_content == file2_content:
            return False, []

        # Porównaj linie
        lines1 = file1_content.splitlines()
        lines2 = file2_content.splitlines()

        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))

        # Filtruj linie z różnicami
        interesting_diff = [
            line
            for line in diff
            if line.startswith("+ ") or line.startswith("- ") or line.startswith("? ")
        ]

        return True, interesting_diff

    def format_json(self, content: str) -> str:
        """
        Formatuje zawartość JSON.

        Args:
            content: Zawartość JSON

        Returns:
            Sformatowana zawartość JSON
        """
        try:
            # Spróbuj zparsować jako JSON
            data = json.loads(content)
            return json.dumps(data, indent=4)
        except json.JSONDecodeError:
            # Jeśli nie jest poprawnym JSON, zwróć oryginalną zawartość
            return content

    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """
        Listuje pliki w katalogu pasujące do wzorca.

        Args:
            directory: Katalog do przeszukania
            pattern: Wzorzec nazw plików

        Returns:
            Lista ścieżek do plików
        """
        if not directory.exists():
            return []

        return list(directory.glob(pattern))
