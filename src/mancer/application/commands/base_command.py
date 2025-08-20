from typing import Any, Dict, List, Optional, TypeVar, cast

from ...domain.interface.command_interface import CommandInterface
from ...domain.model.command_context import CommandContext
from ...domain.model.command_result import CommandResult

T = TypeVar('T', bound='BaseCommand')

class BaseCommand(CommandInterface[T]):
    """Bazowa klasa dla wszystkich komend w frameworku"""
    
    def __init__(self, command_name: str):
        """
        Inicjalizuje komendę.
        
        Args:
            command_name: Nazwa komendy (np. 'apt', 'ls', 'ps')
        """
        self._command_name = command_name
        self._params: Dict[str, Any] = {}
        self._options: List[str] = []
    
    def with_param(self, name: str, value: Any) -> T:
        """
        Dodaje parametr do komendy.
        
        Args:
            name: Nazwa parametru
            value: Wartość parametru
            
        Returns:
            self: Instancja komendy (do łańcuchowania metod)
        """
        self._params[name] = value
        return cast(T, self)
    
    def with_option(self, option: str) -> T:
        """
        Dodaje opcję (flag) do komendy.
        
        Args:
            option: Nazwa opcji (bez myślników)
            
        Returns:
            self: Instancja komendy (do łańcuchowania metod)
        """
        self._options.append(option)
        return cast(T, self)
    
    def build_command(self) -> str:
        """
        Buduje pełną komendę z parametrami.
        
        Returns:
            str: Pełna komenda gotowa do wykonania
        """
        parts = [self._command_name]
        
        # Dodaj parametry w odpowiedniej kolejności
        if "command" in self._params:
            parts.append(str(self._params["command"]))
        
        # Dodaj opcje
        for option in self._options:
            if len(option) == 1:
                parts.append(f"-{option}")
            else:
                parts.append(f"--{option}")
        
        # Dodaj pozostałe parametry
        for name, value in self._params.items():
            if name == "command":
                continue
                
            if isinstance(value, bool):
                if value:
                    parts.append(f"--{name}")
            elif name == "package" or name == "query":
                # Specjalna obsługa dla pakietów i wyszukiwania
                parts.append(str(value))
            else:
                parts.append(f"--{name}")
                parts.append(str(value))
        
        return " ".join(parts)
    
    def execute(self, context: CommandContext, 
                input_result: Optional[CommandResult] = None) -> CommandResult:
        """
        Wykonuje komendę w podanym kontekście.
        
        Args:
            context: Kontekst wykonania komendy
            input_result: Opcjonalny wynik poprzedniej komendy (dla potoków)
            
        Returns:
            CommandResult: Wynik wykonania komendy
        """
        # Budujemy komendę
        command_str = self.build_command()
        
        # Dodajemy komendę do historii
        context.add_to_history(command_str)
        
        # Przekazuj wejście z poprzedniej komendy, jeśli istnieje
        stdin = input_result.raw_output if input_result else None
        
        # Pobieramy odpowiedni backend
        if context.is_remote():
            from ...infrastructure.backend.ssh_backend import SshBackend
            # Tworzymy backend SSH z informacjami o hoście
            backend = SshBackend(
                host=context.remote_host.host,
                user=context.remote_host.user,
                port=context.remote_host.port,
                key_file=context.remote_host.key_file,
                password=context.remote_host.password,
                use_sudo=context.remote_host.use_sudo,
                sudo_password=context.remote_host.sudo_password
            )
        else:
            from ...infrastructure.backend.bash_backend import BashBackend
            backend = BashBackend()
        
        # Wykonujemy komendę
        return backend.execute_command(
            command_str, 
            context.current_directory, 
            context.environment_variables,
            context.parameters,  # Przekazujemy wszystkie parametry kontekstu
            stdin
        )
    
    def clone(self) -> T:
        """
        Tworzy kopię komendy z tą samą konfiguracją.
        
        Returns:
            Nowa instancja komendy z tą samą konfiguracją
        """
        # Tworzymy nową instancję tej samej klasy
        new_command = self.__class__(self._command_name)
        
        # Kopiujemy parametry i opcje
        new_command._params = self._params.copy()
        new_command._options = self._options.copy()
        
        return cast(T, new_command)
    
    def __str__(self) -> str:
        """Zwraca reprezentację tekstową komendy"""
        return self.build_command() 