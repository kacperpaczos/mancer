"""Ping command implementation."""
import subprocess
import sys
import platform
from typing import Optional, List, Dict, Any

from mancer.core.interfaces.command import CommandBuilder


class PingCommand(CommandBuilder['PingCommand']):
    """Ping command builder."""

    def __init__(self) -> None:
        """Initialize Ping command."""
        self.host: Optional[str] = None
        self.count: Optional[int] = None
        self.timeout: Optional[int] = None
        self.interval: Optional[float] = None
        self.size: Optional[int] = None
        self.ttl: Optional[int] = None
        self.interface: Optional[str] = None
        self.ipv6: bool = False

    def to(self, host: str) -> 'PingCommand':
        """Set target host.
        
        Args:
            host: Nazwa hosta lub adres IP do pingowania
            
        Returns:
            PingCommand: Instancja bieżącego obiektu dla chain-callingu
        """
        self.host = host
        return self

    def with_count(self, count: int) -> 'PingCommand':
        """Set number of packets to send.
        
        Args:
            count: Liczba pakietów do wysłania
            
        Returns:
            PingCommand: Instancja bieżącego obiektu dla chain-callingu
        """
        self.count = count
        return self

    def with_timeout(self, timeout: int) -> 'PingCommand':
        """Set timeout in seconds.
        
        Args:
            timeout: Timeout w sekundach
            
        Returns:
            PingCommand: Instancja bieżącego obiektu dla chain-callingu
        """
        self.timeout = timeout
        return self

    def with_interval(self, interval: float) -> 'PingCommand':
        """Set interval between packets in seconds.
        
        Args:
            interval: Interwał między pakietami w sekundach
            
        Returns:
            PingCommand: Instancja bieżącego obiektu dla chain-callingu
        """
        self.interval = interval
        return self

    def with_packet_size(self, size: int) -> 'PingCommand':
        """Set packet size in bytes.
        
        Args:
            size: Rozmiar pakietu w bajtach
            
        Returns:
            PingCommand: Instancja bieżącego obiektu dla chain-callingu
        """
        self.size = size
        return self

    def with_ttl(self, ttl: int) -> 'PingCommand':
        """Set Time To Live.
        
        Args:
            ttl: Wartość TTL (Time To Live)
            
        Returns:
            PingCommand: Instancja bieżącego obiektu dla chain-callingu
        """
        self.ttl = ttl
        return self

    def from_interface(self, interface: str) -> 'PingCommand':
        """Set source interface.
        
        Args:
            interface: Interfejs źródłowy
            
        Returns:
            PingCommand: Instancja bieżącego obiektu dla chain-callingu
        """
        self.interface = interface
        return self

    def use_ipv6(self, enabled: bool = True) -> 'PingCommand':
        """Use IPv6 instead of IPv4.
        
        Args:
            enabled: Czy używać IPv6 zamiast IPv4
            
        Returns:
            PingCommand: Instancja bieżącego obiektu dla chain-callingu
        """
        self.ipv6 = enabled
        return self

    def build_command(self) -> List[str]:
        """Build ping command.
        
        Returns:
            List[str]: Lista argumentów komendy ping
        """
        # Sprawdzamy system operacyjny
        system = platform.system().lower()
        
        # Wybieramy komendę ping dla IPv4 lub IPv6
        if self.ipv6:
            cmd = ["ping6"] if system == "linux" else ["ping", "-6"]
        else:
            cmd = ["ping"]
        
        # Dodajemy opcje specyficzne dla systemu
        if system == "linux":
            # Linux
            if self.count is not None:
                cmd.extend(["-c", str(self.count)])
            if self.timeout is not None:
                cmd.extend(["-W", str(self.timeout)])
            if self.interval is not None:
                cmd.extend(["-i", str(self.interval)])
            if self.size is not None:
                cmd.extend(["-s", str(self.size)])
            if self.ttl is not None:
                cmd.extend(["-t", str(self.ttl)])
            if self.interface is not None:
                cmd.extend(["-I", self.interface])
        elif system == "windows":
            # Windows
            if self.count is not None:
                cmd.extend(["-n", str(self.count)])
            if self.timeout is not None:
                cmd.extend(["-w", str(self.timeout * 1000)])  # Windows używa milisekund
            if self.size is not None:
                cmd.extend(["-l", str(self.size)])
            if self.ttl is not None:
                cmd.extend(["-i", str(self.ttl)])
            # Windows nie obsługuje interwału i interfejsu w standardowy sposób
        elif system == "darwin":
            # macOS
            if self.count is not None:
                cmd.extend(["-c", str(self.count)])
            if self.timeout is not None:
                cmd.extend(["-t", str(self.timeout)])
            if self.interval is not None:
                cmd.extend(["-i", str(self.interval)])
            if self.size is not None:
                cmd.extend(["-s", str(self.size)])
            if self.ttl is not None:
                cmd.extend(["-m", str(self.ttl)])
            if self.interface is not None:
                cmd.extend(["-I", self.interface])
        
        # Dodajemy hosta
        cmd.append(self.host or "localhost")
        
        return cmd

    def validate(self) -> Dict[str, str]:
        """Validate ping command.
        
        Returns:
            Dict[str, str]: Słownik błędów walidacji (pusty jeśli wszystko OK)
        """
        errors = {}

        if not self.host:
            errors["host"] = "Host jest wymagany"
        
        if self.count is not None and self.count <= 0:
            errors["count"] = "Liczba pakietów musi być większa od zera"
        
        if self.timeout is not None and self.timeout <= 0:
            errors["timeout"] = "Timeout musi być większy od zera"
        
        if self.interval is not None and self.interval < 0:
            errors["interval"] = "Interwał nie może być ujemny"
        
        if self.size is not None and (self.size < 0 or self.size > 65507):
            errors["size"] = "Rozmiar pakietu musi być między 0 a 65507"
        
        if self.ttl is not None and (self.ttl < 1 or self.ttl > 255):
            errors["ttl"] = "TTL musi być między 1 a 255"

        return errors

    def _execute(self) -> Any:
        """Execute ping command.
        
        Returns:
            Any: Wynik wykonania komendy ping
            
        Raises:
            subprocess.CalledProcessError: Gdy komenda ping zwróci niezerowy kod wyjścia
        """
        cmd = self.build_command()
        
        try:
            # Uruchamiamy proces ping
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            stdout_data = []
            stderr_data = []
            
            # Odczytujemy dane z stdout w czasie rzeczywistym
            while process.poll() is None:
                if process.stdout and process.stdout.readable():
                    line = process.stdout.readline()
                    if line:
                        stdout_data.append(line)
                        print(line, end="")
                
                if process.stderr and process.stderr.readable():
                    line = process.stderr.readline()
                    if line:
                        stderr_data.append(line)
                        print(line, end="", file=sys.stderr)
            
            # Pobieramy pozostałe dane
            if process.stdout:
                for line in process.stdout:
                    stdout_data.append(line)
                    print(line, end="")
            
            if process.stderr:
                for line in process.stderr:
                    stderr_data.append(line)
                    print(line, end="", file=sys.stderr)
            
            # Tworzymy obiekt wyniku
            result = type('CompletedProcess', (), {
                'returncode': process.returncode,
                'stdout': ''.join(stdout_data),
                'stderr': ''.join(stderr_data),
                'args': cmd
            })
            
            # Sprawdzamy kod wyjścia
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, cmd, output=result.stdout, stderr=result.stderr
                )
            
            return result
            
        except Exception as e:
            print(f"Błąd podczas wykonywania komendy ping: {e}", file=sys.stderr)
            raise 