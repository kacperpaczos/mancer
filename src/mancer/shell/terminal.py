"""
Główny interfejs do komend powłoki.

Ten moduł dostarcza klasę Terminal, która jest głównym interfejsem do uruchamiania komend powłoki.
"""
from typing import Optional, Dict, Any, List, Union, Tuple
import os
import subprocess

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


class Terminal:
    """
    Główny interfejs do komend powłoki.
    
    Przykład użycia:
    ```python
    from mancer.shell import Terminal
    
    # Utworzenie instancji Terminal z domyślnym terminalem
    term = Terminal()
    
    # Listowanie plików
    result = term.ls("-la")
    print(result)
    
    # Wyszukiwanie plików
    files = term.find(".", "-name", "*.py")
    print(files)
    
    # Wykonanie dowolnej komendy
    output = term.run("echo 'Hello, World!'")
    print(output)
    
    # Użycie innego terminala
    custom_term = Terminal(terminal_type="zsh")
    result = custom_term.ls("-la")
    ```
    """
    
    def __init__(self, terminal_type: str = "bash", terminal_path: Optional[str] = None, 
                 terminal_options: Optional[Dict[str, Any]] = None):
        """
        Inicjalizuje instancję Terminal z określonym typem terminala.
        
        Args:
            terminal_type: Typ terminala (np. "bash", "zsh", "xterm")
            terminal_path: Ścieżka do pliku wykonywalnego terminala
            terminal_options: Dodatkowe opcje dla terminala
        """
        self.terminal_type = terminal_type
        self.terminal_path = terminal_path
        self.terminal_options = terminal_options or {}
        self._cwd: Optional[str] = None
    
    def _create_terminal_command(self) -> TerminalCommand:
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
            
        # Ustawienie katalogu roboczego
        if self._cwd:
            cmd.in_directory(self._cwd)
            
        return cmd
    
    def cd(self, path: str) -> None:
        """
        Zmienia katalog roboczy.
        
        Args:
            path: Ścieżka do katalogu
        """
        self._cwd = path
    
    def pwd(self) -> str:
        """
        Zwraca aktualny katalog roboczy.
        
        Returns:
            str: Aktualny katalog roboczy
        """
        if self._cwd:
            return self._cwd
        return self.run("pwd").strip()
    
    def ls(self, *args: str) -> str:
        """
        Listuje zawartość katalogu.
        
        Args:
            *args: Argumenty dla komendy ls
            
        Returns:
            str: Wynik wykonania komendy ls
        """
        cmd = "ls"
        if args:
            cmd += " " + " ".join(args)
        return self.run(cmd)
    
    def find(self, path: str, *args: str) -> List[str]:
        """
        Wyszukuje pliki w katalogu.
        
        Args:
            path: Ścieżka do katalogu
            *args: Argumenty dla komendy find
            
        Returns:
            List[str]: Lista znalezionych plików
        """
        cmd = f"find {path}"
        if args:
            cmd += " " + " ".join(args)
        result = self.run(cmd)
        return [line.strip() for line in result.splitlines() if line.strip()]
    
    def grep(self, pattern: str, file: Optional[str] = None, *args: str) -> List[str]:
        """
        Wyszukuje wzorzec w pliku lub katalogu.
        
        Args:
            pattern: Wzorzec do wyszukania
            file: Ścieżka do pliku lub katalogu
            *args: Dodatkowe argumenty dla komendy grep
            
        Returns:
            List[str]: Lista znalezionych linii
        """
        cmd = f"grep {pattern}"
        if args:
            cmd += " " + " ".join(args)
        if file:
            cmd += f" {file}"
        result = self.run(cmd)
        return [line.strip() for line in result.splitlines() if line.strip()]
    
    def cp(self, source: str, destination: str, *args: str) -> None:
        """
        Kopiuje plik lub katalog.
        
        Args:
            source: Ścieżka źródłowa
            destination: Ścieżka docelowa
            *args: Dodatkowe argumenty dla komendy cp
        """
        cmd = f"cp"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {source} {destination}"
        self.run(cmd)
    
    def mv(self, source: str, destination: str, *args: str) -> None:
        """
        Przenosi plik lub katalog.
        
        Args:
            source: Ścieżka źródłowa
            destination: Ścieżka docelowa
            *args: Dodatkowe argumenty dla komendy mv
        """
        cmd = f"mv"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {source} {destination}"
        self.run(cmd)
    
    def rm(self, path: str, *args: str) -> None:
        """
        Usuwa plik lub katalog.
        
        Args:
            path: Ścieżka do usunięcia
            *args: Dodatkowe argumenty dla komendy rm
        """
        cmd = f"rm"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {path}"
        self.run(cmd)
    
    def mkdir(self, path: str, *args: str) -> None:
        """
        Tworzy katalog.
        
        Args:
            path: Ścieżka do katalogu
            *args: Dodatkowe argumenty dla komendy mkdir
        """
        cmd = f"mkdir"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {path}"
        self.run(cmd)
    
    def rmdir(self, path: str, *args: str) -> None:
        """
        Usuwa pusty katalog.
        
        Args:
            path: Ścieżka do katalogu
            *args: Dodatkowe argumenty dla komendy rmdir
        """
        cmd = f"rmdir"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {path}"
        self.run(cmd)
    
    def touch(self, path: str, *args: str) -> None:
        """
        Tworzy pusty plik lub aktualizuje datę modyfikacji.
        
        Args:
            path: Ścieżka do pliku
            *args: Dodatkowe argumenty dla komendy touch
        """
        cmd = f"touch"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {path}"
        self.run(cmd)
    
    def cat(self, path: str, *args: str) -> str:
        """
        Wyświetla zawartość pliku.
        
        Args:
            path: Ścieżka do pliku
            *args: Dodatkowe argumenty dla komendy cat
            
        Returns:
            str: Zawartość pliku
        """
        cmd = f"cat"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {path}"
        return self.run(cmd)
    
    def echo(self, text: str, *args: str) -> str:
        """
        Wyświetla tekst.
        
        Args:
            text: Tekst do wyświetlenia
            *args: Dodatkowe argumenty dla komendy echo
            
        Returns:
            str: Wynik wykonania komendy echo
        """
        cmd = f"echo"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {text}"
        return self.run(cmd)
    
    def sed(self, pattern: str, file: str, *args: str) -> str:
        """
        Edytuje strumień tekstu.
        
        Args:
            pattern: Wzorzec zamiany
            file: Ścieżka do pliku
            *args: Dodatkowe argumenty dla komendy sed
            
        Returns:
            str: Wynik wykonania komendy sed
        """
        cmd = f"sed"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" '{pattern}' {file}"
        return self.run(cmd)
    
    def awk(self, pattern: str, file: Optional[str] = None, *args: str) -> str:
        """
        Przetwarza i analizuje tekst.
        
        Args:
            pattern: Wzorzec przetwarzania
            file: Ścieżka do pliku
            *args: Dodatkowe argumenty dla komendy awk
            
        Returns:
            str: Wynik wykonania komendy awk
        """
        cmd = f"awk '{pattern}'"
        if args:
            cmd += " " + " ".join(args)
        if file:
            cmd += f" {file}"
        return self.run(cmd)
    
    def cut(self, file: str, *args: str) -> str:
        """
        Wycina fragmenty linii.
        
        Args:
            file: Ścieżka do pliku
            *args: Argumenty dla komendy cut
            
        Returns:
            str: Wynik wykonania komendy cut
        """
        cmd = f"cut"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {file}"
        return self.run(cmd)
    
    def sort(self, file: Optional[str] = None, *args: str) -> str:
        """
        Sortuje linie tekstu.
        
        Args:
            file: Ścieżka do pliku
            *args: Argumenty dla komendy sort
            
        Returns:
            str: Wynik wykonania komendy sort
        """
        cmd = f"sort"
        if args:
            cmd += " " + " ".join(args)
        if file:
            cmd += f" {file}"
        return self.run(cmd)
    
    def uniq(self, file: Optional[str] = None, *args: str) -> str:
        """
        Usuwa powtarzające się linie.
        
        Args:
            file: Ścieżka do pliku
            *args: Argumenty dla komendy uniq
            
        Returns:
            str: Wynik wykonania komendy uniq
        """
        cmd = f"uniq"
        if args:
            cmd += " " + " ".join(args)
        if file:
            cmd += f" {file}"
        return self.run(cmd)
    
    def wc(self, file: Optional[str] = None, *args: str) -> str:
        """
        Liczy linie, słowa i znaki.
        
        Args:
            file: Ścieżka do pliku
            *args: Argumenty dla komendy wc
            
        Returns:
            str: Wynik wykonania komendy wc
        """
        cmd = f"wc"
        if args:
            cmd += " " + " ".join(args)
        if file:
            cmd += f" {file}"
        return self.run(cmd)
    
    def head(self, file: str, *args: str) -> str:
        """
        Wyświetla początek pliku.
        
        Args:
            file: Ścieżka do pliku
            *args: Argumenty dla komendy head
            
        Returns:
            str: Wynik wykonania komendy head
        """
        cmd = f"head"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {file}"
        return self.run(cmd)
    
    def tail(self, file: str, *args: str) -> str:
        """
        Wyświetla koniec pliku.
        
        Args:
            file: Ścieżka do pliku
            *args: Argumenty dla komendy tail
            
        Returns:
            str: Wynik wykonania komendy tail
        """
        cmd = f"tail"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {file}"
        return self.run(cmd)
    
    def ping(self, host: str, *args: str) -> str:
        """
        Pinguje host.
        
        Args:
            host: Nazwa hosta lub adres IP
            *args: Dodatkowe argumenty dla komendy ping
            
        Returns:
            str: Wynik wykonania komendy ping
        """
        cmd = f"ping"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {host}"
        return self.run(cmd)
    
    def ssh(self, host: str, *args: str) -> str:
        """
        Łączy się z hostem przez SSH.
        
        Args:
            host: Nazwa hosta lub adres IP
            *args: Dodatkowe argumenty dla komendy ssh
            
        Returns:
            str: Wynik wykonania komendy ssh
        """
        cmd = f"ssh"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {host}"
        return self.run(cmd)
    
    def scp(self, source: str, destination: str, *args: str) -> str:
        """
        Kopiuje pliki przez SSH.
        
        Args:
            source: Ścieżka źródłowa
            destination: Ścieżka docelowa
            *args: Dodatkowe argumenty dla komendy scp
            
        Returns:
            str: Wynik wykonania komendy scp
        """
        cmd = f"scp"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {source} {destination}"
        return self.run(cmd)
    
    def rsync(self, source: str, destination: str, *args: str) -> str:
        """
        Synchronizuje pliki.
        
        Args:
            source: Ścieżka źródłowa
            destination: Ścieżka docelowa
            *args: Dodatkowe argumenty dla komendy rsync
            
        Returns:
            str: Wynik wykonania komendy rsync
        """
        cmd = f"rsync"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {source} {destination}"
        return self.run(cmd)
    
    def curl(self, url: str, *args: str) -> str:
        """
        Pobiera zawartość URL.
        
        Args:
            url: URL docelowy
            *args: Dodatkowe argumenty dla komendy curl
            
        Returns:
            str: Wynik wykonania komendy curl
        """
        cmd = f"curl"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {url}"
        return self.run(cmd)
    
    def wget(self, url: str, *args: str) -> str:
        """
        Pobiera pliki z sieci.
        
        Args:
            url: URL docelowy
            *args: Dodatkowe argumenty dla komendy wget
            
        Returns:
            str: Wynik wykonania komendy wget
        """
        cmd = f"wget"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {url}"
        return self.run(cmd)
    
    def ps(self, *args: str) -> str:
        """
        Wyświetla procesy.
        
        Args:
            *args: Argumenty dla komendy ps
            
        Returns:
            str: Wynik wykonania komendy ps
        """
        cmd = "ps"
        if args:
            cmd += " " + " ".join(args)
        return self.run(cmd)
    
    def kill(self, pid: Union[int, str], *args: str) -> None:
        """
        Zabija proces.
        
        Args:
            pid: Identyfikator procesu
            *args: Dodatkowe argumenty dla komendy kill
        """
        cmd = f"kill"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {pid}"
        self.run(cmd)
    
    def killall(self, process_name: str, *args: str) -> None:
        """
        Zabija procesy o podanej nazwie.
        
        Args:
            process_name: Nazwa procesu
            *args: Dodatkowe argumenty dla komendy killall
        """
        cmd = f"killall"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {process_name}"
        self.run(cmd)
    
    def top(self, *args: str) -> str:
        """
        Wyświetla aktywne procesy.
        
        Args:
            *args: Argumenty dla komendy top
            
        Returns:
            str: Wynik wykonania komendy top
        """
        cmd = "top"
        if args:
            cmd += " " + " ".join(args)
        cmd += " -b -n 1"  # Tryb wsadowy, jedno wykonanie
        return self.run(cmd)
    
    def df(self, *args: str) -> str:
        """
        Wyświetla użycie dysku.
        
        Args:
            *args: Argumenty dla komendy df
            
        Returns:
            str: Wynik wykonania komendy df
        """
        cmd = "df"
        if args:
            cmd += " " + " ".join(args)
        return self.run(cmd)
    
    def du(self, path: Optional[str] = None, *args: str) -> str:
        """
        Wyświetla użycie dysku przez katalogi.
        
        Args:
            path: Ścieżka do katalogu
            *args: Argumenty dla komendy du
            
        Returns:
            str: Wynik wykonania komendy du
        """
        cmd = "du"
        if args:
            cmd += " " + " ".join(args)
        if path:
            cmd += f" {path}"
        return self.run(cmd)
    
    def free(self, *args: str) -> str:
        """
        Wyświetla użycie pamięci.
        
        Args:
            *args: Argumenty dla komendy free
            
        Returns:
            str: Wynik wykonania komendy free
        """
        cmd = "free"
        if args:
            cmd += " " + " ".join(args)
        return self.run(cmd)
    
    def uname(self, *args: str) -> str:
        """
        Wyświetla informacje o systemie.
        
        Args:
            *args: Argumenty dla komendy uname
            
        Returns:
            str: Wynik wykonania komendy uname
        """
        cmd = "uname"
        if args:
            cmd += " " + " ".join(args)
        return self.run(cmd)
    
    def chmod(self, mode: str, path: str, *args: str) -> None:
        """
        Zmienia uprawnienia pliku.
        
        Args:
            mode: Tryb uprawnień (np. "755")
            path: Ścieżka do pliku
            *args: Dodatkowe argumenty dla komendy chmod
        """
        cmd = f"chmod"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {mode} {path}"
        self.run(cmd)
    
    def chown(self, owner: str, path: str, *args: str) -> None:
        """
        Zmienia właściciela pliku.
        
        Args:
            owner: Nowy właściciel (np. "user:group")
            path: Ścieżka do pliku
            *args: Dodatkowe argumenty dla komendy chown
        """
        cmd = f"chown"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {owner} {path}"
        self.run(cmd)
    
    def tar(self, *args: str) -> str:
        """
        Archiwizuje pliki.
        
        Args:
            *args: Argumenty dla komendy tar
            
        Returns:
            str: Wynik wykonania komendy tar
        """
        cmd = "tar"
        if args:
            cmd += " " + " ".join(args)
        return self.run(cmd)
    
    def gzip(self, file: str, *args: str) -> None:
        """
        Kompresuje pliki.
        
        Args:
            file: Ścieżka do pliku
            *args: Dodatkowe argumenty dla komendy gzip
        """
        cmd = f"gzip"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {file}"
        self.run(cmd)
    
    def gunzip(self, file: str, *args: str) -> None:
        """
        Dekompresuje pliki gzip.
        
        Args:
            file: Ścieżka do pliku
            *args: Dodatkowe argumenty dla komendy gunzip
        """
        cmd = f"gunzip"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {file}"
        self.run(cmd)
    
    def zip(self, archive: str, files: Union[str, List[str]], *args: str) -> None:
        """
        Tworzy archiwum ZIP.
        
        Args:
            archive: Nazwa archiwum
            files: Pliki do dodania do archiwum
            *args: Dodatkowe argumenty dla komendy zip
        """
        cmd = f"zip"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {archive}"
        if isinstance(files, list):
            cmd += " " + " ".join(files)
        else:
            cmd += f" {files}"
        self.run(cmd)
    
    def unzip(self, archive: str, *args: str) -> None:
        """
        Rozpakowuje archiwum ZIP.
        
        Args:
            archive: Nazwa archiwum
            *args: Dodatkowe argumenty dla komendy unzip
        """
        cmd = f"unzip"
        if args:
            cmd += " " + " ".join(args)
        cmd += f" {archive}"
        self.run(cmd)
    
    def date(self, *args: str) -> str:
        """
        Wyświetla lub ustawia datę i czas.
        
        Args:
            *args: Argumenty dla komendy date
            
        Returns:
            str: Wynik wykonania komendy date
        """
        cmd = "date"
        if args:
            cmd += " " + " ".join(args)
        return self.run(cmd)
    
    def run(self, command: str) -> str:
        """
        Wykonuje komendę w terminalu i zwraca wynik.
        
        Args:
            command: Komenda do wykonania
            
        Returns:
            str: Wynik wykonania komendy
        """
        cmd = self._create_terminal_command().execute(command)
        result = cmd.run()
        return result.stdout 