import importlib.metadata as metadata
from dataclasses import dataclass
from typing import Optional
import logging
import pkg_resources
import sys

logger = logging.getLogger(__name__)

@dataclass
class VersionInfo:
    """
    Klasa przechowująca informacje o wersji pakietu Mancer.
    Pozwala na dostęp do informacji o zainstalowanej wersji pakietu.
    """
    name: str
    version: str
    summary: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    
    @classmethod
    def get_mancer_version(cls) -> 'VersionInfo':
        """
        Pobiera informacje o wersji zainstalowanego pakietu Mancer.
        
        Returns:
            Obiekt VersionInfo z informacjami o wersji
        """
        try:
            # Próba pobrania informacji o pakiecie za pomocą importlib.metadata (Python 3.8+)
            pkg_info = metadata.metadata('mancer')
            return cls(
                name='mancer',
                version=metadata.version('mancer'),
                summary=pkg_info.get('Summary'),
                author=pkg_info.get('Author'),
                author_email=pkg_info.get('Author-email')
            )
        except (metadata.PackageNotFoundError, ImportError):
            try:
                # Alternatywna metoda z pkg_resources
                pkg_info = pkg_resources.get_distribution('mancer')
                return cls(
                    name='mancer',
                    version=pkg_info.version,
                    summary=pkg_info.project_name,
                    author=None,
                    author_email=None
                )
            except pkg_resources.DistributionNotFound:
                logger.warning("Pakiet Mancer nie jest zainstalowany przez pip")
                return cls(
                    name='mancer',
                    version='dev',
                    summary='Framework DDD dla komend systemowych (wersja deweloperska)',
                    author=None, 
                    author_email=None
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
        return self.version == 'dev' or self.version.endswith('.dev0') 