"""
Serwis zarządzania profilami SSH
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from ..model.credential_store import CredentialStore
from ..model.ssh_profile import SSHProfile

logger = logging.getLogger(__name__)


class SSHProfileService:
    """Serwis zarządzania profilami SSH"""

    def __init__(self, storage_path: Optional[str] = None, load_profiles: bool = True):
        self.storage_path = storage_path or os.path.expanduser("~/.mancer/profiles")
        self.profiles: Dict[str, SSHProfile] = {}
        self.credential_store = CredentialStore()

        # Upewnij się że katalog istnieje
        os.makedirs(self.storage_path, mode=0o700, exist_ok=True)

        # Załaduj istniejące profile tylko jeśli wymagane
        if load_profiles:
            self._load_profiles()

    def create_profile(
        self,
        name: str,
        hostname: str,
        username: str,
        port: int = 22,
        description: str = "",
        key_filename: Optional[str] = None,
        proxy_config: Optional[Dict[str, Any]] = None,
        ssh_options: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        category: str = "default",
        save_password: bool = False,
    ) -> SSHProfile:
        """Tworzy nowy profil SSH"""

        # Sprawdź czy nazwa jest unikalna
        if self.get_profile_by_name(name):
            raise ValueError(f"Profil o nazwie '{name}' już istnieje")

        # Stwórz profil
        profile = SSHProfile(
            name=name,
            description=description,
            hostname=hostname,
            username=username,
            port=port,
            key_filename=key_filename,
            proxy_config=proxy_config or {},
            ssh_options=ssh_options or {},
            tags=tags or [],
            category=category,
            save_password=save_password,
        )

        # Zapisz profil
        self.profiles[profile.id] = profile
        self._save_profiles()

        logger.info(f"Utworzono profil SSH: {name} ({hostname}:{port})")
        return profile

    def update_profile(self, profile_id: str, **kwargs: Any) -> SSHProfile:
        """Aktualizuje profil SSH"""
        if profile_id not in self.profiles:
            raise ValueError(f"Profil o ID {profile_id} nie istnieje")

        profile = self.profiles[profile_id]

        # Aktualizuj pola
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        # Aktualizuj timestamp
        profile.updated_at = datetime.now()

        # Zapisz zmiany
        self._save_profiles()

        try:
            profile_name = getattr(profile, "name", "Nieznany")
            logger.info(f"Zaktualizowano profil SSH: {profile_name}")
        except Exception:
            logger.info(f"Zaktualizowano profil SSH o ID: {profile_id}")
        return profile

    def delete_profile(self, profile_id: str) -> bool:
        """Usuwa profil SSH"""
        if profile_id not in self.profiles:
            return False

        profile = self.profiles[profile_id]

        # Usuń poświadczenia
        self.credential_store.remove_profile_credentials(profile_id)

        # Usuń profil
        del self.profiles[profile_id]
        self._save_profiles()

        try:
            profile_name = getattr(profile, "name", "Nieznany")
            logger.info(f"Usunięto profil SSH: {profile_name}")
        except Exception:
            logger.info(f"Usunięto profil SSH o ID: {profile_id}")
        return True

    def get_profile(self, profile_id: str) -> Optional[SSHProfile]:
        """Pobiera profil po ID"""
        return self.profiles.get(profile_id)

    def get_profile_by_name(self, name: str) -> Optional[SSHProfile]:
        """Pobiera profil po nazwie"""
        for profile in self.profiles.values():
            if profile.name == name:
                return profile
        return None

    def list_profiles(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[SSHProfile]:
        """Listuje profile z filtrowaniem"""
        profiles = list(self.profiles.values())

        # Filtruj po kategorii
        if category:
            profiles = [p for p in profiles if getattr(p, "category", "default") == category]

        # Filtruj po tagach
        if tags:
            profiles = [p for p in profiles if any(tag in getattr(p, "tags", []) for tag in tags)]

        # Sortuj po ostatnim użyciu i nazwie
        def safe_sort_key(p):
            try:
                last_used = getattr(p, "last_used", None)
                name = getattr(p, "name", "")
                return (last_used or datetime(1900, 1, 1), str(name))
            except Exception:
                return (datetime(1900, 1, 1), "")

        profiles.sort(key=safe_sort_key)

        return profiles

    def search_profiles(self, query: str) -> List[SSHProfile]:
        """Wyszukuje profile po tekście"""
        query = query.lower()
        results = []

        for profile in self.profiles.values():
            try:
                # Bezpieczne pobieranie danych profilu
                name = getattr(profile, "name", "").lower()
                description = getattr(profile, "description", "").lower()
                hostname = getattr(profile, "hostname", "").lower()
                username = getattr(profile, "username", "").lower()
                tags = getattr(profile, "tags", [])

                # Szukaj w nazwie, opisie, hostname, username
                if (
                    query in name
                    or query in description
                    or query in hostname
                    or query in username
                    or any(query in str(tag).lower() for tag in tags)
                ):
                    results.append(profile)
            except Exception:
                continue

        return results

    def get_profile_credentials(self, profile_id: str) -> Optional[str]:
        """Pobiera zapisane poświadczenia dla profilu"""
        return self.credential_store.get_password(profile_id)

    def store_profile_credentials(self, profile_id: str, password: str, expires_in_days: Optional[int] = None) -> str:
        """Zapisuje poświadczenia dla profilu"""
        return self.credential_store.store_password(profile_id, password, expires_in_days)

    def remove_profile_credentials(self, profile_id: str) -> bool:
        """Usuwa poświadczenia dla profilu"""
        return self.credential_store.remove_profile_credentials(profile_id)

    def update_profile_usage(self, profile_id: str) -> None:
        """Aktualizuje statystyki użycia profilu"""
        if profile_id in self.profiles:
            self.profiles[profile_id].update_usage()
            self._save_profiles()

    def get_categories(self) -> List[str]:
        """Zwraca listę wszystkich kategorii"""
        categories = set()
        for profile in self.profiles.values():
            try:
                category = getattr(profile, "category", "default")
                if category:
                    categories.add(str(category))
            except Exception:
                continue
        return sorted(list(categories))

    def get_tags(self) -> List[str]:
        """Zwraca listę wszystkich tagów"""
        tags = set()
        for profile in self.profiles.values():
            try:
                profile_tags = getattr(profile, "tags", [])
                if profile_tags:
                    for tag in profile_tags:
                        if tag:
                            tags.add(str(tag))
            except Exception:
                continue
        return sorted(list(tags))

    def export_profile(self, profile_id: str, include_credentials: bool = False) -> Dict[str, Any]:
        """Eksportuje profil do słownika"""
        if profile_id not in self.profiles:
            raise ValueError(f"Profil o ID {profile_id} nie istnieje")

        profile = self.profiles[profile_id]
        export_data = cast(Dict[str, Any], profile.model_dump())

        # Dodaj poświadczenia jeśli wymagane
        if include_credentials:
            password = self.get_profile_credentials(profile_id)
            if password:
                export_data["password"] = password

        return export_data

    def import_profile(self, profile_data: Dict[str, Any], overwrite: bool = False) -> SSHProfile:
        """Importuje profil ze słownika"""
        # Sprawdź czy profil już istnieje
        if "name" in profile_data:
            existing_profile = self.get_profile_by_name(profile_data["name"])
            if existing_profile and not overwrite:
                raise ValueError(f"Profil o nazwie '{profile_data['name']}' już istnieje")
            if existing_profile and overwrite:
                # Usuń istniejący profil
                self.delete_profile(existing_profile.id)

        # Stwórz profil
        profile = cast(SSHProfile, SSHProfile.model_validate(profile_data))

        # Zapisz profil
        self.profiles[profile.id] = profile
        self._save_profiles()

        # Zapisz poświadczenia jeśli są
        if "password" in profile_data:
            self.store_profile_credentials(profile.id, profile_data["password"])

        try:
            profile_name = getattr(profile, "name", "Nieznany")
            logger.info(f"Zaimportowano profil SSH: {profile_name}")
        except Exception:
            logger.info(f"Zaimportowano profil SSH o ID: {profile.id}")
        return profile

    def _save_profiles(self):
        """Zapisuje profile do pliku"""
        try:
            profiles_file = os.path.join(self.storage_path, "ssh_profiles.json")

            # Konwertuj profile do słowników
            data = {profile_id: profile.model_dump() for profile_id, profile in self.profiles.items()}

            # Zapisz do pliku
            with open(profiles_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Błąd zapisywania profili: {e}")

    def _load_profiles(self):
        """Ładuje profile z pliku"""
        try:
            profiles_file = os.path.join(self.storage_path, "ssh_profiles.json")

            if not os.path.exists(profiles_file):
                return

            with open(profiles_file, "r") as f:
                data = json.load(f)

            # Konwertuj ze słowników z zabezpieczeniem
            for profile_id, profile_data in data.items():
                try:
                    profile = SSHProfile.model_validate(profile_data)
                    self.profiles[profile_id] = profile
                except Exception as e:
                    logger.warning(f"Pominięto problematyczny profil {profile_id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Błąd ładowania profili: {e}")

    def cleanup_expired_credentials(self) -> int:
        """Usuwa wygasłe poświadczenia"""
        return self.credential_store.cleanup_expired()
