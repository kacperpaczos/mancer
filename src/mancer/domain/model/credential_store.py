"""
Bezpieczne przechowywanie poświadczeń SSH
"""

import base64
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StoredCredential(BaseModel):
    """Przechowywane poświadczenie"""

    id: str
    profile_id: str
    credential_type: str  # "password", "key_passphrase", "proxy_password"
    encrypted_value: str
    salt: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    use_count: int = 0

    def is_expired(self) -> bool:
        """Sprawdza czy poświadczenie wygasło"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def update_usage(self):
        """Aktualizuje statystyki użycia"""
        self.last_used = datetime.now()
        self.use_count += 1


class CredentialStore:
    """Bezpieczne przechowywanie poświadczeń"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.expanduser("~/.mancer/credentials")
        self.credentials: Dict[str, StoredCredential] = {}
        self.master_key: Optional[str] = None

        # Upewnij się że katalog istnieje
        os.makedirs(self.storage_path, mode=0o700, exist_ok=True)

        # Załaduj istniejące poświadczenia
        self._load_credentials()

    def set_master_key(self, master_key: str):
        """Ustawia klucz główny do szyfrowania"""
        self.master_key = master_key

    def _generate_salt(self) -> str:
        """Generuje sól do szyfrowania"""
        return base64.b64encode(os.urandom(32)).decode("utf-8")

    def _derive_key(self, password: str, salt: str) -> bytes:
        """Derivuje klucz z hasła i soli"""
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)

    def _encrypt_value(self, value: str, salt: str) -> str:
        """Szyfruje wartość"""
        if not self.master_key:
            raise ValueError("Klucz główny nie jest ustawiony")

        key = self._derive_key(self.master_key, salt)
        # Proste szyfrowanie XOR (w produkcji użyj AES)
        encrypted = "".join(chr(ord(c) ^ key[i % len(key)]) for i, c in enumerate(value))
        return base64.b64encode(encrypted.encode()).decode("utf-8")

    def _decrypt_value(self, encrypted_value: str, salt: str) -> str:
        """Deszyfruje wartość"""
        if not self.master_key:
            raise ValueError("Klucz główny nie jest ustawiony")

        key = self._derive_key(self.master_key, salt)
        encrypted = base64.b64decode(encrypted_value.encode()).decode("utf-8")
        # Proste deszyfrowanie XOR
        decrypted = "".join(chr(ord(c) ^ key[i % len(key)]) for i, c in enumerate(encrypted))
        return decrypted

    def store_password(self, profile_id: str, password: str, expires_in_days: Optional[int] = None) -> str:
        """Zapisuje hasło dla profilu"""
        credential_id = f"{profile_id}_password"

        # Generuj sól
        salt = self._generate_salt()

        # Szyfruj hasło
        encrypted_password = self._encrypt_value(password, salt)

        # Ustaw datę wygaśnięcia
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        # Stwórz poświadczenie
        credential = StoredCredential(
            id=credential_id,
            profile_id=profile_id,
            credential_type="password",
            encrypted_value=encrypted_password,
            salt=salt,
            expires_at=expires_at,
        )

        # Zapisz
        self.credentials[credential_id] = credential
        self._save_credentials()

        return credential_id

    def get_password(self, profile_id: str) -> Optional[str]:
        """Pobiera hasło dla profilu"""
        credential_id = f"{profile_id}_password"

        if credential_id not in self.credentials:
            return None

        credential = self.credentials[credential_id]

        # Sprawdź czy nie wygasło
        if credential.is_expired():
            logger.warning(f"Poświadczenie {credential_id} wygasło")
            self.remove_credential(credential_id)
            return None

        try:
            # Deszyfruj hasło
            password = self._decrypt_value(credential.encrypted_value, credential.salt)
            credential.update_usage()
            self._save_credentials()
            return password
        except Exception as e:
            logger.error(f"Błąd deszyfrowania hasła: {e}")
            return None

    def remove_credential(self, credential_id: str) -> bool:
        """Usuwa poświadczenie"""
        if credential_id in self.credentials:
            del self.credentials[credential_id]
            self._save_credentials()
            return True
        return False

    def remove_profile_credentials(self, profile_id: str) -> bool:
        """Usuwa wszystkie poświadczenia dla profilu"""
        removed = False
        for credential_id in list(self.credentials.keys()):
            if self.credentials[credential_id].profile_id == profile_id:
                del self.credentials[credential_id]
                removed = True

        if removed:
            self._save_credentials()

        return removed

    def list_credentials(self) -> List[StoredCredential]:
        """Listuje wszystkie poświadczenia"""
        return list(self.credentials.values())

    def cleanup_expired(self) -> int:
        """Usuwa wygasłe poświadczenia"""
        expired_count = 0
        for credential_id in list(self.credentials.keys()):
            if self.credentials[credential_id].is_expired():
                del self.credentials[credential_id]
                expired_count += 1

        if expired_count > 0:
            self._save_credentials()

        return expired_count

    def _save_credentials(self):
        """Zapisuje poświadczenia do pliku"""
        try:
            credentials_file = os.path.join(self.storage_path, "credentials.json")

            # Konwertuj do słowników
            data = {
                credential_id: {
                    "id": cred.id,
                    "profile_id": cred.profile_id,
                    "credential_type": cred.credential_type,
                    "encrypted_value": cred.encrypted_value,
                    "salt": cred.salt,
                    "created_at": cred.created_at.isoformat(),
                    "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
                    "last_used": cred.last_used.isoformat() if cred.last_used else None,
                    "use_count": cred.use_count,
                }
                for credential_id, cred in self.credentials.items()
            }

            # Zapisz do pliku
            with open(credentials_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Błąd zapisywania poświadczeń: {e}")

    def _load_credentials(self):
        """Ładuje poświadczenia z pliku"""
        try:
            credentials_file = os.path.join(self.storage_path, "credentials.json")

            if not os.path.exists(credentials_file):
                return

            with open(credentials_file, "r") as f:
                data = json.load(f)

            # Konwertuj ze słowników
            for credential_id, cred_data in data.items():
                credential = StoredCredential(
                    id=cred_data["id"],
                    profile_id=cred_data["profile_id"],
                    credential_type=cred_data["credential_type"],
                    encrypted_value=cred_data["encrypted_value"],
                    salt=cred_data["salt"],
                    created_at=datetime.fromisoformat(cred_data["created_at"]),
                    expires_at=(datetime.fromisoformat(cred_data["expires_at"]) if cred_data["expires_at"] else None),
                    last_used=(datetime.fromisoformat(cred_data["last_used"]) if cred_data["last_used"] else None),
                    use_count=cred_data["use_count"],
                )

                self.credentials[credential_id] = credential

        except Exception as e:
            logger.error(f"Błąd ładowania poświadczeń: {e}")
