import json
import os
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

from ...infrastructure.shared.ssh_connecticer import SSHConnecticer


class ConnectionProfile:
    """Model profilu połączenia."""

    def __init__(
        self,
        name: str,
        hostname: str,
        username: str,
        port: int = 22,
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        passphrase: Optional[str] = None,
        group: Optional[str] = None,
        description: Optional[str] = None,
        ssh_options: Optional[Dict[str, str]] = None,
    ):
        """
        Inicjalizuje profil połączenia.

        Args:
            name: Unikalna nazwa profilu
            hostname: Nazwa hosta lub adres IP
            username: Nazwa użytkownika
            port: Port SSH
            password: Hasło (opcjonalnie)
            key_filename: Ścieżka do klucza prywatnego (opcjonalnie)
            passphrase: Hasło do klucza (opcjonalnie)
            group: Grupa serwerów (opcjonalnie)
            description: Opis profilu (opcjonalnie)
            ssh_options: Dodatkowe opcje SSH (opcjonalnie)
        """
        self.name = name
        self.hostname = hostname
        self.username = username
        self.port = port
        self.password = password
        self.key_filename = key_filename
        self.passphrase = passphrase
        self.group = group
        self.description = description
        self.ssh_options = ssh_options or {}

    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """
        Konwertuje profil do słownika.

        Args:
            include_secrets: Czy dołączyć wrażliwe dane

        Returns:
            Dict[str, Any]: Słownik z danymi profilu
        """
        result = {
            "name": self.name,
            "hostname": self.hostname,
            "username": self.username,
            "port": self.port,
            "group": self.group,
            "description": self.description,
            "ssh_options": self.ssh_options,
        }

        if include_secrets:
            result["password"] = self.password
            result["key_filename"] = self.key_filename
            result["passphrase"] = self.passphrase

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionProfile":
        """
        Tworzy profil z słownika.

        Args:
            data: Słownik z danymi profilu

        Returns:
            ConnectionProfile: Utworzony profil
        """
        return cls(
            name=data.get("name", ""),
            hostname=data.get("hostname", ""),
            username=data.get("username", ""),
            port=data.get("port", 22),
            password=data.get("password"),
            key_filename=data.get("key_filename"),
            passphrase=data.get("passphrase"),
            group=data.get("group"),
            description=data.get("description"),
            ssh_options=data.get("ssh_options", {}),
        )

    def create_ssh_connection(self) -> SSHConnecticer:
        """
        Tworzy obiekt połączenia SSH na podstawie profilu.

        Returns:
            SSHConnecticer: Obiekt połączenia SSH
        """
        return SSHConnecticer(
            hostname=self.hostname,
            username=self.username,
            port=self.port,
            password=self.password,
            key_filename=self.key_filename,
            passphrase=self.passphrase,
            ssh_options=self.ssh_options,
            session_name=self.name,
        )


class ProfileProducer:
    """
    Klasa zarządzająca profilami połączeń.
    Umożliwia zapisywanie, ładowanie i zarządzanie profilami.
    """

    def __init__(self, storage_dir: Optional[str] = None, encrypt_sensitive_data: bool = True):
        """
        Inicjalizuje ProfileProducer.

        Args:
            storage_dir: Katalog do przechowywania profili
            encrypt_sensitive_data: Czy szyfrować wrażliwe dane
        """
        if storage_dir is None:
            self.storage_dir = os.path.join(os.path.expanduser("~"), ".mancer", "profiles")
        else:
            self.storage_dir = storage_dir

        os.makedirs(self.storage_dir, exist_ok=True)

        self.encrypt_sensitive_data = encrypt_sensitive_data
        self._profiles: Dict[str, ConnectionProfile] = {}
        self._crypto_key = self._get_or_create_encryption_key()

    def add_profile(self, profile: ConnectionProfile) -> bool:
        """
        Dodaje nowy profil połączenia.

        Args:
            profile: Profil do dodania

        Returns:
            bool: Czy operacja się powiodła
        """
        # Sprawdzenie czy profil o takiej nazwie już istnieje
        if profile.name in self._profiles:
            return False

        # Dodanie profilu
        self._profiles[profile.name] = profile

        # Zapisanie profilu
        self._save_profile(profile)

        return True

    def get_profile(self, name: str) -> Optional[ConnectionProfile]:
        """
        Pobiera profil o określonej nazwie.

        Args:
            name: Nazwa profilu

        Returns:
            Optional[ConnectionProfile]: Profil lub None jeśli nie znaleziono
        """
        # Sprawdź czy profil jest już załadowany
        if name in self._profiles:
            return self._profiles[name]

        # Próba załadowania profilu z pliku
        profile_path = os.path.join(self.storage_dir, f"{name}.json")
        if os.path.exists(profile_path):
            profile = self._load_profile_from_file(profile_path)
            if profile:
                self._profiles[name] = profile
                return profile

        return None

    def update_profile(self, profile: ConnectionProfile) -> bool:
        """
        Aktualizuje istniejący profil.

        Args:
            profile: Profil z zaktualizowanymi danymi

        Returns:
            bool: Czy operacja się powiodła
        """
        # Sprawdzenie czy profil istnieje
        if profile.name not in self._profiles and not os.path.exists(
            os.path.join(self.storage_dir, f"{profile.name}.json")
        ):
            return False

        # Aktualizacja profilu
        self._profiles[profile.name] = profile

        # Zapisanie profilu
        self._save_profile(profile)

        return True

    def delete_profile(self, name: str) -> bool:
        """
        Usuwa profil o określonej nazwie.

        Args:
            name: Nazwa profilu

        Returns:
            bool: Czy operacja się powiodła
        """
        # Usunięcie profilu z pamięci
        if name in self._profiles:
            del self._profiles[name]

        # Usunięcie pliku profilu
        profile_path = os.path.join(self.storage_dir, f"{name}.json")
        if os.path.exists(profile_path):
            try:
                os.remove(profile_path)
                return True
            except OSError:
                return False

        return False

    def list_profiles(self, group: Optional[str] = None) -> List[ConnectionProfile]:
        """
        Listuje dostępne profile.

        Args:
            group: Opcjonalna grupa do filtrowania

        Returns:
            List[ConnectionProfile]: Lista profili
        """
        # Załaduj wszystkie profile z katalogu
        self._load_all_profiles()

        # Filtruj profile według grupy
        if group:
            return [p for p in self._profiles.values() if p.group == group]

        return list(self._profiles.values())

    def list_groups(self) -> List[str]:
        """
        Listuje dostępne grupy serwerów.

        Returns:
            List[str]: Lista nazw grup
        """
        # Załaduj wszystkie profile
        self._load_all_profiles()

        # Zbierz unikalne nazwy grup
        groups = set()
        for profile in self._profiles.values():
            if profile.group:
                groups.add(profile.group)

        return sorted(list(groups))

    def create_connection(self, profile_name: str) -> Optional[SSHConnecticer]:
        """
        Tworzy połączenie SSH na podstawie profilu.

        Args:
            profile_name: Nazwa profilu

        Returns:
            Optional[SSHConnecticer]: Obiekt połączenia SSH lub None
        """
        profile = self.get_profile(profile_name)
        if profile:
            return profile.create_ssh_connection()
        return None

    def _save_profile(self, profile: ConnectionProfile) -> bool:
        """
        Zapisuje profil do pliku.

        Args:
            profile: Profil do zapisania

        Returns:
            bool: Czy operacja się powiodła
        """
        profile_path = os.path.join(self.storage_dir, f"{profile.name}.json")

        try:
            data = profile.to_dict(include_secrets=True)

            # Szyfrowanie wrażliwych danych
            if self.encrypt_sensitive_data:
                if data.get("password"):
                    data["password"] = self._encrypt_value(data["password"])
                if data.get("passphrase"):
                    data["passphrase"] = self._encrypt_value(data["passphrase"])

            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return True
        except Exception:
            return False

    def _load_profile_from_file(self, file_path: str) -> Optional[ConnectionProfile]:
        """
        Ładuje profil z pliku.

        Args:
            file_path: Ścieżka do pliku profilu

        Returns:
            Optional[ConnectionProfile]: Załadowany profil lub None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Deszyfrowanie wrażliwych danych
            if self.encrypt_sensitive_data:
                if data.get("password"):
                    data["password"] = self._decrypt_value(data["password"])
                if data.get("passphrase"):
                    data["passphrase"] = self._decrypt_value(data["passphrase"])

            return ConnectionProfile.from_dict(data)
        except Exception:
            return None

    def _load_all_profiles(self) -> None:
        """Ładuje wszystkie profile z katalogu."""
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                profile_path = os.path.join(self.storage_dir, filename)
                profile_name = os.path.splitext(filename)[0]

                # Pomijaj już załadowane profile
                if profile_name in self._profiles:
                    continue

                profile = self._load_profile_from_file(profile_path)
                if profile:
                    self._profiles[profile.name] = profile

    def _get_or_create_encryption_key(self) -> bytes:
        """
        Pobiera lub tworzy klucz do szyfrowania.

        Returns:
            bytes: Klucz szyfrujący
        """
        key_path = os.path.join(self.storage_dir, ".encryption_key")

        if os.path.exists(key_path):
            # Odczytaj istniejący klucz
            try:
                with open(key_path, "rb") as f:
                    return f.read()
            except Exception:
                pass

        # Wygeneruj nowy klucz
        key = Fernet.generate_key()

        try:
            # Zapisz klucz do pliku z ograniczonymi uprawnieniami
            with open(key_path, "wb") as f:
                f.write(key)

            # Ustaw uprawnienia (tylko właściciel może czytać)
            os.chmod(key_path, 0o600)
        except Exception:
            pass

        return key

    def _encrypt_value(self, value: str) -> str:
        """
        Szyfruje wartość.

        Args:
            value: Wartość do zaszyfrowania

        Returns:
            str: Zaszyfrowana wartość
        """
        f = Fernet(self._crypto_key)
        return f.encrypt(value.encode()).decode()

    def _decrypt_value(self, encrypted_value: str) -> str:
        """
        Deszyfruje wartość.

        Args:
            encrypted_value: Zaszyfrowana wartość

        Returns:
            str: Odszyfrowana wartość
        """
        f = Fernet(self._crypto_key)
        return f.decrypt(encrypted_value.encode()).decode()
