import datetime
import difflib
import hashlib
import os
import tempfile
from typing import List, Optional, Tuple, Union

from ..backend.bash_backend import BashBackend
from ..backend.ssh_backend import SshBackend
from .ssh_connecticer import SSHConnecticer


class FileTracer:
    """
    Klasa implementująca operacje na plikach, szczególnie przydatne
    przy zarządzaniu plikami konfiguracyjnymi na zdalnych serwerach.
    """

    def __init__(self, remote_backend: Optional[Union[SshBackend, SSHConnecticer]] = None):
        """
        Inicjalizuje FileTracer.

        Args:
            remote_backend: Opcjonalny backend dla operacji zdalnych
        """
        self.local_backend = BashBackend()
        self.remote_backend = remote_backend
        self._backup_dir = os.path.join(os.path.expanduser("~"), ".mancer", "backups")
        os.makedirs(self._backup_dir, exist_ok=True)

    def compare_files(
        self,
        file1_path: str,
        file2_path: str,
        is_file1_remote: bool = False,
        is_file2_remote: bool = False,
    ) -> Tuple[bool, List[str]]:
        """
        Porównuje zawartość dwóch plików.

        Args:
            file1_path: Ścieżka do pierwszego pliku
            file2_path: Ścieżka do drugiego pliku
            is_file1_remote: Czy pierwszy plik jest na zdalnym serwerze
            is_file2_remote: Czy drugi plik jest na zdalnym serwerze

        Returns:
            Tuple[bool, List[str]]: (Czy pliki są identyczne, Lista różnic)
        """
        # Pobierz zawartość plików
        content1 = self._get_file_content(file1_path, is_remote=is_file1_remote)
        content2 = self._get_file_content(file2_path, is_remote=is_file2_remote)

        # Porównaj zawartość
        if content1 == content2:
            return True, []

        # Generuj różnice
        differ = difflib.Differ()
        diff = list(differ.compare(content1.splitlines(), content2.splitlines()))

        return False, diff

    def backup_file(self, file_path: str, is_remote: bool = False, suffix: Optional[str] = None) -> str:
        """
        Tworzy kopię zapasową pliku.

        Args:
            file_path: Ścieżka do pliku
            is_remote: Czy plik jest na zdalnym serwerze
            suffix: Opcjonalny sufiks do nazwy pliku backupu

        Returns:
            str: Ścieżka do pliku backupu
        """
        # Pobierz nazwę pliku z pełnej ścieżki
        filename = os.path.basename(file_path)

        # Utwórz nazwę pliku backupu z datą i opcjonalnym sufiksem
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if suffix:
            backup_filename = f"{filename}.{timestamp}.{suffix}.bak"
        else:
            backup_filename = f"{filename}.{timestamp}.bak"

        backup_path = os.path.join(self._backup_dir, backup_filename)

        # Pobierz zawartość pliku
        content = self._get_file_content(file_path, is_remote)

        # Zapisz backup
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)

        return backup_path

    def restore_from_backup(
        self,
        backup_path: str,
        destination_path: str,
        is_destination_remote: bool = False,
    ) -> bool:
        """
        Przywraca plik z backupu.

        Args:
            backup_path: Ścieżka do pliku backupu
            destination_path: Ścieżka docelowa
            is_destination_remote: Czy cel jest na zdalnym serwerze

        Returns:
            bool: Czy operacja się powiodła
        """
        # Sprawdź czy backup istnieje
        if not os.path.exists(backup_path):
            return False

        # Odczytaj zawartość backupu
        with open(backup_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Zapisz do docelowego pliku
        return self._set_file_content(destination_path, content, is_destination_remote)

    def calculate_file_hash(self, file_path: str, is_remote: bool = False) -> str:
        """
        Oblicza hash SHA-256 zawartości pliku.

        Args:
            file_path: Ścieżka do pliku
            is_remote: Czy plik jest na zdalnym serwerze

        Returns:
            str: Hash SHA-256 zawartości pliku
        """
        # Pobierz zawartość pliku
        content = self._get_file_content(file_path, is_remote)

        # Oblicz hash
        hasher = hashlib.sha256()
        hasher.update(content.encode("utf-8"))

        return hasher.hexdigest()

    def create_temp_file(
        self,
        content: Optional[str] = None,
        prefix: str = "mancer_",
        suffix: str = ".tmp",
    ) -> str:
        """
        Tworzy tymczasowy plik lokalnie.

        Args:
            content: Opcjonalna zawartość pliku
            prefix: Prefiks nazwy pliku
            suffix: Sufiks nazwy pliku

        Returns:
            str: Ścieżka do utworzonego pliku
        """
        # Utwórz tymczasowy plik
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)

        try:
            # Zapisz zawartość jeśli podana
            if content is not None:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                os.close(fd)
        except Exception:
            os.close(fd)
            raise

        return temp_path

    def list_backups(self, original_filename: Optional[str] = None) -> List[str]:
        """
        Listuje dostępne backupy.

        Args:
            original_filename: Opcjonalna nazwa oryginalnego pliku do filtrowania

        Returns:
            List[str]: Lista ścieżek do plików backupów
        """
        backups = []

        for filename in os.listdir(self._backup_dir):
            filepath = os.path.join(self._backup_dir, filename)
            if os.path.isfile(filepath) and filename.endswith(".bak"):
                if original_filename is None or filename.startswith(original_filename + "."):
                    backups.append(filepath)

        # Sortuj po dacie utworzenia (najnowsze najpierw)
        backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        return backups

    def _get_file_content(self, file_path: str, is_remote: bool) -> str:
        """
        Pobiera zawartość pliku lokalnego lub zdalnego.

        Args:
            file_path: Ścieżka do pliku
            is_remote: Czy plik jest na zdalnym serwerze

        Returns:
            str: Zawartość pliku
        """
        if is_remote:
            if not self.remote_backend:
                raise ValueError("Remote backend not configured")

            # Użyj komendy cat do pobrania zawartości pliku
            result = self.remote_backend.execute_command(f"cat {file_path}")

            if not result.success:
                raise IOError(f"Failed to read remote file: {result.error_message}")

            return result.raw_output
        # Bezpośredni odczyt pliku lokalnego
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read local file: {str(e)}")

    def _set_file_content(self, file_path: str, content: str, is_remote: bool) -> bool:
        """
        Zapisuje zawartość do pliku lokalnego lub zdalnego.

        Args:
            file_path: Ścieżka do pliku
            content: Zawartość do zapisania
            is_remote: Czy plik jest na zdalnym serwerze

        Returns:
            bool: Czy operacja się powiodła
        """
        if is_remote:
            if not self.remote_backend:
                raise ValueError("Remote backend not configured")

            # Zapisujemy do pliku tymczasowego
            temp_file = self.create_temp_file(content)

            # Wysyłamy plik na serwer
            if isinstance(self.remote_backend, SSHConnecticer):
                result = self.remote_backend.upload_file(temp_file, file_path)
            else:
                # Użycie standardowej komendy SCP
                host_part = self.remote_backend.hostname
                if self.remote_backend.username:
                    host_part = f"{self.remote_backend.username}@{host_part}"

                scp_cmd = f"scp {temp_file} {host_part}:{file_path}"
                result = self.local_backend.execute_command(scp_cmd)

            # Usuń tymczasowy plik
            os.unlink(temp_file)

            return result.success
        # Bezpośredni zapis do pliku lokalnego
        try:
            # Upewnij się, że katalog istnieje
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False
