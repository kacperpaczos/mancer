from abc import abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Type
from copy import deepcopy
from ...domain.interface.command_interface import CommandInterface
from ...domain.model.command_result import CommandResult
from ...domain.model.command_context import CommandContext, ExecutionMode
from ..backend.bash_backend import BashBackend
from ..backend.ssh_backend import SshBackend

T = TypeVar('T', bound='BaseCommand')

class BaseCommand(CommandInterface):
    """Bazowa implementacja komendy"""
    
    def __init__(self, name: str):
        self.name = name
        self.options: List[str] = []
        self.parameters: Dict[str, Any] = {}
        self.flags: List[str] = []
        self.backend = BashBackend()  # Domyślny backend
        self.pipeline = None  # Opcjonalny pipeline (np. | grep)
        self.requires_sudo = False  # Czy komenda wymaga sudo
        self._args: List[str] = []  # Lista dodatkowych argumentów
    
    def with_option(self, option: str) -> T:
        """Dodaje opcję do komendy"""
        new_instance = self.clone()
        new_instance.options.append(option)
        return new_instance
    
    def with_param(self, name: str, value: Any) -> T:
        """Ustawia parametr komendy"""
        new_instance = self.clone()
        new_instance.parameters[name] = value
        return new_instance
    
    def with_flag(self, flag: str) -> T:
        """Dodaje flagę do komendy"""
        new_instance = self.clone()
        new_instance.flags.append(flag)
        return new_instance
    
    def with_sudo(self) -> T:
        """Oznacza, że komenda wymaga sudo"""
        new_instance = self.clone()
        new_instance.requires_sudo = True
        return new_instance
    
    def add_arg(self, arg: str) -> T:
        """Dodaje argument do komendy"""
        new_instance = self.clone()
        new_instance._args.append(arg)
        return new_instance
    
    def add_args(self, args: List[str]) -> T:
        """Dodaje wiele argumentów do komendy"""
        new_instance = self.clone()
        new_instance._args.extend(args)
        return new_instance
    
    def clone(self) -> T:
        """Tworzy kopię komendy z tą samą konfiguracją"""
        new_instance = self.__class__()
        new_instance.options = deepcopy(self.options)
        new_instance.parameters = deepcopy(self.parameters)
        new_instance.flags = deepcopy(self.flags)
        new_instance.pipeline = self.pipeline
        new_instance.requires_sudo = self.requires_sudo
        new_instance._args = deepcopy(self._args)
        return new_instance
    
    def build_command(self) -> str:
        """Buduje string komendy na podstawie konfiguracji"""
        cmd_parts = [self.name]
        
        # Dodajemy opcje (np. -l, -a)
        cmd_parts.extend(self.options)
        
        # Dodajemy flagi (np. --recursive)
        cmd_parts.extend(self.flags)
        
        # Dodajemy parametry
        for name, value in self.parameters.items():
            # Sprawdzamy, czy parametr ma specjalną obsługę
            param_str = self._format_parameter(name, value)
            if param_str:
                cmd_parts.append(param_str)
        
        # Dodajemy pozostałe argumenty specyficzne dla danej komendy
        additional_args = self._get_additional_args()
        if additional_args:
            cmd_parts.extend(additional_args)
        
        cmd_str = " ".join(cmd_parts)
        
        # Dodajemy pipeline, jeśli istnieje
        if self.pipeline:
            cmd_str = f"{cmd_str} | {self.pipeline}"
        
        return cmd_str
    
    def _get_backend(self, context: CommandContext):
        """Zwraca odpowiedni backend na podstawie kontekstu"""
        if context.is_remote():
            # Jeśli wykonujemy zdalnie, tworzymy backend SSH
            remote_host = context.remote_host
            return SshBackend(
                host=remote_host.host,
                user=remote_host.user,
                port=remote_host.port,
                key_file=remote_host.key_file,
                password=remote_host.password,
                use_sudo=remote_host.use_sudo or self.requires_sudo,
                sudo_password=remote_host.sudo_password,
                use_agent=remote_host.use_agent,
                certificate_file=remote_host.certificate_file,
                identity_only=remote_host.identity_only,
                gssapi_auth=remote_host.gssapi_auth,
                gssapi_keyex=remote_host.gssapi_keyex,
                gssapi_delegate_creds=remote_host.gssapi_delegate_creds,
                ssh_options=remote_host.ssh_options
            )
        else:
            # W przeciwnym razie używamy domyślnego backendu
            return self.backend
    
    @abstractmethod
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Implementacja wykonania komendy - do zaimplementowania w podklasach"""
        pass
    
    def _format_parameter(self, name: str, value: Any) -> str:
        """
        Formatuje pojedynczy parametr komendy.
        Można nadpisać w podklasach dla specjalnego formatowania.
        """
        return f"--{name}={value}"
    
    def _get_additional_args(self) -> List[str]:
        """
        Zwraca dodatkowe argumenty specyficzne dla podklasy.
        Do nadpisania w podklasach.
        """
        return self._args
    
    def _parse_output(self, raw_output: str) -> List[Any]:
        """
        Parsuje surowe wyjście komendy do struktury.
        Do nadpisania w podklasach.
        """
        return [raw_output]
    
    def then(self, next_command: CommandInterface) -> 'CommandChain':
        """Tworzy łańcuch komend"""
        from ...domain.service.command_chain_service import CommandChain
        chain = CommandChain(self)
        return chain.then(next_command)
    
    def pipe(self, next_command: CommandInterface) -> 'CommandChain':
        """Tworzy łańcuch komend z przekierowaniem wyjścia"""
        from ...domain.service.command_chain_service import CommandChain
        chain = CommandChain(self)
        return chain.pipe(next_command)
