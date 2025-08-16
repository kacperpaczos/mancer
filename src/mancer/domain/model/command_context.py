from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum, auto

class ExecutionMode(Enum):
    """Command execution mode.

    - LOCAL: Execute on the local host.
    - REMOTE: Execute on a remote host via SSH.
    """
    LOCAL = auto()
    REMOTE = auto()

@dataclass
class RemoteHostInfo:
    """Remote host connection parameters.

    Attributes:
        host: Hostname or IP address.
        user: SSH username.
        port: SSH port (default 22).
        key_file: Path to private key file.
        password: Password for password-based auth (not recommended).
        use_agent: Whether to use ssh-agent.
        certificate_file: Path to SSH certificate (if applicable).
        identity_only: Force using provided identities only (IdentitiesOnly=yes).
        gssapi_auth: Enable GSSAPI authentication.
        gssapi_keyex: Enable GSSAPI key exchange.
        gssapi_delegate_creds: Delegate GSSAPI credentials.
        use_sudo: Whether commands should use sudo by default.
        sudo_password: Sudo password if required.
        ssh_options: Extra SSH options as a dictionary.
    """
    host: str
    user: Optional[str] = None
    port: int = 22
    # Auth methods
    key_file: Optional[str] = None
    password: Optional[str] = None
    use_agent: bool = False
    certificate_file: Optional[str] = None
    identity_only: bool = False
    gssapi_auth: bool = False
    gssapi_keyex: bool = False
    gssapi_delegate_creds: bool = False
    # Sudo
    use_sudo: bool = False
    sudo_password: Optional[str] = None
    # Extra SSH options
    ssh_options: Dict[str, str] = field(default_factory=dict)

@dataclass
class CommandContext:
    """Command execution context.

    Attributes:
        current_directory: Working directory for the command.
        environment_variables: Environment variables to set for execution.
        command_history: Raw command strings executed in this context.
        parameters: Arbitrary parameters used by commands and backends.
        execution_mode: Local or remote execution mode.
        remote_host: Remote host parameters when in REMOTE mode.
    """
    current_directory: str = "."
    environment_variables: Dict[str, str] = field(default_factory=dict)
    command_history: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    execution_mode: ExecutionMode = ExecutionMode.LOCAL
    remote_host: Optional[RemoteHostInfo] = None
    
    def change_directory(self, new_directory: str) -> None:
        """Change the working directory in this context."""
        self.current_directory = new_directory

    def add_to_history(self, command_string: str) -> None:
        """Append a raw command string to the context history."""
        self.command_history.append(command_string)

    def set_parameter(self, key: str, value: Any) -> None:
        """Set an arbitrary parameter on the context."""
        self.parameters[key] = value

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Return a context parameter by key, or default if not set."""
        return self.parameters.get(key, default)

    def set_remote_execution(self, host: str, user: Optional[str] = None,
                           port: int = 22, key_file: Optional[str] = None,
                           password: Optional[str] = None, use_sudo: bool = False,
                           sudo_password: Optional[str] = None, use_agent: bool = False,
                           certificate_file: Optional[str] = None, identity_only: bool = False,
                           gssapi_auth: bool = False, gssapi_keyex: bool = False,
                           gssapi_delegate_creds: bool = False,
                           ssh_options: Optional[Dict[str, str]] = None) -> None:
        """Configure remote execution mode.

        Args:
            host: Hostname or IP address of the remote server.
            user: SSH username.
            port: SSH port (default 22).
            key_file: Path to private key (optional).
            password: Password (optional; prefer keys).
            use_sudo: Whether to use sudo for commands requiring elevation.
            sudo_password: Sudo password (if required).
            use_agent: Whether to use SSH agent for authentication.
            certificate_file: Path to SSH certificate.
            identity_only: Whether to use only provided identities (IdentitiesOnly=yes).
            gssapi_auth: Enable GSSAPI authentication (Kerberos).
            gssapi_keyex: Enable GSSAPI key exchange.
            gssapi_delegate_creds: Delegate GSSAPI credentials.
            ssh_options: Additional SSH options as a dictionary.
        """
        self.execution_mode = ExecutionMode.REMOTE

        options = {}
        if ssh_options:
            options.update(ssh_options)

        self.remote_host = RemoteHostInfo(
            host=host,
            user=user,
            port=port,
            key_file=key_file,
            password=password,
            use_sudo=use_sudo,
            sudo_password=sudo_password,
            use_agent=use_agent,
            certificate_file=certificate_file,
            identity_only=identity_only,
            gssapi_auth=gssapi_auth,
            gssapi_keyex=gssapi_keyex,
            gssapi_delegate_creds=gssapi_delegate_creds,
            ssh_options=options
        )

    def set_local_execution(self) -> None:
        """Switch to local execution mode."""
        self.execution_mode = ExecutionMode.LOCAL
        self.remote_host = None

    def is_remote(self) -> bool:
        """Return True if the context is in REMOTE mode."""
        return self.execution_mode == ExecutionMode.REMOTE

    def clone(self) -> 'CommandContext':
        """Return a deep copy of this context."""
        import copy
        return copy.deepcopy(self)
