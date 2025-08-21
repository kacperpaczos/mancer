import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from cli import CLI
from config import AppConfig, ServerConfig, load_config
from file_operations import FileInfo, FileManager
from paramiko import AutoAddPolicy, SSHClient
from rich.progress import Progress, SpinnerColumn
from rich.prompt import Confirm, Prompt


class SSHManager:
    def __init__(self, config: AppConfig, cli: CLI):
        self.config = config
        self.cli = cli
        self.ssh = None

    def connect(self) -> bool:
        self.ssh = SSHClient()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())

        try:
            # Najpierw sprawdź ping
            ping_result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", self.config.server.ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if ping_result.returncode != 0:
                self.cli.log(
                    "Błąd połączenia",
                    {
                        "szczegóły": "Adres IP jest nieosiągalny",
                        "host": self.config.server.ip,
                    },
                    status="error",
                )
                return False

            self.cli.log(
                "Próba połączenia SSH",
                {"host": self.config.server.ip, "user": self.config.server.username},
            )

            self.ssh.connect(
                hostname=self.config.server.ip,
                username=self.config.server.username,
                password=self.config.server.password,
                timeout=5,
            )
            return True

        except Exception as e:
            error_msg = str(e).lower()
            error_details = {
                "typ błędu": type(e).__name__,
                "host": self.config.server.ip,
                "użytkownik": self.config.server.username,
            }

            if "authentication failed" in error_msg:
                error_details["szczegóły"] = "Błędna nazwa użytkownika lub hasło"
            elif "connection refused" in error_msg:
                error_details["szczegóły"] = (
                    "Port SSH (22) jest zablokowany lub usługa SSH nie jest uruchomiona"
                )
            elif "timed out" in error_msg:
                error_details["szczegóły"] = "Przekroczono limit czasu połączenia"
            else:
                error_details["szczegóły"] = str(e)

            self.cli.log("Błąd połączenia SSH", error_details, status="error")
            return False

    def close(self):
        if self.ssh:
            self.ssh.close()

    def find_json_files(self) -> List[str]:
        """Znajduje wszystkie pliki JSON, .config oraz config.js w katalogu apps na serwerze"""
        if not self.ssh:
            return []

        try:
            # Wykonaj komendę find na serwerze dla wszystkich typów plików
            cmd = f'find {self.config.server.apps_dir} -type f \( -name "*.json" -o -name "*.config" -o -name "config.js" \)'
            stdin, stdout, stderr = self.ssh.exec_command(cmd)

            # Pobierz wyniki
            files = stdout.read().decode().splitlines()

            # Filtruj pliki według rozszerzeń
            return [f for f in files if f.endswith((".json", ".config", "config.js"))]

        except Exception as e:
            self.cli.log(
                "Błąd podczas wyszukiwania plików",
                {"szczegóły": str(e)},
                status="error",
            )
            return []

    def copy_file(self, remote_path: str, local_path: Path) -> bool:
        """Kopiuje plik z serwera na lokalną maszynę"""
        if not self.ssh:
            return False

        try:
            sftp = self.ssh.open_sftp()
            local_path.parent.mkdir(parents=True, exist_ok=True)
            sftp.get(remote_path, str(local_path))
            sftp.close()
            return True
        except Exception as e:
            self.cli.log(
                "Błąd kopiowania pliku",
                {"plik": remote_path, "szczegóły": str(e)},
                status="error",
            )
            return False

    def update_file(self, local_path: Path, remote_path: str) -> bool:
        """Wysyła plik na serwer z obsługą sudo"""
        if not self.ssh:
            return False

        try:
            sftp = self.ssh.open_sftp()

            # Utwórz tymczasowy plik z unikalną nazwą
            temp_path = f"/tmp/{os.path.basename(remote_path)}.tmp"

            # Najpierw wyślij plik do katalogu tymczasowego
            sftp.put(str(local_path), temp_path)
            sftp.close()

            # Przygotuj komendę sudo do przeniesienia pliku
            sudo_command = (
                f"echo '{self.config.server.sudo_password}' | sudo -S mv {temp_path} {remote_path}"
            )

            # Wykonaj komendę sudo
            stdin, stdout, stderr = self.ssh.exec_command(sudo_command)

            # Sprawdź czy wystąpiły błędy
            error = stderr.read().decode().strip()
            if error and "password" not in error.lower():
                self.cli.log("Błąd sudo", {"szczegóły": error}, status="error")
                return False

            # Ustaw odpowiednie uprawnienia
            chmod_command = (
                f"echo '{self.config.server.sudo_password}' | sudo -S chmod 644 {remote_path}"
            )
            self.ssh.exec_command(chmod_command)

            return True

        except Exception as e:
            self.cli.log(
                "Błąd wysyłania pliku",
                {"plik": str(local_path), "szczegóły": str(e)},
                status="error",
            )
            return False


class DataManager:
    def __init__(self, config: AppConfig, cli: CLI):
        self.config = config
        self.cli = cli
        self.file_manager = FileManager()

    def get_server_path(self, server: str, is_cache: bool = False) -> Path:
        base = self.config.cache_dir if is_cache else Path("serwery")
        return base / server / "apps"

    def list_files(self, server: str, is_cache: bool = False) -> List[Path]:
        server_path = self.get_server_path(server, is_cache)
        if not server_path.exists():
            return []
        return list(server_path.rglob("*.json"))

    def copy_server_to_cache(self, server: str) -> bool:
        """Kopiuje całą strukturę katalogów serwera do cache"""

        source_path = Path("serwery") / server
        if not source_path.exists():
            return False

        cache_path = self.config.cache_dir / server
        try:
            # Usuń istniejący cache dla tego serwera
            if cache_path.exists():
                shutil.rmtree(cache_path)

            # Skopiuj całą strukturę
            shutil.copytree(source_path, cache_path)
            return True
        except Exception as e:
            self.cli.log(f"Błąd kopiowania do cache: {str(e)}", status="error")
            return False

    def delete_files(self, server: str, is_cache: bool = False) -> bool:
        """Usuwa wszystkie pliki dla danego serwera"""
        server_path = self.get_server_path(server, is_cache)
        if not server_path.exists():
            return False

        try:
            # Usuń cały katalog apps i jego zawartość
            import shutil

            shutil.rmtree(server_path)

            # Sprawdź czy katalog serwera jest pusty
            server_dir = server_path.parent
            if not any(server_dir.iterdir()):
                # Jeśli pusty, usuń również katalog serwera
                server_dir.rmdir()

            return True
        except Exception as e:
            self.cli.log(f"Błąd usuwania plików: {str(e)}", status="error")
            return False


class Application:
    def __init__(self):
        self.profiles_dir = Path("profiles")
        self.profiles_dir.mkdir(exist_ok=True)
        Path("serwery").mkdir(exist_ok=True)
        Path("_cache_/serwery").mkdir(parents=True, exist_ok=True)

        try:
            self.config = self.load_active_profile()
            self.cli = CLI(debug=self.config.debug)
            self.ssh = SSHManager(self.config, self.cli)  # Najpierw tworzymy SSH
            self.data_manager = DataManager(self.config, self.cli)  # Potem DataManager
            self.ssh_connected = False
        except Exception as e:
            print(f"Błąd inicjalizacji: {str(e)}")
            print("Tworzenie domyślnej konfiguracji...")
            self.create_default_profile()
            self.config = self.load_active_profile()
            self.cli = CLI(debug=self.config.debug)
            self.ssh = SSHManager(self.config, self.cli)
            self.data_manager = DataManager(self.config, self.cli)
            self.ssh_connected = False

    def create_default_profile(self):
        """Tworzy domyślny profil i aktywny profil"""
        default_config = {
            "debug": False,
            "server": {
                "ip": "10.1.1.1",
                "username": "user",
                "password": "ddd",
                "sudo_password": "ddd",
                "apps_dir": "/apps",
            },
        }

        # Upewnij się, że katalog profiles istnieje
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # Zapisz domyślny profil
        with open(self.profiles_dir / "default.json", "w") as f:
            json.dump(default_config, f, indent=4)

        # Zapisz również jako aktywny profil
        with open(self.profiles_dir / "active.json", "w") as f:
            json.dump(default_config, f, indent=4)

    def load_active_profile(self) -> AppConfig:
        """Ładuje aktywny profil lub tworzy domyślny"""
        try:
            active_profile = self.profiles_dir / "active.json"

            # Jeśli nie ma pliku active.json, stwórz domyślną konfigurację
            if not active_profile.exists():
                self.create_default_profile()

            # Wczytaj konfigurację
            with open(active_profile) as f:
                config_data = json.load(f)

            # Sprawdź czy istnieje sekcja server
            if "server" not in config_data:
                raise KeyError("Brak sekcji 'server' w konfiguracji")

            # Konwersja słownika na obiekt AppConfig
            server_config = ServerConfig(**config_data["server"])
            return AppConfig(
                debug=config_data.get("debug", False),
                server=server_config,
                cache_dir=Path("_cache_/serwery"),
            )
        except Exception as e:
            print(f"Błąd ładowania profilu: {str(e)}")
            print("Tworzenie domyślnej konfiguracji...")
            self.create_default_profile()
            return self.load_active_profile()

    def save_profile(self, name: str, config_data: dict):
        """Zapisuje profil połączenia"""
        try:
            profile_path = self.profiles_dir / f"{name}.json"
            with open(profile_path, "w") as f:
                json.dump(config_data, f, indent=4)

            # Aktualizuj aktywny profil
            active_path = self.profiles_dir / "active.json"
            with open(active_path, "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            self.cli.log(f"Błąd zapisywania profilu: {str(e)}", status="error")

    def connect(self):
        """Nawiązuje połączenie SSH z serwerem"""
        if self.ssh.connect():
            self.ssh_connected = True
            self.cli.log("Połączono z serwerem", status="success")
            return True
        else:
            self.ssh_connected = False
            self.cli.log("Nie można połączyć z serwerem", status="error")
            return False

    def manage_connection(self):
        """Zarządza profilem połączenia"""
        self.cli.log("\nAktualny profil połączenia:")
        self.cli.log(f"Server: {self.config.server.ip}")
        self.cli.log(f"Username: {self.config.server.username}")
        self.cli.log(f"Apps dir: {self.config.server.apps_dir}")
        self.cli.log(
            f"Status SSH: {'✅ Połączono' if self.ssh_connected else '❌ Brak połączenia'}"
        )

        if not self.cli.confirm("\nCzy chcesz zmienić konfigurację?"):
            return

        try:
            # Pobierz nowe dane
            config_data = {
                "debug": self.config.debug,
                "server": {
                    "ip": Prompt.ask("IP serwera", default=self.config.server.ip),
                    "username": Prompt.ask(
                        "Nazwa użytkownika", default=self.config.server.username
                    ),
                    "password": Prompt.ask("Hasło", password=True),
                    "sudo_password": Prompt.ask("Hasło sudo", password=True),
                    "apps_dir": Prompt.ask(
                        "Katalog aplikacji", default=self.config.server.apps_dir
                    ),
                },
            }

            # Zapisz tylko do active.json
            active_path = self.profiles_dir / "active.json"
            with open(active_path, "w") as f:
                json.dump(config_data, f, indent=4)

            # Przeładuj konfigurację
            server_config = ServerConfig(**config_data["server"])
            self.config = AppConfig(
                debug=config_data["debug"],
                server=server_config,
                cache_dir=Path("_cache_/serwery"),
            )
            self.ssh = SSHManager(self.config, self.cli)

            # Spróbuj połączyć
            if self.ssh.connect():
                self.ssh_connected = True
                self.cli.log("Połączono z serwerem", status="success")
            else:
                self.ssh_connected = False
                self.cli.log("Nie można połączyć z serwerem", status="error")
        except Exception as e:
            self.cli.log(f"Błąd konfiguracji: {str(e)}", status="error")

    def backup_files(self):
        if self.config.debug:
            self.cli.log("Operacja niedostępna w trybie debug", status="warning")
            return

        with Progress(SpinnerColumn(), *Progress.get_default_columns()) as progress:
            json_files = self.ssh.find_json_files()
            if not json_files:
                self.cli.log("Nie znaleziono plików JSON")
                return

            task = progress.add_task("Kopiowanie plików...", total=len(json_files))

            for remote_file in json_files:
                relative_path = remote_file.replace("/apps/", "")
                local_path = Path(f"serwery/{self.config.server.ip}/apps") / relative_path
                local_path.parent.mkdir(parents=True, exist_ok=True)

                if self.ssh.copy_file(remote_file, local_path):
                    self.cli.log("Skopiowano", {"plik": str(local_path)})
                else:
                    self.cli.log("Błąd kopiowania", {"plik": remote_file}, status="error")

                progress.advance(task)

            # Po pobraniu wszystkich plików, skopiuj do cache
            if self.data_manager.copy_server_to_cache(self.config.server.ip):
                self.cli.log("Zaktualizowano cache", status="success")
            else:
                self.cli.log("Błąd aktualizacji cache", status="error")

    def check_differences(self) -> bool:
        local_base = Path(f"serwery/{self.config.server.ip}/apps")
        cache_base = self.config.cache_dir / self.config.server.ip / "apps"

        if not local_base.exists():
            self.cli.log("Brak lokalnych plików", status="error")
            return False

        if not cache_base.exists():
            self.cli.log("Brak plików w cache", status="error")
            return False

        # Zbierz wszystkie pliki JSON z obu lokalizacji
        local_files = set(str(p.relative_to(local_base)) for p in local_base.rglob("*.json"))
        cache_files = set(str(p.relative_to(cache_base)) for p in cache_base.rglob("*.json"))

        all_files = sorted(local_files | cache_files)
        differences = {}

        with Progress() as progress:
            task = progress.add_task("Sprawdzanie różnic...", total=len(all_files))

            for relative_path in all_files:
                local_path = local_base / relative_path
                cache_path = cache_base / relative_path

                if local_path.exists() and cache_path.exists():
                    if not self.data_manager.file_manager.compare_files(local_path, cache_path):
                        differences[relative_path] = "zmieniony"
                elif local_path.exists():
                    differences[relative_path] = "tylko_lokalnie"
                elif cache_path.exists():
                    differences[relative_path] = "tylko_w_cache"

                progress.advance(task)

        if differences:
            self.cli.log("\nZnalezione różnice:")
            for file, status in differences.items():
                status_icon = {
                    "zmieniony": "🔄",
                    "tylko_lokalnie": "➕",
                    "tylko_w_cache": "❌",
                }.get(status, "❓")
                self.cli.log(f"{status_icon} {file}")

            if self.cli.confirm("\nCzy pokazać szczegóły różnic?"):
                for file, status in differences.items():
                    if status == "zmieniony":
                        self.cli.log(f"\nRóżnice w pliku {file}:")
                        cache_path = cache_base / file
                        local_path = local_base / file
                        self.cli.show_file_diff(cache_path, local_path)
            return True

        self.cli.log("Brak różnic w konfiguracji", status="success")
        return False

    def update_files(self):
        if self.config.debug:
            self.cli.log("Operacja niedostępna w trybie debug", status="warning")
            return

        local_base = Path(f"serwery/{self.config.server.ip}/apps")
        cache_base = self.config.cache_dir / self.config.server.ip / "apps"

        if not local_base.exists():
            self.cli.log("Brak lokalnych plików", status="error")
            return

        if not cache_base.exists():
            self.cli.log("Brak plików w cache", status="error")
            return

        # Znajdź zmienione pliki
        changed_files = []
        for local_path in local_base.rglob("*.json"):
            relative_path = local_path.relative_to(local_base)
            cache_path = cache_base / relative_path
            remote_file = f"/apps/{relative_path}"

            if not cache_path.exists() or not self.data_manager.file_manager.compare_files(
                local_path, cache_path
            ):
                changed_files.append((remote_file, local_path, cache_path))

        if not changed_files:
            self.cli.log("Brak plików do wysłania", status="success")
            return

        # Pokaż listę zmienionych plików
        self.cli.log(f"\nZnaleziono {len(changed_files)} zmienionych plików:")
        for _, local_path, _ in changed_files:
            self.cli.log(f"- {local_path.name}")

        if not self.cli.confirm("\nCzy chcesz kontynuować wysyłanie zmienionych plików?"):
            return

        # Zapytaj o tryb wysyłania
        send_all = False
        if self.cli.confirm("\nCzy chcesz wysłać wszystkie pliki bez potwierdzania?"):
            send_all = True

        # Zapytaj o każdy plik
        files_updated = False
        for remote_file, local_path, cache_path in changed_files:
            self.cli.log(f"\n[cyan]Plik: {local_path.name}[/cyan]")

            if not send_all:
                if self.cli.confirm("Czy pokazać różnice?"):
                    if cache_path.exists():
                        self.cli.show_file_diff(cache_path, local_path)
                    else:
                        self.cli.log("(Nowy plik)")

                # Pokazujemy dostępne opcje
                self.cli.show_file_options()

                choice = Prompt.ask("Co zrobić?", choices=["w", "p", "s", "n"], default="n")

                if choice == "p":
                    self.cli.log("Przerwano wysyłanie", status="warning")
                    break
                elif choice == "s":
                    self.cli.log("Wysyłanie wszystkich pozostałych plików", status="info")
                    send_all = True
                elif choice == "n":
                    self.cli.log("Pominięto plik", status="info")
                    continue

            # Wysyłanie pliku
            if send_all or choice == "w":
                if self.ssh.update_file(local_path, remote_file):
                    self.cli.log(
                        f"Zaktualizowano plik {local_path.name} na serwerze",
                        status="success",
                    )
                    files_updated = True
                else:
                    self.cli.log(f"Błąd aktualizacji pliku {local_path.name}", status="error")
                    if self.cli.confirm("\nCzy przerwać wysyłanie?"):
                        break

        # Aktualizuj cache tylko jeśli coś zostało wysłane
        if files_updated and self.cli.confirm("\nCzy pobrać najnowszą konfigurację do cache?"):
            self.backup_files()

    def update_cache(self, source_path: Path):
        """Ta metoda nie jest już potrzebna, używamy copy_server_to_cache"""
        pass

    def get_available_servers(self) -> List[str]:
        """Zwraca listę dostępnych serwerów z obu lokalizacji"""
        servers = set()

        # Sprawdź serwery w cache
        if self.config.cache_dir.exists():
            servers.update(path.name for path in self.config.cache_dir.glob("*") if path.is_dir())

        # Sprawdź serwery lokalne
        servers.update(path.name for path in Path("serwery").glob("*") if path.is_dir())

        return sorted(list(servers))

    def get_user_choice(self, max_choice: int) -> Optional[int]:
        """Pobiera wybór użytkownika z możliwością wyjścia"""
        choices = [str(i) for i in range(1, max_choice + 1)]
        choices.append("0")
        choice = Prompt.ask("Wybierz numer (0 aby wrócić)", choices=choices)
        return None if choice == "0" else int(choice)

    def handle_file_deletion(self, is_cache: bool = False):
        operation = "cache" if is_cache else "lokalnych"
        base_path = self.config.cache_dir if is_cache else Path("serwery")

        if not base_path.exists() or not any(base_path.iterdir()):
            self.cli.log(f"Brak plików {operation}", status="warning")
            return

        # Pobierz tylko te serwery, które faktycznie istnieją w danej lokalizacji
        servers = []
        for path in base_path.glob("*"):
            if path.is_dir() and (path / "apps").exists():
                servers.append(path.name)

        if not servers:
            self.cli.log(f"Brak serwerów z plikami {operation}", status="warning")
            return

        self.cli.log("Dostępne serwery:")
        for idx, server in enumerate(servers, 1):
            self.cli.log(f"{idx}. {server}")
        self.cli.log("0. Wróć do menu")

        choice = self.get_user_choice(len(servers))
        if choice is None:
            return

        server = servers[choice - 1]
        files = self.data_manager.list_files(server, is_cache)

        if not files:
            self.cli.log(f"Brak plików {operation} dla tego serwera", status="warning")
            return

        self.cli.log(f"\nZnalezione pliki {operation} dla serwera {server}:")
        for file in files:
            relative_path = file.relative_to(self.data_manager.get_server_path(server, is_cache))
            opposite_path = self.data_manager.get_server_path(server, not is_cache) / relative_path
            status = "✅" if opposite_path.exists() else "❌"
            self.cli.log(f"{status} {relative_path}")

        if not self.cli.confirm(
            f"\nCzy na pewno chcesz usunąć wszystkie pliki {operation}? (N aby wrócić)"
        ):
            return

        if self.data_manager.delete_files(server, is_cache):
            self.cli.log(
                f"Usunięto wszystkie pliki {operation} dla serwera {server}",
                status="success",
            )

    def manage_profiles(self):
        """Zarządza profilami połączeń"""
        while True:
            # Pobierz listę profili
            profiles = [
                p.stem
                for p in self.profiles_dir.glob("*.json")
                if p.stem not in ["active", "default"]
            ]

            self.cli.log("\nDostępne profile:")
            self.cli.log("1. Utwórz nowy profil")
            for idx, profile in enumerate(profiles, 2):
                self.cli.log(f"{idx}. {profile}")
            self.cli.log("0. Powrót do menu")

            choice = self.get_user_choice(len(profiles) + 1)
            if choice is None:
                break

            if choice == 1:
                # Tworzenie nowego profilu
                try:
                    # Użyj aktualnej konfiguracji jako domyślnej
                    config_data = {
                        "debug": self.config.debug,
                        "server": {
                            "ip": Prompt.ask("IP serwera", default=self.config.server.ip),
                            "username": Prompt.ask(
                                "Nazwa użytkownika", default=self.config.server.username
                            ),
                            "password": Prompt.ask("Hasło", password=True),
                            "sudo_password": Prompt.ask("Hasło sudo", password=True),
                            "apps_dir": Prompt.ask(
                                "Katalog aplikacji", default=self.config.server.apps_dir
                            ),
                        },
                    }

                    profile_name = Prompt.ask("Nazwa profilu")
                    if profile_name in ["active", "default"]:
                        self.cli.log("Nazwa profilu zarezerwowana", status="error")
                        continue

                    self.save_profile(profile_name, config_data)
                    self.cli.log(f"Utworzono profil {profile_name}", status="success")

                    if self.cli.confirm("Czy chcesz aktywować ten profil?"):
                        self.activate_profile(profile_name)

                except Exception as e:
                    self.cli.log(f"Błąd tworzenia profilu: {str(e)}", status="error")
            else:
                # Wybór istniejącego profilu
                profile_name = profiles[choice - 2]
                self.cli.log(f"\nProfil: {profile_name}")
                self.cli.log("1. Aktywuj profil")
                self.cli.log("2. Usuń profil")
                self.cli.log("0. Powrót")

                subchoice = self.get_user_choice(2)
                if subchoice == 1:
                    self.activate_profile(profile_name)
                elif subchoice == 2:
                    if self.cli.confirm(f"Czy na pewno chcesz usunąć profil {profile_name}?"):
                        try:
                            (self.profiles_dir / f"{profile_name}.json").unlink()
                            self.cli.log(f"Usunięto profil {profile_name}", status="success")
                        except Exception as e:
                            self.cli.log(f"Błąd usuwania profilu: {str(e)}", status="error")

    def activate_profile(self, profile_name: str):
        """Aktywuje wybrany profil"""
        try:
            # Wczytaj wybrany profil
            with open(self.profiles_dir / f"{profile_name}.json") as f:
                config_data = json.load(f)

            # Zapisz jako aktywny
            self.save_profile("active", config_data)

            # Przeładuj konfigurację
            self.config = self.load_active_profile()
            self.ssh = SSHManager(self.config, self.cli)

            # Spróbuj połączyć
            if self.ssh.connect():
                self.ssh_connected = True
                self.cli.log("Połączono z serwerem", status="success")
            else:
                self.ssh_connected = False
                self.cli.log("Nie można połączyć z serwerem", status="error")

            self.cli.log(f"Aktywowano profil {profile_name}", status="success")
        except Exception as e:
            self.cli.log(f"Błąd aktywacji profilu: {str(e)}", status="error")

    def run(self):
        self.cli.show_header("Program do backupu plików JSON")

        # Próba połączenia SSH
        if not self.config.debug:
            if self.ssh.connect():
                self.ssh_connected = True
                self.cli.log("Połączono z serwerem", status="success")
            else:
                self.ssh_connected = False
                self.cli.log("Nie można połączyć z serwerem", status="error")

        while True:
            choice = self.cli.show_menu(ssh_connected=self.ssh_connected)

            if choice in ["1", "2"] and not self.ssh_connected and not self.config.debug:
                self.cli.log("Brak połączenia z serwerem", status="error")
                continue

            if choice == "1":
                self.backup_files()
            elif choice == "2":
                self.update_files()
            elif choice == "3":
                self.check_differences()
            elif choice == "4":
                self.handle_file_deletion(is_cache=True)
            elif choice == "5":
                self.handle_file_deletion(is_cache=False)
            elif choice == "6":
                self.manage_connection()
            elif choice == "7":
                self.manage_profiles()
            elif choice == "0":
                if self.ssh_connected:
                    self.cli.log("Zamykanie połączenia...")
                    self.ssh.close()
                break

            time.sleep(1)


if __name__ == "__main__":
    app = Application()
    app.run()
