import shlex
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from ...domain.interface.backend_interface import BackendInterface
from ...domain.model.command_result import CommandResult


class SshBackend(BackendInterface):
    """Backend executing commands over SSH on a remote host."""

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

    def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """Execute a command over SSH on the remote host."""
        # Budujemy komendę SSH
        ssh_command = ["ssh"]

        # Dodajemy opcje SSH
        if self.port != 22:
            ssh_command.extend(["-p", str(self.port)])

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

        if self.gssapi_kex:
            ssh_command.extend(["-o", "GSSAPIKeyExchange=yes"])

        if self.gssapi_delegate_creds:
            ssh_command.extend(["-o", "GSSAPIDelegateCredentials=yes"])

        # Dodajemy opcje dla automatycznego odpowiadania na pytania (non-interactive)
        ssh_command.extend(["-o", "BatchMode=no"])
        ssh_command.extend(["-o", "StrictHostKeyChecking=no"])

        # Dodajemy dodatkowe opcje SSH
        for key, value in self.ssh_options.items():
            ssh_command.extend(["-o", f"{key}={value}"])

        # Dodajemy użytkownika i hosta
        target = self.hostname
        if self.username:
            target = f"{self.username}@{self.hostname}"

        ssh_command.append(target)

        # Przygotowanie środowiska
        env_prefix = ""
        if env_vars:
            env_parts = []
            for key, value in env_vars.items():
                env_parts.append(f"export {key}={shlex.quote(value)}")
            if env_parts:
                env_prefix = "; ".join(env_parts) + "; "

        # Przygotowanie katalogu roboczego
        cd_prefix = ""
        if working_dir:
            cd_prefix = f"cd {shlex.quote(working_dir)} && "

        # Łączymy wszystko w jedną komendę
        remote_command = f"{env_prefix}{cd_prefix}{command}"

        # Dodajemy komendę do wykonania na zdalnym hoście
        ssh_command.append(remote_command)

        # Jeśli mamy hasło do SSH, musimy użyć sshpass
        if self.password:
            # Używamy sshpass do podania hasła
            final_command = ["sshpass", "-p", self.password]
            final_command.extend(ssh_command)
        else:
            final_command = ssh_command

        try:
            # Wykonanie komendy
            process = subprocess.run(final_command, text=True, capture_output=True)

            # Parsowanie wyniku
            return self.parse_output(command, process.stdout, process.returncode, process.stderr)
        except Exception:
            # Obsługa błędów
            return CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=-1,
                error_message="SSH Error occurred",
            )

    def execute(
        self,
        command: str,
        input_data: Optional[str] = None,
        working_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """
        Executes a command via SSH and returns exit code, stdout, and stderr.
        This method is used by Command classes.

        Args:
            command: The command to execute
            input_data: Optional input data to pass to stdin
            working_dir: Optional working directory

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Build SSH command
            ssh_command = ["ssh"]

            # Add SSH options
            if self.port != 22:
                ssh_command.extend(["-p", str(self.port)])

            # Handle authentication methods
            if self.key_filename:
                ssh_command.extend(["-i", self.key_filename])

            if not self.look_for_keys:
                ssh_command.extend(["-o", "IdentitiesOnly=yes"])

            if self.allow_agent:
                ssh_command.extend(["-o", "ForwardAgent=yes"])

            if self.compress:
                ssh_command.append("-C")

            if self.timeout:
                ssh_command.extend(["-o", f"ConnectTimeout={self.timeout}"])

            if self.gssapi_auth:
                ssh_command.extend(["-o", "GSSAPIAuthentication=yes"])

            if self.gssapi_kex:
                ssh_command.extend(["-o", "GSSAPIKeyExchange=yes"])

            if self.gssapi_delegate_creds:
                ssh_command.extend(["-o", "GSSAPIDelegateCredentials=yes"])

            # Add options for non-interactive mode
            ssh_command.extend(["-o", "BatchMode=no"])
            ssh_command.extend(["-o", "StrictHostKeyChecking=no"])

            # Add additional SSH options
            for key, value in self.ssh_options.items():
                ssh_command.extend(["-o", f"{key}={value}"])

            # Add username and host
            target = self.hostname
            if self.username:
                target = f"{self.username}@{self.hostname}"

            ssh_command.append(target)

            # Prepare working directory
            cd_prefix = ""
            if working_dir:
                cd_prefix = f"cd {shlex.quote(working_dir)} && "

            # Combine command
            remote_command = f"{cd_prefix}{command}"

            # Add command to execute on remote host
            ssh_command.append(remote_command)

            # If we have an SSH password, use sshpass
            final_command = ssh_command
            if self.password:
                final_command = ["sshpass", "-p", self.password] + ssh_command

            # Execute the command
            stdin_pipe = subprocess.PIPE if input_data else None
            process = subprocess.Popen(
                final_command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=stdin_pipe,
            )

            # Send input data if provided
            stdout, stderr = process.communicate(input=input_data)
            exit_code = process.returncode

            return exit_code, stdout, stderr

        except Exception as e:
            return -1, "", str(e)

    def parse_output(
        self, command: str, raw_output: str, exit_code: int, error_output: str = ""
    ) -> CommandResult:
        """Parse command output into a standard CommandResult."""
        success = exit_code == 0

        # Próbujemy podstawowe strukturyzowanie wyniku (linie tekstu)
        structured_output = []
        if raw_output:
            structured_output = raw_output.strip().split("\n")
            # Usuwamy puste linie
            structured_output = [line for line in structured_output if line]

        return CommandResult(
            raw_output=raw_output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_output if not success else None,
        )

    def build_command_string(
        self,
        command_name: str,
        options: List[str],
        params: Dict[str, Any],
        flags: List[str],
    ) -> str:
        """Buduje string komendy zgodny z bashem (używanym przez SSH)"""
        parts = [command_name]

        # Opcje (krótkie, np. -l)
        parts.extend(options)

        # Flagi (długie, np. --recursive)
        parts.extend(flags)

        # Parametry (--name=value lub -n value)
        for name, value in params.items():
            if len(name) == 1:
                # Krótka opcja
                parts.append(f"-{name}")
                parts.append(shlex.quote(str(value)))
            else:
                # Długa opcja
                parts.append(f"--{name}={shlex.quote(str(value))}")

        return " ".join(parts)
