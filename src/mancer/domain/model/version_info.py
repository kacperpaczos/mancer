import importlib.metadata as metadata
import logging
from dataclasses import dataclass
from typing import Optional

import pkg_resources

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """
    Holds version information for the installed Mancer package.

    Attributes:
        name: Package name.
        version: Package version string.
        summary: Optional short package summary from metadata.
        author: Optional package author.
        author_email: Optional package author email.
    """

    name: str
    version: str
    summary: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None

    @classmethod
    def get_mancer_version(cls) -> "VersionInfo":
        """
        Pobiera informacje o wersji zainstalowanego pakietu Mancer.

        Returns:
            Obiekt VersionInfo z informacjami o wersji
        """
        try:
            # Próba pobrania informacji o pakiecie za pomocą importlib.metadata (Python 3.8+)
            pkg_info = metadata.metadata("mancer")
            return cls(
                name="mancer",
                version=metadata.version("mancer"),
                summary=pkg_info.get("Summary"),
                author=pkg_info.get("Author"),
                author_email=pkg_info.get("Author-email"),
            )
        except (metadata.PackageNotFoundError, ImportError):
            try:
                # Alternatywna metoda z pkg_resources
                dist = pkg_resources.get_distribution("mancer")
                return cls(
                    name="mancer",
                    version=dist.version,
                    summary=str(dist.project_name),
                    author=None,
                    author_email=None,
                )
            except pkg_resources.DistributionNotFound:
                logger.warning("Pakiet Mancer nie jest zainstalowany przez pip")
                return cls(
                    name="mancer",
                    version="dev",
                    summary="Framework DDD dla komend systemowych (wersja deweloperska)",
                    author=None,
                    author_email=None,
                )

    def __str__(self) -> str:
        """
        Zwraca reprezentację tekstową wersji pakietu.

        Returns:
            String z informacją o wersji
        """
        return f"{self.name} v{self.version}"

    @property
    def is_dev_version(self) -> bool:
        """
        Sprawdza czy obecna wersja to wersja deweloperska.

        Returns:
            True jeśli wersja deweloperska, False w przeciwnym przypadku
        """
        return self.version == "dev" or self.version.endswith(".dev0")
