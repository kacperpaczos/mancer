from abc import abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Type
from copy import deepcopy
from ...domain.interface.command_interface import CommandInterface
from ...domain.model.command_result import CommandResult
from ...domain.model.command_context import CommandContext, ExecutionMode
from ...domain.model.data_format import DataFormat
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
        self.preferred_data_format: DataFormat = DataFormat.LIST  # Preferowany format danych
    
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
        """Dodaje listę argumentów do komendy"""
        new_instance = self.clone()
        new_instance._args.extend(args)
        return new_instance
    
    def with_data_format(self, format_type: DataFormat) -> T:
        """Ustawia preferowany format danych wyjściowych komendy"""
        new_instance = self.clone()
        new_instance.preferred_data_format = format_type
        return new_instance
    
    def clone(self) -> T:
        """Tworzy kopię instancji komendy"""
        new_instance = type(self)()  # Wywołaj bezargumentowy konstruktor
        new_instance.name = self.name  # Przepisz nazwę komendy
        new_instance.options = deepcopy(self.options)
        new_instance.parameters = deepcopy(self.parameters)
        new_instance.flags = deepcopy(self.flags)
        new_instance.backend = self.backend
        new_instance.pipeline = self.pipeline
        new_instance.requires_sudo = self.requires_sudo
        new_instance._args = deepcopy(self._args)
        new_instance.preferred_data_format = self.preferred_data_format
        return new_instance
    
    def build_command(self) -> str:
        """Buduje string komendy"""
        cmd_parts = []
        
        # Dodaj sudo jeśli wymagane
        if self.requires_sudo:
            cmd_parts.append("sudo")
            
        # Dodaj nazwę komendy
        cmd_parts.append(self.name)
        
        # Dodaj opcje
        cmd_parts.extend(self.options)
        
        # Dodaj parametry
        for name, value in self.parameters.items():
            cmd_parts.append(self._format_parameter(name, value))
            
        # Dodaj flagi
        cmd_parts.extend([f"--{flag}" for flag in self.flags])
        
        # Dodaj dodatkowe argumenty
        cmd_parts.extend(self._get_additional_args())
        
        # Dodaj pipeline jeśli istnieje
        if self.pipeline:
            cmd_parts.append(self.pipeline)
            
        return " ".join(cmd_parts)
    
    def _get_backend(self, context: CommandContext):
        """
        Wybiera odpowiedni backend na podstawie kontekstu.
        """
        # Jeśli kontekst wskazuje na tryb zdalny, użyj SSH
        if (context.execution_mode == ExecutionMode.REMOTE 
            and context.remote_host is not None):
            
            remote_host = context.remote_host
            
            return SshBackend(
                hostname=remote_host.hostname,
                username=remote_host.username,
                password=remote_host.password,
                port=remote_host.port,
                key_filename=remote_host.key_filename,
                passphrase=remote_host.passphrase,
                allow_agent=remote_host.allow_agent,
                look_for_keys=remote_host.look_for_keys,
                compress=remote_host.compress, 
                timeout=remote_host.timeout,
                gssapi_auth=remote_host.gssapi_auth,
                gssapi_kex=remote_host.gssapi_kex,
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
    
    def _prepare_result(self, raw_output: str, success: bool, exit_code: int = 0, 
                       error_message: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> CommandResult:
        """
        Przygotowuje wynik komendy z uwzględnieniem preferowanego formatu danych i historii.
        """
        # Parsuj dane wyjściowe
        structured_output = self._parse_output(raw_output)
        
        # Utwórz obiekt wyniku
        result = CommandResult(
            raw_output=raw_output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_message,
            metadata=metadata,
            data_format=self.preferred_data_format
        )
        
        # Dodaj krok do historii
        result.add_to_history(
            command_string=self.build_command(),
            command_type=self.__class__.__name__,
            structured_sample=structured_output[:5] if structured_output else None
        )
        
        # Jeśli format danych jest inny niż LIST, dokonaj konwersji
        if self.preferred_data_format != DataFormat.LIST:
            return result.to_format(self.preferred_data_format)
            
        return result
    
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
