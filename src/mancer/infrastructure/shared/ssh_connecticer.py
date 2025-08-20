import os
from typing import Dict, Optional

from ...domain.model.command_result import CommandResult
from ..backend.ssh_backend import SshBackend


class SSHConnecticer(SshBackend):
    """
    Rozszerzenie SshBackend o dodatkowe funkcje zarządzania połączeniami SSH.
    Zapewnia zaawansowane funkcje zarządzania sesjami, transferem plików i monitorowaniem połączeń.
    """
    
    def __init__(self, hostname: str = "", username: Optional[str] = None, 
                port: int = 22, key_filename: Optional[str] = None, 
                password: Optional[str] = None, passphrase: Optional[str] = None,
                allow_agent: bool = True, look_for_keys: bool = True, 
                compress: bool = False, timeout: Optional[int] = None,
                gssapi_auth: bool = False, gssapi_kex: bool = False, 
                gssapi_delegate_creds: bool = False,
                ssh_options: Optional[Dict[str, str]] = None,
                session_name: Optional[str] = None):
        """
        Inicjalizuje SSHConnecticer.
        
        Args:
            Wszystkie parametry SshBackend oraz:
            session_name: Opcjonalna nazwa sesji dla łatwiejszej identyfikacji
        """
        super().__init__(
            hostname=hostname, username=username, port=port, 
            key_filename=key_filename, password=password, 
            passphrase=passphrase, allow_agent=allow_agent,
            look_for_keys=look_for_keys, compress=compress,
            timeout=timeout, gssapi_auth=gssapi_auth,
            gssapi_kex=gssapi_kex, gssapi_delegate_creds=gssapi_delegate_creds,
            ssh_options=ssh_options
        )
        self.session_name = session_name or f"{username}@{hostname}:{port}"
        self._connection_alive = False
        self._last_error = None
    
    def check_connection(self) -> bool:
        """
        Sprawdza, czy połączenie SSH jest aktywne.
        
        Returns:
            bool: True jeśli połączenie jest aktywne, False w przeciwnym przypadku
        """
        try:
            result = self.execute_command("echo Connection test")
            self._connection_alive = result.success
            return self._connection_alive
        except Exception as e:
            self._last_error = str(e)
            self._connection_alive = False
            return False
    
    def upload_file(self, local_path: str, remote_path: str, 
                  create_dirs: bool = True) -> CommandResult:
        """
        Wysyła plik na zdalny serwer poprzez SCP.
        
        Args:
            local_path: Ścieżka do pliku lokalnego
            remote_path: Ścieżka docelowa na zdalnym serwerze
            create_dirs: Czy tworzyć katalogi docelowe, jeśli nie istnieją
            
        Returns:
            CommandResult: Wynik operacji
        """
        # Sprawdzenie czy plik lokalny istnieje
        if not os.path.exists(local_path):
            return CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=1,
                error_message=f"Local file not found: {local_path}"
            )
        
        # Tworzenie katalogów docelowych jeśli potrzeba
        if create_dirs:
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                mkdir_cmd = f"mkdir -p {remote_dir}"
                self.execute_command(mkdir_cmd)
        
        # Przygotowanie komendy SCP
        scp_command = ["scp"]
        
        # Dodanie opcji SSH do komendy SCP
        if self.port != 22:
            scp_command.extend(["-P", str(self.port)])
        
        if self.key_filename:
            scp_command.extend(["-i", self.key_filename])
        
        # Lokalna i zdalna ścieżka
        scp_command.append(local_path)
        
        target = self.hostname
        if self.username:
            target = f"{self.username}@{self.hostname}"
        
        scp_command.append(f"{target}:{remote_path}")
        
        try:
            # Wykonanie komendy SCP jako podzielne części
            cmd = " ".join(scp_command)
            if self.password:
                cmd = f"sshpass -p '{self.password}' {cmd}"
                
            # Wykonujemy jako komendę lokalną
            result = super().execute(cmd)
            exit_code, stdout, stderr = result
            
            # Sprawdzenie wyniku
            success = exit_code == 0
            
            return CommandResult(
                raw_output=stdout,
                success=success,
                structured_output=[],
                exit_code=exit_code,
                error_message=stderr if not success else ""
            )
        except Exception as e:
            return CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=-1,
                error_message=f"Error uploading file: {str(e)}"
            )
    
    def download_file(self, remote_path: str, local_path: str, 
                    create_dirs: bool = True) -> CommandResult:
        """
        Pobiera plik ze zdalnego serwera poprzez SCP.
        
        Args:
            remote_path: Ścieżka do pliku na zdalnym serwerze
            local_path: Ścieżka docelowa na lokalnym komputerze
            create_dirs: Czy tworzyć katalogi docelowe, jeśli nie istnieją
            
        Returns:
            CommandResult: Wynik operacji
        """
        # Tworzenie katalogów docelowych jeśli potrzeba
        if create_dirs:
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
        
        # Przygotowanie komendy SCP
        scp_command = ["scp"]
        
        # Dodanie opcji SSH do komendy SCP
        if self.port != 22:
            scp_command.extend(["-P", str(self.port)])
        
        if self.key_filename:
            scp_command.extend(["-i", self.key_filename])
        
        # Zdalna i lokalna ścieżka
        target = self.hostname
        if self.username:
            target = f"{self.username}@{self.hostname}"
        
        scp_command.append(f"{target}:{remote_path}")
        scp_command.append(local_path)
        
        try:
            # Wykonanie komendy SCP jako podzielne części
            cmd = " ".join(scp_command)
            if self.password:
                cmd = f"sshpass -p '{self.password}' {cmd}"
                
            # Wykonujemy jako komendę lokalną
            result = super().execute(cmd)
            exit_code, stdout, stderr = result
            
            # Sprawdzenie wyniku
            success = exit_code == 0
            
            return CommandResult(
                raw_output=stdout,
                success=success,
                structured_output=[],
                exit_code=exit_code,
                error_message=stderr if not success else ""
            )
        except Exception as e:
            return CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=-1,
                error_message=f"Error downloading file: {str(e)}"
            )
    
    def execute_command_with_timeout(self, command: str, 
                                  timeout: int = 30, 
                                  working_dir: Optional[str] = None, 
                                  env_vars: Optional[Dict[str, str]] = None) -> CommandResult:
        """
        Wykonuje komendę z określonym timeoutem.
        
        Args:
            command: Komenda do wykonania
            timeout: Timeout w sekundach
            working_dir: Katalog roboczy
            env_vars: Zmienne środowiskowe
            
        Returns:
            CommandResult: Wynik operacji
        """
        # Ustawienie opcji timeout dla SSH
        original_timeout = self.timeout
        original_ssh_options = self.ssh_options.copy() if self.ssh_options else {}
        
        try:
            # Ustawienie timeoutu
            self.timeout = timeout
            if not self.ssh_options:
                self.ssh_options = {}
            self.ssh_options["ConnectTimeout"] = str(timeout)
            
            # Wykonanie komendy
            return self.execute_command(command, working_dir, env_vars)
        finally:
            # Przywrócenie oryginalnych opcji
            self.timeout = original_timeout
            self.ssh_options = original_ssh_options
    
    def get_last_error(self) -> Optional[str]:
        """Zwraca ostatni błąd połączenia"""
        return self._last_error
    
    def is_alive(self) -> bool:
        """Zwraca czy połączenie jest aktywne bez sprawdzania"""
        return self._connection_alive 