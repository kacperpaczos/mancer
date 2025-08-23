import threading
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ...infrastructure.backend.ssh_backend import SCPTransfer, SshBackend, SSHSession
from ..model.config_manager import ConfigManager

if TYPE_CHECKING:
    from ..model.ssh_profile import SSHProfile


class SSHSessionService:
    """Serwis do zarządzania sesjami SSH i transferami SCP"""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager
        self.ssh_backend = SshBackend()
        self.sessions: Dict[str, SSHSession] = {}
        self.transfers: Dict[str, SCPTransfer] = {}
        self.lock = threading.Lock()

        # Inicjalizacja loggera
        self._setup_logger()

        # Inicjalizacja CredentialStore
        try:
            from ..model.credential_store import CredentialStore

            self.credential_store = CredentialStore()
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Nie udało się zainicjalizować CredentialStore: {e}")
            self.credential_store = None

    def _setup_logger(self):
        """Konfiguruje logger dla serwisu"""
        try:
            from ...infrastructure.logging.mancer_logger import MancerLogger

            self.logger = MancerLogger.get_instance()
        except Exception:
            self.logger = None

    def create_session(
        self,
        hostname: str,
        username: str,
        port: int = 22,
        key_filename: Optional[str] = None,
        password: Optional[str] = None,
        proxy_config: Optional[Dict[str, Any]] = None,
        request_password_callback: Optional[callable] = None,
        **kwargs,
    ) -> SSHSession:
        """Tworzy nową sesję SSH"""
        session_id = str(uuid.uuid4())

        # Konfiguruj backend dla tej sesji
        session_backend = SshBackend(
            hostname=hostname,
            username=username,
            port=port,
            key_filename=key_filename,
            password=password,
            proxy_config=proxy_config,
            **kwargs,
        )

        # Sprawdź czy potrzebne jest hasło
        if not password and not key_filename and request_password_callback:
            try:
                password = request_password_callback(hostname, username)
                if not password:
                    raise ValueError("Hasło jest wymagane")
            except Exception as e:
                raise ValueError(f"Błąd pobierania hasła: {e}")

        # Sprawdź połączenie przed utworzeniem sesji
        if not self._test_connection(
            hostname, username, password, port, key_filename, proxy_config, **kwargs
        ):
            raise ValueError(f"Nie udało się połączyć z serwerem {hostname}:{port}")

        # Stwórz sesję
        session = session_backend.create_session(
            session_id=session_id,
            hostname=hostname,
            username=username,
            port=port,
            **kwargs,
        )

        with self.lock:
            self.sessions[session_id] = session
            # Zastąp backend w sesji naszym backendem
            session.connection_info["backend"] = session_backend

        return session

    def create_session_from_profile(
        self, profile: "SSHProfile", password: Optional[str] = None
    ) -> SSHSession:
        """Tworzy sesję SSH z profilu"""
        if self.logger:
            self.logger.info(
                f"Tworzenie sesji SSH z profilu: {profile.name} ({profile.hostname}:{profile.port})"
            )

        # Użyj hasła z profilu jeśli nie podano
        if not password and profile.save_password:
            try:
                # Pobierz hasło z CredentialStore
                password = self.credential_store.get_password(profile.id)
                if self.logger:
                    self.logger.info(f"Pobrano zapisane hasło dla profilu: {profile.name}")
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"Nie udało się pobrać hasła dla profilu {profile.name}: {e}"
                    )

        # Stwórz sesję używając parametrów z profilu
        session = self.create_session(
            hostname=profile.hostname,
            username=profile.username,
            port=profile.port,
            key_filename=profile.key_filename,
            password=password,
            proxy_config=profile.proxy_config,
            **profile.ssh_options,
        )

        # Aktualizuj statystyki użycia profilu
        try:
            profile.update_usage()
            if self.logger:
                self.logger.info(f"Zaktualizowano statystyki użycia profilu: {profile.name}")
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    f"Nie udało się zaktualizować statystyk profilu {profile.name}: {e}"
                )

        return session

    def check_host_fingerprint(
        self,
        hostname: str,
        username: str,
        port: int = 22,
        key_filename: Optional[str] = None,
        proxy_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Check SSH host fingerprint - simplified approach

        Args:
            hostname: Host address
            username: Username
            port: SSH port (default 22)
            key_filename: Path to private key
            proxy_config: Proxy configuration
            **kwargs: Additional SSH options

        Returns:
            Tuple (is_known, key_type, fingerprint)
            - is_known: True if host is known in known_hosts
            - key_type: Key type (e.g., "ED25519", "RSA")
            - fingerprint: Key fingerprint (always None in simplified approach)
        """
        try:
            # Stwórz backend do sprawdzenia klucza
            backend = SshBackend(
                hostname=hostname,
                username=username,
                port=port,
                key_filename=key_filename,
                proxy_config=proxy_config,
                **kwargs,
            )

            # Sprawdź klucz hosta
            is_known, key_type, fingerprint = backend.check_host_key()

            if self.logger:
                if is_known:
                    self.logger.info(f"Host {hostname}:{port} is known in known_hosts")
                else:
                    self.logger.info(
                        f"Host {hostname}:{port} is not known - will be handled during connection"
                    )

            return (
                is_known,
                key_type,
                None,
            )  # Simplified approach - no fingerprint extraction

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking host fingerprint for {hostname}:{port}: {e}")
            return False, None, None

    def add_host_to_known_hosts(
        self, hostname: str, port: int, key_type: str, fingerprint: str
    ) -> bool:
        """Dodaje host do known_hosts

        Args:
            hostname: Adres hosta
            port: Port SSH
            key_type: Typ klucza
            fingerprint: Fingerprint klucza

        Returns:
            True jeśli dodano pomyślnie
        """
        try:
            # Import tutaj żeby uniknąć circular imports
            import os
            import sys
            from pathlib import Path

            # Dodaj ścieżkę do prototypów
            prototype_path = (
                Path(__file__).parent.parent.parent.parent.parent / "prototypes" / "mancer-terminal"
            )
            sys.path.insert(0, str(prototype_path))

            try:
                from gui.ssh_fingerprint_dialog import SSHHostKeyManager
            finally:
                # Usuń ścieżkę po imporcie
                if str(prototype_path) in sys.path:
                    sys.path.remove(str(prototype_path))

            # Użyj managera kluczy
            key_manager = SSHHostKeyManager()

            # Dodaj klucz (fingerprint zawiera już pełne dane klucza)
            success = key_manager.add_host_key(hostname, port, key_type, fingerprint)

            if self.logger:
                if success:
                    self.logger.info(f"Dodano host {hostname}:{port} do known_hosts")
                else:
                    self.logger.error(f"Nie udało się dodać hosta {hostname}:{port} do known_hosts")

            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Błąd dodawania hosta do known_hosts: {e}")
            return False

    def _test_connection(
        self,
        hostname: str,
        username: str,
        password: Optional[str],
        port: int,
        key_filename: Optional[str],
        proxy_config: Optional[Dict[str, Any]],
        **kwargs,
    ) -> bool:
        """Testuje połączenie SSH przed utworzeniem sesji"""
        try:
            # Stwórz tymczasowy backend do testu
            test_backend = SshBackend(
                hostname=hostname,
                username=username,
                password=password,
                port=port,
                key_filename=key_filename,
                proxy_config=proxy_config,
                **kwargs,
            )

            # Spróbuj połączyć się
            return test_backend.test_connection()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Błąd testu połączenia z {hostname}:{port}: {e}")
            return False

    def connect_session(self, session_id: str) -> bool:
        """Łączy sesję SSH"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        backend = session.connection_info.get("backend")

        if not backend:
            return False

        return backend.connect_session(session_id)

    def disconnect_session(self, session_id: str) -> bool:
        """Rozłącza sesję SSH"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        backend = session.connection_info.get("backend")

        if not backend:
            return False

        return backend.disconnect_session(session_id)

    def execute_command(
        self,
        command: str,
        session_id: str,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ):
        """Wykonuje komendę na sesji SSH"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        backend = session.connection_info.get("backend")

        if not backend:
            return None

        return backend.execute_command(
            command=command,
            session_id=session_id,
            working_dir=working_dir,
            env_vars=env_vars,
        )

    def scp_upload(
        self, local_path: str, remote_path: str, session_id: str
    ) -> Optional[SCPTransfer]:
        """Upload pliku przez SCP"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        backend = session.connection_info.get("backend")

        if not backend:
            return None

        transfer = backend.scp_upload(local_path, remote_path, session_id)

        with self.lock:
            self.transfers[transfer.id] = transfer

        return transfer

    def scp_download(
        self, remote_path: str, local_path: str, session_id: str
    ) -> Optional[SCPTransfer]:
        """Download pliku przez SCP"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        backend = session.connection_info.get("backend")

        if not backend:
            return None

        transfer = backend.scp_download(remote_path, local_path, session_id)

        with self.lock:
            self.transfers[transfer.id] = transfer

        return transfer

    def get_session_status(self, session_id: str) -> Optional[str]:
        """Pobiera status sesji"""
        if session_id in self.sessions:
            return self.sessions[session_id].status
        return None

    def list_sessions(self) -> List[SSHSession]:
        """Listuje wszystkie sesje"""
        with self.lock:
            return list(self.sessions.values())

    def get_transfer_status(self, transfer_id: str) -> Optional[SCPTransfer]:
        """Pobiera status transferu"""
        with self.lock:
            return self.transfers.get(transfer_id)

    def list_transfers(self) -> List[SCPTransfer]:
        """Listuje wszystkie transfery"""
        with self.lock:
            return list(self.transfers.values())

    def cancel_transfer(self, transfer_id: str) -> bool:
        """Anuluje transfer"""
        with self.lock:
            if transfer_id in self.transfers:
                transfer = self.transfers[transfer_id]
                if transfer.status == "transferring":
                    transfer.status = "cancelled"
                    return True
        return False

    def close_session(self, session_id: str) -> bool:
        """Zamyka sesję i usuwa ją"""
        if session_id not in self.sessions:
            return False

        # Rozłącz sesję
        self.disconnect_session(session_id)

        # Usuń sesję
        with self.lock:
            del self.sessions[session_id]

        return True

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Pobiera szczegółowe informacje o sesji"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        backend = session.connection_info.get("backend")

        info = {
            "id": session.id,
            "hostname": session.hostname,
            "username": session.username,
            "port": session.port,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "active_transfers": [],
        }

        # Dodaj aktywne transfery dla tej sesji
        for transfer in self.transfers.values():
            if transfer.status in ["pending", "transferring"]:
                info["active_transfers"].append(
                    {
                        "id": transfer.id,
                        "direction": transfer.direction,
                        "source": transfer.source,
                        "destination": transfer.destination,
                        "progress": transfer.progress,
                        "status": transfer.status,
                    }
                )

        return info
