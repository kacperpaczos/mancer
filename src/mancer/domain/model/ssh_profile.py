"""
Model profilu SSH - przechowuje konfigurację połączenia
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SSHProfile:
    """Profil połączenia SSH"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    hostname: str = ""
    username: str = ""
    port: int = 22
    key_filename: Optional[str] = None
    proxy_config: Optional[Dict[str, Any]] = None
    ssh_options: Dict[str, str] = field(default_factory=dict)

    # Metadane
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    use_count: int = 0

    # Tagi i kategorie
    tags: List[str] = field(default_factory=list)
    category: str = "default"

    # Ustawienia bezpieczeństwa
    save_password: bool = False  # Czy zapisywać hasło
    password_hash: Optional[str] = None  # Hash hasła (nie same hasło)

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje profil do słownika"""
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

        safe_ssh_options = {}
        if self.ssh_options:
            try:
                for key, value in self.ssh_options.items():
                    if isinstance(value, (str, int, float, bool, type(None))):
                        safe_ssh_options[str(key)] = value
                    else:
                        safe_ssh_options[str(key)] = str(value)
            except Exception:
                safe_ssh_options = {"error": "Nie można skonwertować ssh_options"}

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "hostname": self.hostname,
            "username": self.username,
            "port": self.port,
            "key_filename": self.key_filename,
            "proxy_config": safe_proxy_config,
            "ssh_options": safe_ssh_options,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "use_count": self.use_count,
            "tags": self.tags,
            "category": self.category,
            "save_password": self.save_password,
            "password_hash": self.password_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SSHProfile":
        """Tworzy profil ze słownika"""
        profile = cls()
        profile.id = data.get("id", str(uuid.uuid4()))
        profile.name = data.get("name", "")
        profile.description = data.get("description", "")
        profile.hostname = data.get("hostname", "")
        profile.username = data.get("username", "")
        profile.port = data.get("port", 22)
        profile.key_filename = data.get("key_filename")
        profile.proxy_config = data.get("proxy_config")
        profile.ssh_options = data.get("ssh_options", {})

        # Parsuj daty
        if "created_at" in data:
            profile.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            profile.updated_at = datetime.fromisoformat(data["updated_at"])
        if "last_used" in data and data["last_used"]:
            profile.last_used = datetime.fromisoformat(data["last_used"])

        profile.use_count = data.get("use_count", 0)
        profile.tags = data.get("tags", [])
        profile.category = data.get("category", "default")
        profile.save_password = data.get("save_password", False)
        profile.password_hash = data.get("password_hash")

        return profile

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
