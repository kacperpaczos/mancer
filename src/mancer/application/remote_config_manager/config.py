"""
Moduł definiujący klasy konfiguracyjne dla RemoteConfigManager.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ServerConfig:
    """
    Klasa przechowująca konfigurację serwera.
    """

    host: str
    username: str
    password: str
    sudo_password: str
    app_dir: str
    services: List[str]


@dataclass
class AppConfig:
    """
    Klasa przechowująca konfigurację aplikacji.
    """

    name: str
    server: ServerConfig
