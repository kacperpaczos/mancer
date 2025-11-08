"""
Model profilu SSH - przechowuje konfigurację połączenia
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class SSHProfileDict(TypedDict, total=False):
    """TypedDict representation of SSH profile for serialization."""

    id: str
    name: str
    description: str
    hostname: str
    username: str
    port: int
    key_filename: Optional[str]
    proxy_config: Optional[Dict[str, Any]]
    ssh_options: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime]
    use_count: int
    tags: List[str]
    category: str
    save_password: bool
    password_hash: Optional[str]


class SSHProfile(BaseModel):
    """Profil połączenia SSH"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    hostname: str = ""
    username: str = ""
    port: int = 22
    key_filename: Optional[str] = None
    proxy_config: Optional[Dict[str, Any]] = None
    ssh_options: Dict[str, str] = Field(default_factory=dict)

    # Metadane
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    use_count: int = 0

    # Tagi i kategorie
    tags: List[str] = Field(default_factory=list)
    category: str = "default"

    # Ustawienia bezpieczeństwa
    save_password: bool = False  # Czy zapisywać hasło
    password_hash: Optional[str] = None  # Hash hasła (nie same hasło)

    def to_dict(self) -> SSHProfileDict:
        """Konwertuje profil do słownika"""
        return cast(SSHProfileDict, self.model_dump())

    @classmethod
    def from_dict(cls, data: SSHProfileDict) -> "SSHProfile":
        """Tworzy profil ze słownika"""
        return cls(**data)

    def update_usage(self) -> None:
        """Aktualizuje statystyki użycia"""
        self.last_used = datetime.now()
        self.use_count += 1
        self.updated_at = datetime.now()

    def is_valid(self) -> bool:
        """Sprawdza czy profil jest poprawny"""
        return bool(self.name and self.hostname and self.username)

    def get_connection_string(self) -> str:
        """Zwraca string połączenia (bez hasła)"""
        if self.username:
            return f"{self.username}@{self.hostname}:{self.port}"
        return f"{self.hostname}:{self.port}"

    def __str__(self) -> str:
        """Bezpieczna reprezentacja string"""
        return f"SSHProfile(name='{self.name}', hostname='{self.hostname}', username='{self.username}')"

    def __repr__(self) -> str:
        """Bezpieczna reprezentacja repr"""
        return f"SSHProfile(id='{self.id}', name='{self.name}', hostname='{self.hostname}')"

    def __hash__(self) -> int:
        """Bezpieczny hash"""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Bezpieczne porównanie"""
        if not isinstance(other, SSHProfile):
            return False
        return self.id == other.id
