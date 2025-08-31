import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ToolVersion:
    """Reprezentuje informacje o wersji narzędzia systemowego (komendy bash)"""

    name: str  # Nazwa narzędzia (np. 'ls', 'grep')
    version: str  # Wersja narzędzia (np. '8.30', '3.4')
    raw_version_output: str  # Pełny tekst wyjścia komendy z opcją --version

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"

    @classmethod
    def parse_version_output(cls, name: str, version_output: str) -> "ToolVersion":
        """
        Parsuje wyjście komendy bash z opcją --version i tworzy obiekt ToolVersion

        Args:
            name: Nazwa narzędzia
            version_output: Wyjście komendy z opcją --version

        Returns:
            Obiekt ToolVersion
        """
        # Uniwersalny wzorzec do wyszukiwania wersji w typowych formatach
        # Obsługuje wzorce jak "tool (GNU coreutils) 8.30", "tool version 1.2.3", itp.
        patterns = [
            r"(\d+\.\d+\.\d+)",  # Wersja w formacie X.Y.Z
            r"(\d+\.\d+)",  # Wersja w formacie X.Y
            r"version\s+(\d+\.\d+[\.\d]*)",  # "version X.Y[.Z]"
            r"\d+\s+(\d+\.\d+[\.\d]*)",  # "TOOL X.Y[.Z]"
            r"v(\d+\.\d+[\.\d]*)",  # vX.Y[.Z]
        ]

        version = "nieznana"
        for pattern in patterns:
            match = re.search(pattern, version_output)
            if match:
                version = match.group(1)
                break

        return cls(name=name, version=version, raw_version_output=version_output)


@dataclass
class ToolVersionRegistry:
    """Rejestr wersji narzędzi systemowych"""

    # Słownik mapujący nazwę narzędzia na dozwolone wersje
    allowed_versions: Dict[str, Set[str]] = field(default_factory=dict)

    # Bufor wykrytych wersji narzędzi
    detected_versions: Dict[str, ToolVersion] = field(default_factory=dict)

    def register_allowed_version(self, tool_name: str, version: str) -> None:
        """
        Rejestruje dozwoloną wersję narzędzia

        Args:
            tool_name: Nazwa narzędzia
            version: Wersja narzędzia
        """
        if tool_name not in self.allowed_versions:
            self.allowed_versions[tool_name] = set()

        self.allowed_versions[tool_name].add(version)

    def register_allowed_versions(self, tool_name: str, versions: List[str]) -> None:
        """
        Rejestruje wiele dozwolonych wersji narzędzia

        Args:
            tool_name: Nazwa narzędzia
            versions: Lista dozwolonych wersji
        """
        if tool_name not in self.allowed_versions:
            self.allowed_versions[tool_name] = set()

        for version in versions:
            self.allowed_versions[tool_name].add(version)

    def is_version_allowed(self, tool_name: str, version: str) -> bool:
        """
        Sprawdza, czy wersja narzędzia jest dozwolona

        Args:
            tool_name: Nazwa narzędzia
            version: Wersja narzędzia

        Returns:
            True, jeśli wersja jest dozwolona, False w przeciwnym razie
        """
        # Jeśli narzędzie nie ma zarejestrowanych wersji, uznajemy każdą wersję za dozwoloną
        if (
            tool_name not in self.allowed_versions
            or not self.allowed_versions[tool_name]
        ):
            return True

        return version in self.allowed_versions[tool_name]

    def update_detected_version(self, tool_version: ToolVersion) -> None:
        """
        Aktualizuje informacje o wykrytej wersji narzędzia

        Args:
            tool_version: Obiekt ToolVersion z informacjami o wykrytej wersji
        """
        self.detected_versions[tool_version.name] = tool_version

    def get_detected_version(self, tool_name: str) -> Optional[ToolVersion]:
        """
        Pobiera informacje o wykrytej wersji narzędzia

        Args:
            tool_name: Nazwa narzędzia

        Returns:
            Obiekt ToolVersion z informacjami o wykrytej wersji lub None, jeśli wersja nie została wykryta
        """
        return self.detected_versions.get(tool_name)
