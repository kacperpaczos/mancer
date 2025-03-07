"""
Funkcje skrótowe dla najczęściej używanych komend powłoki.

Ten moduł dostarcza funkcje skrótowe, które upraszczają korzystanie z komend powłoki.
"""
import os
from typing import List, Dict, Optional, Any, Union

from mancer.shell.shell import Shell

# Domyślna instancja Shell
_default_shell = Shell()


def run(command: str, cwd: Optional[str] = None, shell: Optional[Shell] = None) -> str:
    """
    Wykonuje komendę w terminalu i zwraca wynik.
    
    Args:
        command: Komenda do wykonania
        cwd: Katalog roboczy (opcjonalnie)
        shell: Instancja Shell do użycia (opcjonalnie)
        
    Returns:
        str: Wynik wykonania komendy
    """
    shell = shell or _default_shell
    return shell.run(command, cwd)


def ls(path: str = ".", all_files: bool = False, long_format: bool = False, shell: Optional[Shell] = None) -> str:
    """
    Listuje zawartość katalogu.
    
    Args:
        path: Ścieżka do katalogu
        all_files: Czy pokazać wszystkie pliki (włącznie z ukrytymi)
        long_format: Czy użyć długiego formatu wyświetlania
        shell: Instancja Shell do użycia (opcjonalnie)
        
    Returns:
        str: Wynik wykonania komendy ls
    """
    shell = shell or _default_shell
    cmd = shell.ls().in_path(path)
    if all_files:
        cmd.show_all()
    if long_format:
        cmd.long_format()
    return cmd.run().stdout


def find(path: str = ".", name: Optional[str] = None, file_type: Optional[str] = None, shell: Optional[Shell] = None) -> List[str]:
    """
    Wyszukuje pliki w katalogu.
    
    Args:
        path: Ścieżka do katalogu
        name: Wzorzec nazwy pliku
        file_type: Typ pliku (f - zwykły plik, d - katalog)
        shell: Instancja Shell do użycia (opcjonalnie)
        
    Returns:
        List[str]: Lista znalezionych plików
    """
    shell = shell or _default_shell
    cmd = shell.find().in_path(path)
    if name:
        cmd.by_name(name)
    if file_type:
        cmd.of_type(file_type)
    result = cmd.run().stdout
    return [line.strip() for line in result.splitlines() if line.strip()]


def grep(pattern: str, file: Optional[str] = None, recursive: bool = False, shell: Optional[Shell] = None) -> List[str]:
    """
    Wyszukuje wzorzec w pliku lub katalogu.
    
    Args:
        pattern: Wzorzec do wyszukania
        file: Ścieżka do pliku lub katalogu
        recursive: Czy przeszukiwać rekurencyjnie
        shell: Instancja Shell do użycia (opcjonalnie)
        
    Returns:
        List[str]: Lista znalezionych linii
    """
    shell = shell or _default_shell
    cmd = shell.grep().search(pattern)
    if file:
        cmd.in_file(file)
    if recursive:
        cmd.recursively()
    result = cmd.run().stdout
    return [line.strip() for line in result.splitlines() if line.strip()]


def copy(source: str, destination: str, recursive: bool = False, force: bool = False, shell: Optional[Shell] = None) -> None:
    """
    Kopiuje plik lub katalog.
    
    Args:
        source: Ścieżka źródłowa
        destination: Ścieżka docelowa
        recursive: Czy kopiować rekurencyjnie
        force: Czy wymuszać kopiowanie bez potwierdzenia
        shell: Instancja Shell do użycia (opcjonalnie)
    """
    shell = shell or _default_shell
    cmd = shell.file().copy(source, destination)
    if recursive:
        cmd.recursively()
    if force:
        cmd.force()
    cmd.run()


def move(source: str, destination: str, force: bool = False, shell: Optional[Shell] = None) -> None:
    """
    Przenosi plik lub katalog.
    
    Args:
        source: Ścieżka źródłowa
        destination: Ścieżka docelowa
        force: Czy wymuszać przenoszenie bez potwierdzenia
        shell: Instancja Shell do użycia (opcjonalnie)
    """
    shell = shell or _default_shell
    cmd = shell.file().move(source, destination)
    if force:
        cmd.force()
    cmd.run()


def remove(path: str, recursive: bool = False, force: bool = False, shell: Optional[Shell] = None) -> None:
    """
    Usuwa plik lub katalog.
    
    Args:
        path: Ścieżka do usunięcia
        recursive: Czy usuwać rekurencyjnie
        force: Czy wymuszać usuwanie bez potwierdzenia
        shell: Instancja Shell do użycia (opcjonalnie)
    """
    shell = shell or _default_shell
    cmd = shell.file().remove(path)
    if recursive:
        cmd.recursively()
    if force:
        cmd.force()
    cmd.run()


def ping(host: str, count: Optional[int] = None, shell: Optional[Shell] = None) -> str:
    """
    Pinguje host.
    
    Args:
        host: Nazwa hosta lub adres IP
        count: Liczba pakietów do wysłania
        shell: Instancja Shell do użycia (opcjonalnie)
        
    Returns:
        str: Wynik wykonania komendy ping
    """
    shell = shell or _default_shell
    cmd = shell.ping().to(host)
    if count:
        cmd.with_count(count)
    return cmd.run().stdout


def ssh(host: str, command: Optional[str] = None, username: Optional[str] = None, 
        port: int = 22, key_file: Optional[str] = None, shell: Optional[Shell] = None) -> str:
    """
    Łączy się z hostem przez SSH.
    
    Args:
        host: Nazwa hosta lub adres IP
        command: Komenda do wykonania na zdalnym hoście
        username: Nazwa użytkownika
        port: Numer portu SSH
        key_file: Ścieżka do pliku klucza prywatnego
        shell: Instancja Shell do użycia (opcjonalnie)
        
    Returns:
        str: Wynik wykonania komendy SSH
    """
    shell = shell or _default_shell
    cmd = shell.ssh().to(host)
    if username:
        cmd.as_user(username)
    if port != 22:
        cmd.on_port(port)
    if key_file:
        cmd.with_key(key_file)
    if command:
        cmd.run_command(command)
    return cmd.run().stdout


def curl(url: str, method: str = "GET", data: Optional[str] = None, 
         headers: Optional[Dict[str, str]] = None, output_file: Optional[str] = None, 
         shell: Optional[Shell] = None) -> str:
    """
    Wykonuje żądanie HTTP.
    
    Args:
        url: URL docelowy
        method: Metoda HTTP (GET, POST, PUT, DELETE, etc.)
        data: Dane żądania
        headers: Nagłówki HTTP
        output_file: Ścieżka do pliku wyjściowego
        shell: Instancja Shell do użycia (opcjonalnie)
        
    Returns:
        str: Wynik wykonania komendy curl
    """
    shell = shell or _default_shell
    cmd = shell.curl().to(url).using_method(method)
    if data:
        cmd.with_data(data)
    if headers:
        for name, value in headers.items():
            cmd.with_header(name, value)
    if output_file:
        cmd.save_to(output_file)
    return cmd.run().stdout 