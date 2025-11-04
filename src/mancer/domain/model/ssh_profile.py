"""
Model profilu SSH - przechowuje konfigurację połączenia
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje profil do słownika"""
        # Użyj model_dump() jako podstawy
        data = self.model_dump()

        # Bezpieczne konwersje dla proxy_config i ssh_options
        safe_proxy_config = None
        if self.proxy_config:
            try:
                # Konwertuj do prostych typów
                safe_proxy_config = {}
                for key, value in self.proxy_config.items():
                    if isinstance(value, (str, int, float, bool, type(None))):
                        safe_proxy_config[str(key)] = value
                    else:
                        safe_proxy_config[str(key)] = str(value)
            except Exception:
                safe_proxy_config = {"error": "Nie można skonwertować proxy_config"}

        # Konwersja ssh_options do bezpiecznych typów bez zagnieżdżonych try/except
        safe_ssh_options = {
            str(key): (value if isinstance(value, (str, int, float, bool, type(None))) else str(value))
            for key, value in (self.ssh_options or {}).items()
        }

        # Zaktualizuj dane bezpiecznymi wersjami
        data.update(
            {
                "proxy_config": safe_proxy_config,
                "ssh_options": safe_ssh_options,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "last_used": self.last_used.isoformat() if self.last_used else None,
            }
        )

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SSHProfile":
        """Tworzy profil ze słownika"""
        # Przygotuj dane dla model_validate
        processed_data = data.copy()

        # Parsuj daty
        if "created_at" in processed_data and isinstance(processed_data["created_at"], str):
            processed_data["created_at"] = datetime.fromisoformat(processed_data["created_at"])
        if "updated_at" in processed_data and isinstance(processed_data["updated_at"], str):
            processed_data["updated_at"] = datetime.fromisoformat(processed_data["updated_at"])
        if (
            "last_used" in processed_data
            and processed_data["last_used"]
            and isinstance(processed_data["last_used"], str)
        ):
            processed_data["last_used"] = datetime.fromisoformat(processed_data["last_used"])

        # Ustaw domyślne wartości jeśli brak
        if "id" not in processed_data:
            processed_data["id"] = str(uuid.uuid4())
        if "ssh_options" not in processed_data:
            processed_data["ssh_options"] = {}
        if "tags" not in processed_data:
            processed_data["tags"] = []

        return cls.model_validate(processed_data)

    def update_usage(self):
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

    def __eq__(self, other) -> bool:
        """Bezpieczne porównanie"""
        if not isinstance(other, SSHProfile):
            return False
        return self.id == other.id
