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

        # Interactive shell handling
        self.output_callback: Optional[Callable[[str, str], None]] = None  # (session_id, data)
        self.shells: Dict[str, Dict[str, Any]] = (
            {}
        )  # session_id -> {"fd": int, "reader": Thread, "alive": bool}

        # Logger initialization (if available)
        try:
            from ..logging.mancer_logger import MancerLogger

            self.logger = MancerLogger.get_instance()
        except Exception:
            self.logger = None

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
                # Uruchom interaktywną powłokę domyślnie
                try:
                    self._start_interactive_shell(session)
                except Exception as _e:
                    # Nie blokuj połączenia jeśli powłoka nie wystartowała; loguj jeśli jest logger
                    if hasattr(self, "logger") and self.logger:
                        self.logger.warning(f"Nie udało się uruchomić sesji interaktywnej: {_e}")
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
        # Zamknij interaktywną powłokę, jeśli działa
        try:
            self.close_interactive(session_id)
        except Exception:
            pass
        session.status = "disconnected"

        if self.active_session == session_id:
            self.active_session = None

        return True

    def set_fingerprint_callback(self, callback: Callable):
        """Ustawia callback do obsługi fingerprint prompts"""
        with self.fingerprint_callback_lock:
            self.fingerprint_callback = callback

    def set_output_callback(self, callback: Callable[[str, str], None]):
        """Ustawia callback dla wyjścia interaktywnej sesji SSH (session_id, chunk)."""
        self.output_callback = callback

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
                # Standardowe wykonanie SSH (dla jednorazowych komend). Jeśli interaktywna powłoka działa,
                # wyślij komendę do niej i zwróć sukces natychmiast (output trafi przez callback terminala).
                if session_id in self.shells and self.shells[session_id].get("alive"):
                    sent = self.send_input(session_id, command + "\n")
                    return CommandResult(
                        success=sent,
                        raw_output="",
                        structured_output=[],
                        exit_code=0 if sent else 1,
                        error_message=None if sent else "Interactive shell not available",
                    )
                # Brak interaktywnej sesji – jednorazowe uruchomienie
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
        """Execute SSH command with interactive fingerprint handling using subprocess."""
        import os
        import queue
        import re

        # Aby uniknąć problemu z TTY, dodajemy flagę -T do komendy ssh.
        # To zmusza ssh do używania stdin/stdout zamiast /dev/tty.
        modified_ssh_command = ssh_command.copy()
        if modified_ssh_command and modified_ssh_command[0] == "ssh":
            # Wstaw -T zaraz po komendzie 'ssh'
            modified_ssh_command.insert(1, "-T")
            # Wymuś brak promptów po zaakceptowaniu klucza (po preflight) jeśli nie określono inaczej w ssh_options
            has_shkc = any(
                (isinstance(tok, str) and tok.startswith("StrictHostKeyChecking="))
                or (
                    tok == "StrictHostKeyChecking"
                    and i + 1 < len(modified_ssh_command)
                    and str(modified_ssh_command[i + 1]).startswith("StrictHostKeyChecking=")
                )
                or (
                    tok == "-o"
                    and i + 1 < len(modified_ssh_command)
                    and str(modified_ssh_command[i + 1]).startswith("StrictHostKeyChecking=")
                )
                for i, tok in enumerate(modified_ssh_command)
            )
            if not has_shkc:
                modified_ssh_command.extend(["-o", "StrictHostKeyChecking=yes"])

        result_queue: queue.Queue[CommandResult] = queue.Queue()

        def run_command():
            try:
                # Preflight: pobierz klucz hosta i policz fingerprint, pokaż dialog, zapisz do known_hosts po akceptacji
                if hasattr(self, "logger") and self.logger:
                    self.logger.info("Starting SSH with fingerprint handling (preflight mode).")

                host_target = None
                for tok in modified_ssh_command:
                    if "@" in tok and not tok.startswith("-") and " " not in tok:
                        host_target = tok.split("@", 1)[1]
                        break
                if host_target is None and modified_ssh_command:
                    host_target = (
                        modified_ssh_command[-2] if len(modified_ssh_command) >= 2 else None
                    )

                # Ustal port z opcji, domyślnie 22
                port_value = 22
                if "-p" in modified_ssh_command:
                    try:
                        pidx = modified_ssh_command.index("-p")
                        port_value = int(modified_ssh_command[pidx + 1])
                    except Exception:
                        port_value = 22

                # Uruchom ssh-keyscan
                try:
                    keyscan_cmd = [
                        "ssh-keyscan",
                        "-p",
                        str(port_value),
                        "-T",
                        "5",
                        host_target,
                    ]
                    ks = subprocess.run(keyscan_cmd, capture_output=True, text=True, timeout=10)
                    if ks.returncode != 0 or not ks.stdout:
                        raise RuntimeError(ks.stderr or "ssh-keyscan failed or returned no data")
                    # Pierwsza niekomentarzowa linia
                    key_line = None
                    for ln in ks.stdout.splitlines():
                        if ln and not ln.startswith("#"):
                            key_line = ln.strip()
                            break
                    if not key_line:
                        raise RuntimeError("No host key found by ssh-keyscan")
                    # Format: host keytype base64
                    parts = key_line.split()
                    if len(parts) < 3:
                        raise RuntimeError(f"Unexpected keyscan line: {key_line}")
                    key_type = parts[1]
                    key_b64 = parts[2]

                    # Policz fingerprint: ssh-keygen -lf - (stdin: "host keytype base64")
                    to_hash = f"{host_target} {key_type} {key_b64}\n"
                    sk = subprocess.run(
                        ["ssh-keygen", "-lf", "-"],
                        input=to_hash,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if sk.returncode != 0 or not sk.stdout:
                        raise RuntimeError(sk.stderr or "ssh-keygen failed to compute fingerprint")
                    # Przykład: "256 SHA256:abcdef... host (ED25519)"
                    mfp = re.search(r"SHA256:[A-Za-z0-9+/=]+", sk.stdout)
                    if not mfp:
                        raise RuntimeError(f"Could not parse fingerprint from: {sk.stdout}")
                    fingerprint_str = mfp.group(0)

                    if hasattr(self, "logger") and self.logger:
                        self.logger.info(
                            f"Preflight fingerprint detected: {fingerprint_str} ({key_type})"
                        )

                    # Callback do GUI
                    decision = fingerprint_callback(fingerprint_str)
                    if hasattr(self, "logger") and self.logger:
                        self.logger.info(f"Preflight callback decision: {decision}")
                    if decision != "yes":
                        result_queue.put(
                            CommandResult(
                                success=False,
                                raw_output="",
                                structured_output=[],
                                exit_code=1,
                                error_message="Fingerprint rejected by user (preflight).",
                            )
                        )
                        return

                    # Zapisz do known_hosts
                    # Szanuj UserKnownHostsFile jeśli przekazano w ssh_options
                    kh_override = None
                    try:
                        kh_override = (
                            self.ssh_options.get("UserKnownHostsFile")
                            if isinstance(self.ssh_options, dict)
                            else None
                        )
                    except Exception:
                        kh_override = None
                    known_hosts = (
                        os.path.expanduser(kh_override)
                        if kh_override
                        else os.path.expanduser("~/.ssh/known_hosts")
                    )
                    os.makedirs(os.path.dirname(known_hosts), exist_ok=True)
                    host_entry = (
                        f"[{host_target}]:{port_value}" if port_value != 22 else host_target
                    )
                    with open(known_hosts, "a", encoding="utf-8") as fh:
                        fh.write(f"{host_entry} {key_type} {key_b64}\n")
                    try:
                        os.chmod(known_hosts, 0o600)
                    except Exception:
                        pass
                    if hasattr(self, "logger") and self.logger:
                        self.logger.info(f"Host key saved to known_hosts for {host_entry}")
                except Exception as e:
                    if hasattr(self, "logger") and self.logger:
                        self.logger.error(f"Preflight host key handling failed: {e}")
                    result_queue.put(
                        CommandResult(
                            success=False,
                            raw_output="",
                            structured_output=[],
                            exit_code=1,
                            error_message=f"Preflight failed: {e}",
                        )
                    )
                    return

                # Wykonaj właściwe SSH (bez interakcji)
                if hasattr(self, "logger") and self.logger:
                    self.logger.info(
                        f"Starting SSH with fingerprint handling. Command: {' '.join(modified_ssh_command)}"
                    )
                run_env = dict(os.environ)
                if env_vars:
                    run_env.update(env_vars)

                # Jeśli mamy hasło, użyj SSH_ASKPASS (bez TTY)
                cleanup_script = None
                try:
                    if getattr(self, "password", None):
                        # Preferuj uwierzytelnianie hasłem
                        modified_ssh_command.extend(
                            [
                                "-o",
                                "PreferredAuthentications=password,keyboard-interactive",
                                "-o",
                                "PubkeyAuthentication=no",
                            ]
                        )
                        import stat
                        import tempfile

                        fd, script_path = tempfile.mkstemp(prefix="mancer_askpass_", text=True)
                        os.close(fd)
                        with open(script_path, "w", encoding="utf-8") as sf:
                            sf.write("#!/bin/sh\n")
                            sf.write("echo '" + str(self.password).replace("'", "'\\''") + "'\n")
                        os.chmod(script_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                        cleanup_script = script_path
                        run_env["SSH_ASKPASS"] = script_path
                        run_env["SSH_ASKPASS_REQUIRE"] = "force"
                        # SSH wymaga DISPLAY ustawionego (nie musi być prawdziwy)
                        run_env.setdefault("DISPLAY", ":9999")

                    result = subprocess.run(
                        modified_ssh_command,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout or 30,
                        cwd=working_dir,
                        env=run_env,
                        preexec_fn=os.setsid,
                    )
                finally:
                    if cleanup_script:
                        try:
                            os.remove(cleanup_script)
                        except Exception:
                            pass
                final_output = (result.stdout or "") + (
                    "\n" + result.stderr if result.stderr else ""
                )
                result_queue.put(
                    CommandResult(
                        success=result.returncode == 0,
                        raw_output=final_output,
                        structured_output=[ln for ln in final_output.splitlines() if ln],
                        exit_code=result.returncode,
                        error_message=None if result.returncode == 0 else result.stderr,
                    )
                )
            except subprocess.TimeoutExpired:
                result_queue.put(
                    CommandResult(
                        success=False,
                        raw_output="",
                        structured_output=[],
                        exit_code=-1,
                        error_message="SSH command execution timed out.",
                    )
                )
            except Exception as e:
                if hasattr(self, "logger") and self.logger:
                    self.logger.error(f"SSH worker thread error: {e}")
                result_queue.put(
                    CommandResult(
                        success=False,
                        raw_output="",
                        structured_output=[],
                        exit_code=-1,
                        error_message=f"SSH execution failed: {e}",
                    )
                )

        thread = threading.Thread(target=run_command, daemon=True)
        thread.start()

        try:
            # Czekaj na wynik z kolejki z timeoutem
            return result_queue.get(timeout=self.timeout or 60)
        except queue.Empty:
            if hasattr(self, "logger") and self.logger:
                self.logger.error("Timed out waiting for SSH command result.")
            return CommandResult(
                success=False,
                raw_output="",
                structured_output=[],
                exit_code=-1,
                error_message="Timeout waiting for SSH command to complete.",
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

    def _build_ssh_base_command(self, session: SSHSession) -> List[str]:
        cmd = ["ssh"]
        if session.port != 22:
            cmd.extend(["-p", str(session.port)])
        if self.key_filename:
            cmd.extend(["-i", self.key_filename])
        if not self.look_for_keys:
            cmd.extend(["-o", "IdentitiesOnly=yes"])
        if self.allow_agent:
            cmd.extend(["-o", "ForwardAgent=yes"])
        if self.compress:
            cmd.append("-C")
        if self.timeout:
            cmd.extend(["-o", f"ConnectTimeout={self.timeout}"])
        if self.gssapi_auth:
            cmd.extend(["-o", "GSSAPIAuthentication=yes"])
        if self.proxy_config:
            cmd.extend(self._build_proxy_options())
        for key, value in self.ssh_options.items():
            cmd.extend(["-o", f"{key}={value}"])
        if session.username:
            cmd.append(f"{session.username}@{session.hostname}")
        else:
            cmd.append(session.hostname)
        return cmd

    def _start_interactive_shell(self, session: SSHSession) -> None:
        """Startuje interaktywną sesję SSH z użyciem lokalnego PTY; domyślne zachowanie."""
        if session.id in self.shells and self.shells[session.id].get("alive"):
            return
        import os as _os
        import pty
        import select

        ssh_cmd = self._build_ssh_base_command(session)
        # Wymuś przydzielenie PTY po stronie zdalnej
        ssh_cmd.insert(1, "-tt")

        if hasattr(self, "logger") and self.logger:
            self.logger.info(f"Starting interactive SSH shell: {' '.join(ssh_cmd)}")

        pid, fd = pty.fork()
        if pid == 0:
            # Child: exec ssh
            try:
                _os.execvp(ssh_cmd[0], ssh_cmd)
            except Exception:
                _os._exit(1)
        else:
            alive_flag = {"alive": True}

            def reader_loop():
                try:
                    while alive_flag["alive"]:
                        rlist, _, _ = select.select([fd], [], [], 0.2)
                        if fd in rlist:
                            try:
                                data = _os.read(fd, 4096)
                            except OSError:
                                break
                            if not data:
                                break
                            text = data.decode("utf-8", errors="ignore")
                            if self.output_callback:
                                try:
                                    self.output_callback(session.id, text)
                                except Exception:
                                    pass
                finally:
                    alive_flag["alive"] = False
                    try:
                        _os.close(fd)
                    except Exception:
                        pass

            t = threading.Thread(target=reader_loop, daemon=True)
            t.start()
            self.shells[session.id] = {
                "fd": fd,
                "pid": pid,
                "reader": t,
                "alive": True,
                "alive_flag": alive_flag,
            }

    def send_input(self, session_id: str, data: str) -> bool:
        """Wysyła dane do interaktywnej sesji SSH."""
        import os as _os

        shell = self.shells.get(session_id)
        if not shell or not shell.get("alive"):
            return False
        try:
            _os.write(shell["fd"], data.encode("utf-8"))
            return True
        except Exception:
            return False

    def close_interactive(self, session_id: str) -> None:
        import os as _os

        shell = self.shells.get(session_id)
        if not shell:
            return
        shell.get("alive_flag", {}).update({"alive": False})
        try:
            _os.close(shell.get("fd"))
        except Exception:
            pass
        self.shells.pop(session_id, None)
