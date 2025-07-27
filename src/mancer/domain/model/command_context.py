from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum, auto

class ExecutionMode(Enum):
    """Tryb wykonania komendy"""
    LOCAL = auto()  # Wykonanie lokalne
    REMOTE = auto()  # Wykonanie zdalne

@dataclass
class RemoteHostInfo:
    """Informacje o zdalnym hoście"""
    host: str
    user: Optional[str] = None
    port: int = 22
    
    # Metody uwierzytelniania
    key_file: Optional[str] = None
    password: Optional[str] = None
    use_agent: bool = False
    certificate_file: Optional[str] = None
    identity_only: bool = False
    gssapi_auth: bool = False
    gssapi_keyex: bool = False
    gssapi_delegate_creds: bool = False
    
    # Opcje sudo
    use_sudo: bool = False
    sudo_password: Optional[str] = None
    
    # Dodatkowe opcje SSH
    ssh_options: Dict[str, str] = field(default_factory=dict)

@dataclass
class CommandContext:
    """Kontekst wykonania komendy"""
    current_directory: str = "."
    environment_variables: Dict[str, str] = field(default_factory=dict)
    command_history: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    execution_mode: ExecutionMode = ExecutionMode.LOCAL
    remote_host: Optional[RemoteHostInfo] = None
    
    def change_directory(self, new_directory: str) -> None:
        """Zmienia bieżący katalog w kontekście"""
        self.current_directory = new_directory
        
    def add_to_history(self, command_string: str) -> None:
        """Dodaje komendę do historii"""
        self.command_history.append(command_string)
        
    def set_parameter(self, key: str, value: Any) -> None:
        """Ustawia parametr kontekstu"""
        self.parameters[key] = value
        
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Pobiera parametr kontekstu"""
        return self.parameters.get(key, default)
    
    def set_remote_execution(self, host: str, user: Optional[str] = None, 
                           port: int = 22, key_file: Optional[str] = None,
                           password: Optional[str] = None, use_sudo: bool = False,
                           sudo_password: Optional[str] = None, use_agent: bool = False,
                           certificate_file: Optional[str] = None, identity_only: bool = False,
                           gssapi_auth: bool = False, gssapi_keyex: bool = False,
                           gssapi_delegate_creds: bool = False,
                           ssh_options: Optional[Dict[str, str]] = None) -> None:
        """Ustawia tryb wykonania zdalnego
        
        Args:
            host: Nazwa hosta lub adres IP zdalnego serwera
            user: Nazwa użytkownika (opcjonalnie)
            port: Port SSH (domyślnie 22)
            key_file: Ścieżka do pliku klucza prywatnego (opcjonalnie)
            password: Hasło (opcjonalnie, niezalecane - lepiej używać kluczy)
            use_sudo: Czy automatycznie używać sudo dla komend, które tego wymagają
            sudo_password: Hasło do sudo (opcjonalnie)
            use_agent: Czy używać agenta SSH do uwierzytelniania
            certificate_file: Ścieżka do pliku certyfikatu SSH
            identity_only: Czy używać tylko podanego klucza/certyfikatu (IdentitiesOnly=yes)
            gssapi_auth: Czy używać uwierzytelniania GSSAPI (Kerberos)
            gssapi_keyex: Czy używać wymiany kluczy GSSAPI
            gssapi_delegate_creds: Czy delegować poświadczenia GSSAPI
            ssh_options: Dodatkowe opcje SSH jako słownik
        """
        self.execution_mode = ExecutionMode.REMOTE
        
        # Przygotowanie opcji SSH
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
        """Ustawia tryb wykonania lokalnego"""
        self.execution_mode = ExecutionMode.LOCAL
        self.remote_host = None
    
    def is_remote(self) -> bool:
        """Sprawdza, czy kontekst jest w trybie zdalnym"""
        return self.execution_mode == ExecutionMode.REMOTE
    
    def clone(self) -> 'CommandContext':
        """Tworzy kopię kontekstu"""
        import copy
        return copy.deepcopy(self)
