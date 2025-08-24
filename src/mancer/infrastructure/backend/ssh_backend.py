import shlex
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from ...domain.interface.backend_interface import BackendInterface
from ...domain.model.command_result import CommandResult


@dataclass
class SSHSession:
    """Reprezentuje sesję SSH"""

    id: str
    hostname: str
    username: str
    port: int
    status: str = "disconnected"  # connected, disconnected, connecting, error
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    connection_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SCPTransfer:
    """Reprezentuje transfer pliku przez SCP"""

    id: str
    source: str
    destination: str
    direction: str  # upload, download
    status: str = "pending"  # pending, transferring, completed, failed
    progress: float = 0.0
    bytes_transferred: int = 0
    total_bytes: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None


class SshBackend(BackendInterface):
    """Backend executing commands over SSH on a remote host with session management and SCP support."""

    def __init__(
        self,
        hostname: str = "",
        username: Optional[str] = None,
        port: int = 22,
        key_filename: Optional[str] = None,
        password: Optional[str] = None,
        passphrase: Optional[str] = None,
        allow_agent: bool = True,
        look_for_keys: bool = True,
        compress: bool = False,
        timeout: Optional[int] = None,
        gssapi_auth: bool = False,
        gssapi_kex: bool = False,
        gssapi_delegate_creds: bool = False,
        ssh_options: Optional[Dict[str, str]] = None,
        proxy_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the SSH backend.

        Args:
            hostname: Remote host address or IP.
            username: SSH user.
            port: SSH port (default 22).
            key_filename: Path to private key file.
            password: SSH password (not recommended; prefer keys).
            passphrase: Passphrase for the private key.
            allow_agent: Whether to use SSH agent authentication.
            look_for_keys: Whether to look for keys in ~/.ssh.
            compress: Whether to enable compression.
            timeout: Connection timeout in seconds.
            gssapi_auth: Enable GSSAPI (Kerberos) authentication.
            gssapi_kex: Enable GSSAPI key exchange.
            gssapi_delegate_creds: Delegate GSSAPI credentials.
            ssh_options: Additional SSH options as a dictionary.
            proxy_config: SSH proxy configuration.
        """
        self.hostname = hostname
        self.username = username
        self.port = port
        self.key_filename = key_filename
        self.password = password
        self.passphrase = passphrase
        self.allow_agent = allow_agent
        self.look_for_keys = look_for_keys
        self.compress = compress
        self.timeout = timeout
        self.gssapi_auth = gssapi_auth
        self.gssapi_kex = gssapi_kex
        self.gssapi_delegate_creds = gssapi_delegate_creds
        self.ssh_options = ssh_options or {}
        self.proxy_config = proxy_config or {}

        # Session management
        self.sessions: Dict[str, SSHSession] = {}
        self.active_session: Optional[str] = None
        self.session_lock = threading.Lock()

        # SCP transfers
        self.transfers: Dict[str, SCPTransfer] = {}
        self.transfer_lock = threading.Lock()

        # Fingerprint handling
        self.fingerprint_callback: Optional[Callable] = None
        self.fingerprint_callback_lock = threading.Lock()

    def create_session(self, session_id: str, **kwargs) -> SSHSession:
        """Tworzy nową sesję SSH"""
        with self.session_lock:
            # Usuń fingerprint_callback z kwargs żeby nie trafiło do SSHSession
            if "fingerprint_callback" in kwargs:
                del kwargs["fingerprint_callback"]

            # Wyciągnij podstawowe parametry z kwargs
            hostname = kwargs.pop("hostname", self.hostname)
            username = kwargs.pop("username", self.username)
            port = kwargs.pop("port", self.port)

            session = SSHSession(id=session_id, hostname=hostname, username=username, port=port)
            self.sessions[session_id] = session
            return session

    def connect_session(self, session_id: str) -> bool:
        """Łączy sesję SSH"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        session.status = "connecting"

        try:
            # Test connection
            test_result = self.execute_command("echo 'Connection test'", session_id=session_id)
            if test_result.success:
                session.status = "connected"
                session.last_activity = datetime.now()
                self.active_session = session_id
                return True
            else:
                session.status = "error"
                return False
        except Exception:
            session.status = "error"
            return False

    def disconnect_session(self, session_id: str) -> bool:
        """Rozłącza sesję SSH"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        session.status = "disconnected"

        if self.active_session == session_id:
            self.active_session = None

        return True

    def set_fingerprint_callback(self, callback: Callable):
        """Ustawia callback do obsługi fingerprint prompts"""
        with self.fingerprint_callback_lock:
            self.fingerprint_callback = callback

    def get_fingerprint_callback(self) -> Optional[Callable]:
        """Pobiera aktualny fingerprint callback"""
        with self.fingerprint_callback_lock:
            return self.fingerprint_callback

    def get_session_status(self, session_id: str) -> Optional[str]:
        """Pobiera status sesji"""
        if session_id in self.sessions:
            return self.sessions[session_id].status
        return None

    def list_sessions(self) -> List[SSHSession]:
        """Listuje wszystkie sesje"""
        with self.session_lock:
            return list(self.sessions.values())

    def switch_session(self, session_id: str) -> bool:
        """Przełącza na inną sesję"""
        if session_id in self.sessions and self.sessions[session_id].status == "connected":
            self.active_session = session_id
            return True
        return False

    def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> CommandResult:
        """Execute a command over SSH on the remote host."""
        # Użyj aktywnej sesji lub podanej
        target_session = session_id or self.active_session
        if not target_session or target_session not in self.sessions:
            return CommandResult(
                success=False,
                raw_output="",
                structured_output=[],
                exit_code=1,
                error_message="No active SSH session",
            )

        session = self.sessions[target_session]
        if session.status != "connected":
            return CommandResult(
                success=False,
                raw_output="",
                structured_output=[],
                exit_code=1,
                error_message=f"Session {session_id} is not connected",
            )

        # Aktualizuj aktywność sesji
        session.last_activity = datetime.now()

        # Budujemy komendę SSH
        ssh_command = ["ssh"]

        # Dodajemy opcje SSH
        if session.port != 22:
            ssh_command.extend(["-p", str(session.port)])

        # Obsługa różnych metod uwierzytelniania

        # 1. Klucz prywatny
        if self.key_filename:
            ssh_command.extend(["-i", self.key_filename])

        # 2. Używanie tylko podanych tożsamości
        if not self.look_for_keys:
            ssh_command.extend(["-o", "IdentitiesOnly=yes"])

        # 3. Agent SSH
        if self.allow_agent:
            ssh_command.extend(["-o", "ForwardAgent=yes"])

        # 4. Kompresja
        if self.compress:
            ssh_command.append("-C")

        # 5. Timeout
        if self.timeout:
            ssh_command.extend(["-o", f"ConnectTimeout={self.timeout}"])

        # 6. Uwierzytelnianie GSSAPI (Kerberos)
        if self.gssapi_auth:
            ssh_command.extend(["-o", "GSSAPIAuthentication=yes"])

        # 7. Proxy support
        if self.proxy_config:
            ssh_command.extend(self._build_proxy_options())

        # Dodajemy opcje SSH z ssh_options
        for key, value in self.ssh_options.items():
            ssh_command.extend(["-o", f"{key}={value}"])

        # Dodajemy hostname i username
        if session.username:
            ssh_command.append(f"{session.username}@{session.hostname}")
        else:
            ssh_command.append(session.hostname)

        # Dodajemy komendę
        ssh_command.append(command)

        try:
            # Sprawdź czy mamy fingerprint callback
            fingerprint_callback = self.get_fingerprint_callback()

            if fingerprint_callback:
                # Użyj interaktywnej obsługi fingerprinta
                return self._execute_with_fingerprint_handling(
                    ssh_command, working_dir, env_vars, fingerprint_callback
                )
            else:
                # Standardowe wykonanie SSH
                result = subprocess.run(
                    ssh_command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout or 30,
                    cwd=working_dir,
                    env=env_vars,
                )

                return CommandResult(
                    success=result.returncode == 0,
                    raw_output=result.stdout,
                    structured_output=result.stdout.split("\n") if result.stdout else [],
                    exit_code=result.returncode,
                    error_message=result.stderr if result.stderr else None,
                )

        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                raw_output="",
                structured_output=[],
                exit_code=1,
                error_message="SSH command execution timed out",
            )
        except Exception as e:
            return CommandResult(
                success=False,
                raw_output="",
                structured_output=[],
                exit_code=1,
                error_message=f"SSH command execution failed: {str(e)}",
            )

    def _execute_with_fingerprint_handling(
        self,
        ssh_command: List[str],
        working_dir: Optional[str],
        env_vars: Optional[Dict[str, str]],
        fingerprint_callback: Callable,
    ) -> CommandResult:
        """Execute SSH command with interactive fingerprint handling"""
        try:
            import queue
            import threading

            import pexpect

            # Zbuduj komendę jako string
            cmd_str = " ".join(ssh_command)

            if hasattr(self, "logger") and self.logger:
                self.logger.info(f"Executing SSH with fingerprint handling: {cmd_str}")

            # Kolejka do komunikacji między wątkami
            result_queue: queue.Queue = queue.Queue()

            def ssh_worker():
                try:
                    # Uruchom SSH z pexpect w osobnym wątku
                    child = pexpect.spawn(cmd_str, timeout=30)

                    # Oczekuj na różne możliwe prompty
                    index = child.expect(
                        [
                            pexpect.EOF,  # Połączenie udane
                            "fingerprint is",  # Pytanie o fingerprint
                            "continue connecting",  # Inny format pytania
                            "password:",  # Pytanie o hasło
                            pexpect.TIMEOUT,  # Timeout
                        ]
                    )

                    if index == 1 or index == 2:  # Pytanie o fingerprint
                        # Pobierz output przed pytaniem
                        output = child.before.decode("utf-8", errors="ignore")

                        if hasattr(self, "logger") and self.logger:
                            self.logger.info(f"SSH fingerprint prompt detected: {output}")

                        # Wyciągnij fingerprint i key type
                        import re

                        pattern = r"(\w+) key fingerprint is (SHA256:[A-Za-z0-9+/=]+)"
                        match = re.search(pattern, output)

                        if match:
                            key_type = match.group(1)
                            fingerprint = match.group(2)

                            if hasattr(self, "logger") and self.logger:
                                self.logger.info(f"Extracted: {key_type} - {fingerprint}")

                            # Wywołaj callback z fingerprintem w głównym wątku
                            try:
                                # Użyj QTimer żeby wywołać callback w głównym wątku GUI
                                from PyQt6.QtCore import QTimer

                                def call_callback():
                                    try:
                                        result = fingerprint_callback(key_type, fingerprint)

                                        if result == "yes":
                                            child.sendline("yes")
                                            if hasattr(self, "logger") and self.logger:
                                                self.logger.info("User accepted fingerprint")
                                        elif result == "no":
                                            child.sendline("no")
                                            child.close()
                                            result_queue.put(
                                                CommandResult(
                                                    success=False,
                                                    raw_output="",
                                                    structured_output=[],
                                                    exit_code=1,
                                                    error_message="Fingerprint rejected by user",
                                                )
                                            )
                                            return
                                        else:
                                            child.close()
                                            result_queue.put(
                                                CommandResult(
                                                    success=False,
                                                    raw_output="",
                                                    structured_output=[],
                                                    exit_code=1,
                                                    error_message="Fingerprint handling cancelled",
                                                )
                                            )
                                            return
                                    except Exception as e:
                                        if hasattr(self, "logger") and self.logger:
                                            self.logger.error(f"Error in fingerprint callback: {e}")
                                        child.close()
                                        result_queue.put(
                                            CommandResult(
                                                success=False,
                                                raw_output="",
                                                structured_output=[],
                                                exit_code=1,
                                                error_message=f"Fingerprint callback error: {str(e)}",
                                            )
                                        )
                                        return

                                # Uruchom callback w głównym wątku
                                QTimer.singleShot(0, call_callback)

                            except ImportError:
                                # Fallback jeśli PyQt6 nie jest dostępne
                                result = fingerprint_callback(key_type, fingerprint)

                                if result == "yes":
                                    child.sendline("yes")
                                    if hasattr(self, "logger") and self.logger:
                                        self.logger.info("User accepted fingerprint")
                                elif result == "no":
                                    child.sendline("no")
                                    child.close()
                                    result_queue.put(
                                        CommandResult(
                                            success=False,
                                            raw_output="",
                                            structured_output=[],
                                            exit_code=1,
                                            error_message="Fingerprint rejected by user",
                                        )
                                    )
                                    return
                                else:
                                    child.close()
                                    result_queue.put(
                                        CommandResult(
                                            success=False,
                                            raw_output="",
                                            structured_output=[],
                                            exit_code=1,
                                            error_message="Fingerprint handling cancelled",
                                        )
                                    )
                                    return

                        # Kontynuuj połączenie
                        try:
                            child.expect([pexpect.EOF, "password:", pexpect.TIMEOUT], timeout=30)
                        except pexpect.TIMEOUT:
                            child.close()
                            result_queue.put(
                                CommandResult(
                                    success=False,
                                    raw_output="",
                                    structured_output=[],
                                    exit_code=1,
                                    error_message="SSH connection timeout after fingerprint",
                                )
                            )
                            return

                    elif index == 3:  # Pytanie o hasło
                        if hasattr(self, "logger") and self.logger:
                            self.logger.info("SSH password prompt detected")
                        # Obsługa hasła (jeśli potrzebna)
                        pass

                    # Czekaj na zakończenie
                    try:
                        child.expect(pexpect.EOF, timeout=30)
                    except pexpect.TIMEOUT:
                        child.close()
                        result_queue.put(
                            CommandResult(
                                success=False,
                                raw_output="",
                                structured_output=[],
                                exit_code=1,
                                error_message="SSH command execution timeout",
                            )
                        )
                        return

                    # Pobierz output
                    output = child.read().decode("utf-8", errors="ignore")
                    exit_code = child.exitstatus if hasattr(child, "exitstatus") else 0

                    child.close()

                    if hasattr(self, "logger") and self.logger:
                        self.logger.info(f"SSH command completed with exit code: {exit_code}")

                    result_queue.put(
                        CommandResult(
                            success=exit_code == 0,
                            raw_output=output,
                            structured_output=output.split("\n") if output else [],
                            exit_code=exit_code,
                            error_message=None,
                        )
                    )

                except Exception as e:
                    if hasattr(self, "logger") and self.logger:
                        self.logger.error(f"SSH worker error: {str(e)}")
                    result_queue.put(
                        CommandResult(
                            success=False,
                            raw_output="",
                            structured_output=[],
                            exit_code=1,
                            error_message=f"SSH worker error: {str(e)}",
                        )
                    )

            # Uruchom SSH w osobnym wątku
            ssh_thread = threading.Thread(target=ssh_worker, daemon=True)
            ssh_thread.start()

            # Czekaj na wynik z timeoutem
            try:
                result = result_queue.get(timeout=60)  # 60 sekund timeout
                return result
            except queue.Empty:
                if hasattr(self, "logger") and self.logger:
                    self.logger.error("SSH execution timeout")
                return CommandResult(
                    success=False,
                    raw_output="",
                    structured_output=[],
                    exit_code=1,
                    error_message="SSH execution timeout",
                )

        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(f"Fingerprint handling failed: {str(e)}")
            return CommandResult(
                success=False,
                raw_output="",
                structured_output=[],
                exit_code=1,
                error_message=f"Fingerprint handling failed: {str(e)}",
            )

    def _build_proxy_options(self) -> List[str]:
        """Buduje opcje proxy dla SSH"""
        options = []

        if "proxy_command" in self.proxy_config:
            options.extend(["-o", f"ProxyCommand={self.proxy_config['proxy_command']}"])

        if "proxy_host" in self.proxy_config:
            options.extend(["-o", f"ProxyHost={self.proxy_config['proxy_host']}"])

        if "proxy_port" in self.proxy_config:
            options.extend(["-o", f"ProxyPort={self.proxy_config['proxy_port']}"])

        if "proxy_user" in self.proxy_config:
            options.extend(["-o", f"ProxyUser={self.proxy_config['proxy_user']}"])

        return options

    def scp_upload(
        self, local_path: str, remote_path: str, session_id: Optional[str] = None
    ) -> SCPTransfer:
        """Upload pliku przez SCP"""
        target_session = session_id or self.active_session
        if not target_session or target_session not in self.sessions:
            raise ValueError("No active SSH session")

        session = self.sessions[target_session]
        transfer_id = f"upload_{int(time.time())}"

        transfer = SCPTransfer(
            id=transfer_id,
            source=local_path,
            destination=remote_path,
            direction="upload",
        )

        with self.transfer_lock:
            self.transfers[transfer_id] = transfer

        # Uruchom transfer w osobnym wątku
        threading.Thread(target=self._execute_scp_upload, args=(transfer, session)).start()

        return transfer

    def scp_download(
        self, remote_path: str, local_path: str, session_id: Optional[str] = None
    ) -> SCPTransfer:
        """Download pliku przez SCP"""
        target_session = session_id or self.active_session
        if not target_session or target_session not in self.sessions:
            raise ValueError("No active SSH session")

        session = self.sessions[target_session]
        transfer_id = f"download_{int(time.time())}"

        transfer = SCPTransfer(
            id=transfer_id,
            source=remote_path,
            destination=local_path,
            direction="download",
        )

        with self.transfer_lock:
            self.transfers[transfer_id] = transfer

        # Uruchom transfer w osobnym wątku
        threading.Thread(target=self._execute_scp_download, args=(transfer, session)).start()

        return transfer

    def _execute_scp_upload(self, transfer: SCPTransfer, session: SSHSession):
        """Wykonuje upload SCP"""
        transfer.status = "transferring"

        try:
            scp_command = ["scp"]

            if session.port != 22:
                scp_command.extend(["-P", str(session.port)])

            if self.key_filename:
                scp_command.extend(["-i", self.key_filename])

            scp_command.extend(
                [
                    transfer.source,
                    f"{session.username}@{session.hostname}:{transfer.destination}",
                ]
            )

            result = subprocess.run(scp_command, capture_output=True, text=True)

            if result.returncode == 0:
                transfer.status = "completed"
                transfer.progress = 100.0
            else:
                transfer.status = "failed"

        except Exception as e:
            transfer.status = "failed"

        transfer.end_time = datetime.now()

    def _execute_scp_download(self, transfer: SCPTransfer, session: SSHSession):
        """Wykonuje download SCP"""
        transfer.status = "transferring"

        try:
            scp_command = ["scp"]

            if session.port != 22:
                scp_command.extend(["-P", str(session.port)])

            if self.key_filename:
                scp_command.extend(["-i", self.key_filename])

            scp_command.extend(
                [
                    f"{session.username}@{session.hostname}:{transfer.source}",
                    transfer.destination,
                ]
            )

            result = subprocess.run(scp_command, capture_output=True, text=True)

            if result.returncode == 0:
                transfer.status = "completed"
                transfer.progress = 100.0
            else:
                transfer.status = "failed"

        except Exception as e:
            transfer.status = "failed"

        transfer.end_time = datetime.now()

    def get_transfer_status(self, transfer_id: str) -> Optional[SCPTransfer]:
        """Pobiera status transferu"""
        with self.transfer_lock:
            return self.transfers.get(transfer_id)

    def list_transfers(self) -> List[SCPTransfer]:
        """Listuje wszystkie transfery"""
        with self.transfer_lock:
            return list(self.transfers.values())

    def cancel_transfer(self, transfer_id: str) -> bool:
        """Anuluje transfer"""
        with self.transfer_lock:
            if transfer_id in self.transfers:
                transfer = self.transfers[transfer_id]
                if transfer.status == "transferring":
                    transfer.status = "cancelled"
                    return True
        return False

    def parse_output(
        self, command: str, raw_output: str, exit_code: int, error_output: str = ""
    ) -> CommandResult:
        """Parse command output into a standard CommandResult."""
        success = exit_code == 0

        # Basic line-splitting structure
        structured_output = []
        if raw_output:
            structured_output = raw_output.strip().split("\n")
            structured_output = [line for line in structured_output if line]

        return CommandResult(
            raw_output=raw_output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_output if not success else None,
        )

    def test_connection(self) -> bool:
        """Testuje połączenie SSH bez tworzenia sesji"""
        try:
            # Buduj komendę SSH do testu
            ssh_command = ["ssh"]

            # Dodaj opcje SSH
            if self.port != 22:
                ssh_command.extend(["-p", str(self.port)])

            if self.key_filename:
                ssh_command.extend(["-i", self.key_filename])

            if self.proxy_config:
                ssh_command.extend(self._build_proxy_options())

            # Dodaj timeout
            if self.timeout:
                ssh_command.extend(["-o", f"ConnectTimeout={self.timeout}"])
            else:
                ssh_command.extend(["-o", "ConnectTimeout=10"])

            # Dodaj hostname i username
            if self.username:
                ssh_command.append(f"{self.username}@{self.hostname}")
            else:
                ssh_command.append(self.hostname)

            # Dodaj prostą komendę testową
            ssh_command.append("echo 'Connection test successful'")

            # Wykonaj test z obsługą fingerprinta
            fingerprint_callback = self.get_fingerprint_callback()

            if fingerprint_callback:
                # Użyj interaktywnej obsługi fingerprinta
                return self._execute_with_fingerprint_handling(
                    ssh_command, None, None, fingerprint_callback
                ).success
            else:
                # Standardowy test
                result = subprocess.run(
                    ssh_command,
                    capture_output=True,
                    text=True,
                    timeout=15,  # Krótki timeout dla testu
                )

                return result.returncode == 0

        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(f"Błąd testu połączenia SSH: {e}")
            return False

    def check_host_key(self) -> tuple[bool, Optional[str], Optional[str]]:
        """Check SSH host key - simplified approach

        Returns:
            Tuple (is_known, key_type, fingerprint)
            - is_known: True if host is known in known_hosts
            - key_type: Key type (e.g., "ED25519", "RSA")
            - fingerprint: Key fingerprint
        """
        try:
            # Simple check - just verify if host is in known_hosts
            import os

            known_hosts_file = os.path.expanduser("~/.ssh/known_hosts")

            if not os.path.exists(known_hosts_file):
                return False, None, None

            host_entry = f"[{self.hostname}]:{self.port}" if self.port != 22 else self.hostname

            with open(known_hosts_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == host_entry:
                            return True, None, None

            return False, None, None

        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(f"Error checking SSH host key: {e}")
            return False, None, None

    def build_command_string(
        self,
        command_name: str,
        options: List[str],
        params: Dict[str, Any],
        flags: List[str],
    ) -> str:
        """Build an SSH-compatible command string."""
        parts = [command_name]
        parts.extend(options)
        parts.extend(flags)
        for name, value in params.items():
            if len(name) == 1:
                parts.append(f"-{name}")
                parts.append(shlex.quote(str(value)))
            else:
                parts.append(f"--{name}={shlex.quote(str(value))}")
        return " ".join(parts)
