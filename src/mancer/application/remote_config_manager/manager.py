"""
Główny moduł implementujący funkcjonalność zarządzania konfiguracjami na zdalnych serwerach.
"""
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import paramiko
from paramiko import SSHClient, AutoAddPolicy

from .config import AppConfig, ServerConfig
from .file_operations import FileManager, FileInfo, FileDiff

class SSHManager:
    """
    Klasa zarządzająca połączeniami SSH do zdalnych serwerów.
    """
    
    def __init__(self, server_config: ServerConfig):
        """
        Inicjalizuje menedżera SSH.
        
        Args:
            server_config: Konfiguracja serwera z danymi do połączenia
        """
        self.config = server_config
        self.ssh = None
        
    def connect(self) -> Tuple[bool, Optional[str]]:
        """
        Nawiązuje połączenie SSH z serwerem.
        
        Returns:
            Krotka (sukces, opcjonalny komunikat błędu)
        """
        self.ssh = SSHClient()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        
        try:
            # Najpierw sprawdź ping
            ping_cmd = ['ping', '-c', '1', '-W', '2', self.config.host]
            ping_result = subprocess.run(
                ping_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if ping_result.returncode != 0:
                return False, f"Adres IP {self.config.host} jest nieosiągalny"
            
            # Próba połączenia SSH
            self.ssh.connect(
                hostname=self.config.host,
                username=self.config.username,
                password=self.config.password,
                timeout=5
            )
            return True, None
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "authentication failed" in error_msg:
                detail = "Błędna nazwa użytkownika lub hasło"
            elif "connection refused" in error_msg:
                detail = "Port SSH (22) jest zablokowany lub usługa SSH nie jest uruchomiona"
            elif "timed out" in error_msg:
                detail = "Przekroczono limit czasu połączenia"
            else:
                detail = str(e)
                
            return False, detail
            
    def close(self) -> None:
        """
        Zamyka połączenie SSH.
        """
        if self.ssh:
            self.ssh.close()
            self.ssh = None

    def find_config_files(self) -> List[str]:
        """
        Znajduje pliki konfiguracyjne na serwerze.
        
        Returns:
            Lista ścieżek do plików konfiguracyjnych
        """
        if not self.ssh:
            return []
            
        try:
            # Wykonaj komendę find na serwerze dla wszystkich typów plików konfiguracyjnych
            find_cmd = f'find {self.config.app_dir} -type f \( -name "*.json" -o -name "*.config" -o -name "config.js" \)'
            stdin, stdout, stderr = self.ssh.exec_command(find_cmd)
            
            # Pobierz wyniki
            files = stdout.read().decode().splitlines()
            
            # Filtruj pliki według rozszerzeń
            return [f for f in files if f.endswith(('.json', '.config')) or f.endswith('config.js')]
            
        except Exception:
            return []
            
    def copy_file_from_server(self, remote_path: str, local_path: Path) -> bool:
        """
        Kopiuje plik z serwera na lokalną maszynę.
        
        Args:
            remote_path: Ścieżka pliku na serwerze
            local_path: Ścieżka docelowa na lokalnej maszynie
            
        Returns:
            True jeśli kopiowanie się powiodło, False w przeciwnym razie
        """
        if not self.ssh:
            return False
            
        try:
            sftp = self.ssh.open_sftp()
            local_path.parent.mkdir(parents=True, exist_ok=True)
            sftp.get(remote_path, str(local_path))
            sftp.close()
            return True
        except Exception:
            return False
            
    def copy_file_to_server(self, local_path: Path, remote_path: str) -> bool:
        """
        Kopiuje plik z lokalnej maszyny na serwer.
        
        Args:
            local_path: Ścieżka pliku na lokalnej maszynie
            remote_path: Ścieżka docelowa na serwerze
            
        Returns:
            True jeśli kopiowanie się powiodło, False w przeciwnym razie
        """
        if not self.ssh:
            return False
        
        try:
            sftp = self.ssh.open_sftp()
            
            # Tymczasowy plik
            temp_path = f"/tmp/{os.path.basename(remote_path)}.tmp"
            
            # Wyślij plik do katalogu tymczasowego
            sftp.put(str(local_path), temp_path)
            sftp.close()
            
            # Użyj sudo do przeniesienia pliku
            sudo_command = f"echo '{self.config.sudo_password}' | sudo -S mv {temp_path} {remote_path}"
            
            # Wykonaj komendę sudo
            stdin, stdout, stderr = self.ssh.exec_command(sudo_command)
            
            # Sprawdź czy wystąpiły błędy
            error = stderr.read().decode().strip()
            if error and "password" not in error.lower():
                return False
            
            # Ustaw odpowiednie uprawnienia
            chmod_command = f"echo '{self.config.sudo_password}' | sudo -S chmod 644 {remote_path}"
            self.ssh.exec_command(chmod_command)
            
            return True
        
        except Exception:
            return False

    def restart_service(self, service_name: str) -> Tuple[bool, Optional[str]]:
        """
        Restartuje usługę na serwerze.
        
        Args:
            service_name: Nazwa usługi do zrestartowania
            
        Returns:
            Krotka (sukces, opcjonalny komunikat błędu)
        """
        if not self.ssh:
            return False, "Brak połączenia SSH"
            
        try:
            restart_cmd = f"echo '{self.config.sudo_password}' | sudo -S systemctl restart {service_name}"
            stdin, stdout, stderr = self.ssh.exec_command(restart_cmd)
            
            # Sprawdź czy wystąpiły błędy
            error = stderr.read().decode().strip()
            if error and "password" not in error.lower():
                return False, error
                
            # Sprawdź status usługi
            status_cmd = f"echo '{self.config.sudo_password}' | sudo -S systemctl is-active {service_name}"
            stdin, stdout, stderr = self.ssh.exec_command(status_cmd)
            status = stdout.read().decode().strip()
            
            if status == "active":
                return True, None
            else:
                return False, f"Usługa {service_name} nie jest aktywna po restarcie"
                
        except Exception as e:
            return False, str(e)


class RemoteConfigManager:
    """
    Główna klasa implementująca zarządzanie konfiguracjami na zdalnych serwerach.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Inicjalizuje menedżera konfiguracji.
        
        Args:
            config_dir: Opcjonalna ścieżka do katalogu konfiguracyjnego
        """
        # Ustaw ścieżki katalogów
        self.base_dir = Path(config_dir) if config_dir else Path.home() / ".remote_config_manager"
        self.profiles_dir = self.base_dir / "profiles"
        self.servers_dir = self.base_dir / "servers"
        self.cache_dir = self.base_dir / "cache"
        self.backup_dir = self.base_dir / "backups"
        
        # Utwórz strukturę katalogów
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.servers_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Ustaw domyślne wartości
        self.active_profile: Optional[str] = None
        self.config: Optional[AppConfig] = None
        self.ssh_manager: Optional[SSHManager] = None
        self.file_manager = FileManager()
        
        # Wczytaj aktywny profil
        active_profile_path = self.base_dir / "active_profile.txt"
        if active_profile_path.exists():
            with open(active_profile_path, "r") as f:
                self.active_profile = f.read().strip()
            self.load_active_profile()

    def create_default_profile(self) -> None:
        """
        Tworzy domyślny profil, jeśli nie istnieje żaden profil.
        """
        default_profile_path = self.profiles_dir / "default.json"
        
        if not default_profile_path.exists():
            default_config = {
                "name": "default",
                "server": {
                    "host": "example.com",
                    "username": "admin",
                    "password": "",
                    "sudo_password": "",
                    "app_dir": "/var/www/html",
                    "services": ["nginx", "php-fpm"]
                }
            }
            
            with open(default_profile_path, "w") as f:
                json.dump(default_config, f, indent=4)
                
            self.active_profile = "default"
            with open(self.base_dir / "active_profile.txt", "w") as f:
                f.write(self.active_profile)
                
            self.load_active_profile()

    def load_active_profile(self) -> bool:
        """
        Wczytuje aktywny profil.
        
        Returns:
            True jeśli profil został wczytany, False w przeciwnym razie
        """
        if not self.active_profile:
            return False
            
        profile_path = self.profiles_dir / f"{self.active_profile}.json"
        if not profile_path.exists():
            return False
            
        try:
            with open(profile_path, "r") as f:
                profile_data = json.load(f)
                server_config = ServerConfig(
                    host=profile_data["server"]["host"],
                    username=profile_data["server"]["username"],
                    password=profile_data["server"]["password"],
                    sudo_password=profile_data["server"]["sudo_password"],
                    app_dir=profile_data["server"]["app_dir"],
                    services=profile_data["server"]["services"]
                )
                
                self.config = AppConfig(
                    name=profile_data["name"],
                    server=server_config
                )
                
                return True
        except (KeyError, json.JSONDecodeError):
            return False

    def save_profile(self, name: str, config_data: Dict[str, Any]) -> bool:
        """
        Zapisuje profil do pliku.
        
        Args:
            name: Nazwa profilu
            config_data: Dane konfiguracyjne
            
        Returns:
            True jeśli profil został zapisany, False w przeciwnym razie
        """
        try:
            profile_path = self.profiles_dir / f"{name}.json"
            
            with open(profile_path, "w") as f:
                json.dump(config_data, f, indent=4)
                
            return True
        except Exception:
            return False

    def connect_to_server(self) -> Tuple[bool, Optional[str]]:
        """
        Nawiązuje połączenie z serwerem.
        
        Returns:
            Krotka (sukces, opcjonalny komunikat błędu)
        """
        if not self.config:
            return False, "Brak aktywnego profilu"
            
        # Zamknij poprzednie połączenie
        if self.ssh_manager:
            self.ssh_manager.close()
            
        # Utwórz nowe połączenie
        self.ssh_manager = SSHManager(self.config.server)
        return self.ssh_manager.connect()

    def get_config_files(self) -> List[str]:
        """
        Pobiera listę plików konfiguracyjnych z serwera.
        
        Returns:
            Lista ścieżek do plików konfiguracyjnych
        """
        if not self.ssh_manager:
            return []
            
        return self.ssh_manager.find_config_files()

    def backup_server_files(self) -> Tuple[bool, List[str], List[str]]:
        """
        Tworzy kopię zapasową plików z serwera.
        
        Returns:
            Krotka (sukces, lista skopiowanych plików, lista nieudanych kopii)
        """
        if not self.ssh_manager or not self.config:
            return False, [], []
            
        # Utwórz katalog dla serwera
        server_dir = self.servers_dir / self.config.server.host
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Pobierz listę plików
        config_files = self.get_config_files()
        if not config_files:
            return False, [], []
            
        successful = []
        failed = []
        
        for remote_path in config_files:
            # Utwórz ścieżkę lokalną z zachowaniem struktury katalogów
            rel_path = remote_path.replace(self.config.server.app_dir, "").lstrip("/")
            local_path = server_dir / rel_path
            
            # Kopiuj plik
            success = self.ssh_manager.copy_file_from_server(remote_path, local_path)
            if success:
                successful.append(remote_path)
            else:
                failed.append(remote_path)
                
        # Utwórz kopię kopii zapasowej z datą/godziną
        if successful:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{self.config.server.host}_{timestamp}"
            shutil.copytree(server_dir, backup_path)
            
        return len(successful) > 0, successful, failed

    def copy_server_to_cache(self) -> bool:
        """
        Kopiuje pliki serwera do pamięci podręcznej.
        
        Returns:
            True jeśli kopiowanie się powiodło, False w przeciwnym razie
        """
        if not self.config:
            return False
            
        source_path = self.servers_dir / self.config.server.host
        if not source_path.exists():
            return False
            
        cache_path = self.cache_dir / self.config.server.host
        try:
            # Usuń istniejący cache
            if cache_path.exists():
                shutil.rmtree(cache_path)
            
            # Skopiuj całą strukturę
            shutil.copytree(source_path, cache_path)
            return True
        except Exception:
            return False

    def find_differences(self) -> List[FileDiff]:
        """
        Znajduje różnice między plikami w pamięci podręcznej a plikami serwerowymi.
        
        Returns:
            Lista różnic w plikach
        """
        if not self.config:
            return []
            
        server_dir = self.servers_dir / self.config.server.host
        cache_dir = self.cache_dir / self.config.server.host
        
        if not server_dir.exists() or not cache_dir.exists():
            return []
            
        differences = []
        
        # Znajdź wszystkie pliki w katalogu serwera
        server_files = list(server_dir.rglob("*.*"))
        for server_file in server_files:
            rel_path = server_file.relative_to(server_dir)
            cache_file = cache_dir / rel_path
            
            if cache_file.exists():
                # Porównaj pliki
                is_different, diff_content = self.file_manager.compare_files(server_file, cache_file)
                if is_different:
                    differences.append(
                        FileDiff(
                            server_path=str(server_file),
                            cache_path=str(cache_file),
                            rel_path=str(rel_path),
                            differences=diff_content
                        )
                    )
                    
        return differences

    def update_server_files(self, diffs: List[FileDiff]) -> Tuple[List[str], List[str]]:
        """
        Aktualizuje pliki na serwerze na podstawie plików w pamięci podręcznej.
        
        Args:
            diffs: Lista różnic w plikach
            
        Returns:
            Krotka (lista zaktualizowanych plików, lista nieudanych aktualizacji)
        """
        if not self.ssh_manager or not self.config:
            return [], []
            
        updated = []
        failed = []
        
        for diff in diffs:
            # Ścieżka pliku na serwerze
            remote_path = os.path.join(self.config.server.app_dir, diff.rel_path)
            local_path = Path(diff.cache_path)
            
            success = self.ssh_manager.copy_file_to_server(local_path, remote_path)
            if success:
                updated.append(remote_path)
            else:
                failed.append(remote_path)
                
        return updated, failed

    def restart_services(self) -> Dict[str, bool]:
        """
        Restartuje usługi na serwerze.
        
        Returns:
            Słownik {nazwa_usługi: status_restartu}
        """
        if not self.ssh_manager or not self.config:
            return {}
            
        results = {}
        
        for service in self.config.server.services:
            success, _ = self.ssh_manager.restart_service(service)
            results[service] = success
            
        return results

    def list_profiles(self) -> List[str]:
        """
        Zwraca listę dostępnych profili.
        
        Returns:
            Lista nazw profili
        """
        profiles = []
        for profile_path in self.profiles_dir.glob("*.json"):
            profiles.append(profile_path.stem)
            
        return profiles

    def get_profile_details(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Pobiera szczegóły profilu.
        
        Args:
            profile_name: Nazwa profilu
            
        Returns:
            Słownik z danymi profilu lub None, jeśli profil nie istnieje
        """
        profile_path = self.profiles_dir / f"{profile_name}.json"
        if not profile_path.exists():
            return None
            
        try:
            with open(profile_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None

    def delete_profile(self, profile_name: str) -> bool:
        """
        Usuwa profil.
        
        Args:
            profile_name: Nazwa profilu do usunięcia
            
        Returns:
            True jeśli profil został usunięty, False w przeciwnym razie
        """
        profile_path = self.profiles_dir / f"{profile_name}.json"
        if not profile_path.exists():
            return False
            
        try:
            profile_path.unlink()
            
            # Jeśli usunięto aktywny profil, zresetuj
            if self.active_profile == profile_name:
                self.active_profile = None
                active_profile_path = self.base_dir / "active_profile.txt"
                if active_profile_path.exists():
                    active_profile_path.unlink()
                self.config = None
                
            return True
        except Exception:
            return False

    def set_active_profile(self, profile_name: str) -> bool:
        """
        Ustawia aktywny profil.
        
        Args:
            profile_name: Nazwa profilu
            
        Returns:
            True jeśli profil został ustawiony, False w przeciwnym razie
        """
        profile_path = self.profiles_dir / f"{profile_name}.json"
        if not profile_path.exists():
            return False
            
        try:
            self.active_profile = profile_name
            with open(self.base_dir / "active_profile.txt", "w") as f:
                f.write(profile_name)
                
            return self.load_active_profile()
        except Exception:
            return False

    def get_available_servers(self) -> List[str]:
        """
        Zwraca listę dostępnych serwerów w katalogu serwerów.
        
        Returns:
            Lista nazw serwerów
        """
        servers = []
        for server_dir in self.servers_dir.iterdir():
            if server_dir.is_dir():
                servers.append(server_dir.name)
                
        return servers

    def clean_cache(self) -> bool:
        """
        Czyści pamięć podręczną.
        
        Returns:
            True jeśli czyszczenie się powiodło, False w przeciwnym razie
        """
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True)
            return True
        except Exception:
            return False

    def disconnect(self) -> None:
        """
        Zamyka połączenie z serwerem.
        """
        if self.ssh_manager:
            self.ssh_manager.close()
            self.ssh_manager = None 