"""
Moduł definiujący klasy konfiguracyjne dla RemoteConfigManager.
"""

from typing import List

from pydantic import BaseModel


class ServerConfig(BaseModel):
    """
    Klasa przechowująca konfigurację serwera.
    """

    host: str
    username: str
    password: str
    sudo_password: str
    app_dir: str
    services: List[str]


class AppConfig(BaseModel):
    """
    Klasa przechowująca konfigurację aplikacji.
    """

    name: str
    server: ServerConfig
