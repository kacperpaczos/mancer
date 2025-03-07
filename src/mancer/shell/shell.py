"""
Główny interfejs do komend powłoki.

Ten moduł dostarcza jednolity interfejs do wszystkich komend powłoki.
Zamiast importować różne klasy z różnych modułów, programista może
korzystać z tego jednego interfejsu.
"""
from typing import Optional, Dict, Any, List

from mancer.shell.commands.terminal.terminal import TerminalCommand
from mancer.shell.commands.file.file_operations import FileCommand
from mancer.shell.commands.system.process import ProcessCommand
from mancer.shell.commands.grep import Grep
from mancer.shell.commands.find import Find
from mancer.shell.commands.ls import Ls
from mancer.shell.commands.sed import Sed
from mancer.shell.commands.network.curl import CurlCommand
from mancer.shell.commands.network.ping import PingCommand
from mancer.shell.commands.network.ssh import SSHCommand


class Shell:
    """
    Główny interfejs do komend powłoki.
    
    Przykład użycia:
    ```python
    from mancer.shell import Shell
    
    # Utworzenie instancji Shell z domyślnym terminalem
    shell = Shell()
    
    # Wykonanie komendy w terminalu
    result = shell.terminal().execute("ls -la").run()
    
    # Kopiowanie pliku
    shell.file().copy("/path/source", "/path/dest").run()
    
    # Pingowanie hosta
    shell.ping().to("example.com").with_count(5).run()
    
    # Użycie innego terminala
    custom_shell = Shell(terminal_type="xterm")
    result = custom_shell.terminal().execute("ls -la").run()
    ```
    """
    
    def __init__(self, terminal_type: str = "bash", terminal_path: Optional[str] = None, 
                 terminal_options: Optional[Dict[str, Any]] = None):
        """
        Inicjalizuje instancję Shell z określonym typem terminala.
        
        Args:
            terminal_type: Typ terminala (np. "bash", "zsh", "xterm")
            terminal_path: Ścieżka do pliku wykonywalnego terminala
            terminal_options: Dodatkowe opcje dla terminala
        """
        self.terminal_type = terminal_type
        self.terminal_path = terminal_path
        self.terminal_options = terminal_options or {}
    
    def terminal(self) -> TerminalCommand:
        """
        Tworzy nową instancję komendy terminala.
        
        Returns:
            TerminalCommand: Nowa instancja komendy terminala
        """
        cmd = TerminalCommand()
        
        # Ustawienie odpowiedniego terminala
        if self.terminal_path:
            cmd.with_env("SHELL", self.terminal_path)
        
        # Dodanie opcji terminala
        for key, value in self.terminal_options.items():
            cmd.with_env(key, str(value))
            
        return cmd
    
    def file(self) -> FileCommand:
        """
        Tworzy nową instancję komendy operacji na plikach.
        
        Returns:
            FileCommand: Nowa instancja komendy operacji na plikach
        """
        return FileCommand()
    
    def process(self) -> ProcessCommand:
        """
        Tworzy nową instancję komendy zarządzania procesami.
        
        Returns:
            ProcessCommand: Nowa instancja komendy zarządzania procesami
        """
        return ProcessCommand()
    
    def grep(self) -> Grep:
        """
        Tworzy nową instancję komendy grep.
        
        Returns:
            Grep: Nowa instancja komendy grep
        """
        return Grep()
    
    def find(self) -> Find:
        """
        Tworzy nową instancję komendy find.
        
        Returns:
            Find: Nowa instancja komendy find
        """
        return Find()
    
    def ls(self) -> Ls:
        """
        Tworzy nową instancję komendy ls.
        
        Returns:
            Ls: Nowa instancja komendy ls
        """
        return Ls()
    
    def sed(self) -> Sed:
        """
        Tworzy nową instancję komendy sed.
        
        Returns:
            Sed: Nowa instancja komendy sed
        """
        return Sed()
    
    def curl(self) -> CurlCommand:
        """
        Tworzy nową instancję komendy curl.
        
        Returns:
            CurlCommand: Nowa instancja komendy curl
        """
        return CurlCommand()
    
    def ping(self) -> PingCommand:
        """
        Tworzy nową instancję komendy ping.
        
        Returns:
            PingCommand: Nowa instancja komendy ping
        """
        return PingCommand()
    
    def ssh(self) -> SSHCommand:
        """
        Tworzy nową instancję komendy ssh.
        
        Returns:
            SSHCommand: Nowa instancja komendy ssh
        """
        return SSHCommand()
    
    def run(self, command: str, cwd: Optional[str] = None) -> str:
        """
        Szybkie wykonanie komendy w terminalu i zwrócenie wyniku.
        
        Args:
            command: Komenda do wykonania
            cwd: Katalog roboczy (opcjonalnie)
            
        Returns:
            str: Wynik wykonania komendy
        """
        cmd = self.terminal().execute(command)
        if cwd:
            cmd.in_directory(cwd)
        result = cmd.run()
        return result.stdout
        
    # Statyczne metody dla wygody użycia bez tworzenia instancji
    
    @staticmethod
    def create(terminal_type: str = "bash", terminal_path: Optional[str] = None, 
               terminal_options: Optional[Dict[str, Any]] = None) -> 'Shell':
        """
        Tworzy nową instancję Shell z określonym typem terminala.
        
        Args:
            terminal_type: Typ terminala (np. "bash", "zsh", "xterm")
            terminal_path: Ścieżka do pliku wykonywalnego terminala
            terminal_options: Dodatkowe opcje dla terminala
            
        Returns:
            Shell: Nowa instancja Shell
        """
        return Shell(terminal_type, terminal_path, terminal_options) 