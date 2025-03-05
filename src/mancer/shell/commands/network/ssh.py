"""SSH command implementation."""
import os
import subprocess
import sys
from typing import Dict, List, Optional, Union, Any
import re

from mancer.core.interfaces.command import CommandBuilder


class SSHCommand(CommandBuilder['SSHCommand']):
    """SSH command builder."""

    def __init__(self) -> None:
        """Initialize SSH command."""
        self.host: Optional[str] = None
        self.port: int = 22
        self.username: Optional[str] = None
        self.identity_file: Optional[str] = None
        self.command: Optional[str] = None
        self.options: Dict[str, str] = {}
        # Domyślnie wyłączamy StrictHostKeyChecking, aby obsłużyć fingerprint
        self.options["StrictHostKeyChecking"] = "no"
        # Dodajemy opcję do obsługi pytania o fingerprint
        self.options["BatchMode"] = "no"

    def to(self, host: str) -> 'SSHCommand':
        """Set target host."""
        self.host = host
        return self

    def as_user(self, username: str) -> 'SSHCommand':
        """Set username."""
        self.username = username
        return self

    def on_port(self, port: int) -> 'SSHCommand':
        """Set SSH port."""
        self.port = port
        return self

    def with_key(self, identity_file: str) -> 'SSHCommand':
        """Set identity file."""
        self.identity_file = identity_file
        return self

    def run_command(self, command: str) -> 'SSHCommand':
        """Set command to run."""
        self.command = command
        return self

    def with_option(self, option: str, value: str) -> 'SSHCommand':
        """Set SSH option."""
        self.options[option] = value
        return self

    def with_strict_host_checking(self, enabled: bool = True) -> 'SSHCommand':
        """Enable or disable strict host key checking."""
        self.options["StrictHostKeyChecking"] = "yes" if enabled else "no"
        return self

    def build_command(self) -> List[str]:
        """Build SSH command."""
        cmd = ["ssh"]

        # Dodaj opcje
        for key, value in self.options.items():
            cmd.extend(["-o", f"{key}={value}"])

        # Dodaj port
        if self.port != 22:
            cmd.extend(["-p", str(self.port)])

        # Dodaj klucz
        if self.identity_file:
            cmd.extend(["-i", self.identity_file])

        # Dodaj użytkownika i hosta
        target = ""
        if self.username:
            target = f"{self.username}@"
        target += self.host or ""
        cmd.append(target)

        # Dodaj komendę
        if self.command:
            cmd.append(self.command)

        return cmd

    def validate(self) -> Dict[str, str]:
        """Validate SSH command."""
        errors = {}

        if not self.host:
            errors["host"] = "Host is required"

        return errors

    def _execute(self) -> Any:
        """Execute SSH command with fingerprint handling."""
        cmd = self.build_command()
        
        # Uruchamiamy proces SSH z obsługą interaktywną
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Monitorujemy wyjście stderr, aby wykryć pytanie o fingerprint
        while process.poll() is None:
            # Sprawdzamy, czy jest coś na stderr
            if process.stderr and process.stderr.readable():
                line = process.stderr.readline()
                if not line:
                    continue
                
                # Sprawdzamy, czy to pytanie o fingerprint
                if "fingerprint" in line and "Are you sure you want to continue connecting" in line:
                    print(line, end="", file=sys.stderr)
                    
                    # Pytamy użytkownika o potwierdzenie
                    response = input("Czy chcesz kontynuować połączenie? (yes/no): ")
                    
                    # Przekazujemy odpowiedź do procesu SSH
                    if process.stdin and process.stdin.writable():
                        process.stdin.write(response + "\n")
                        process.stdin.flush()
                else:
                    # Wyświetlamy inne komunikaty
                    print(line, end="", file=sys.stderr)
        
        # Pobieramy wynik procesu
        stdout, stderr = process.communicate()
        
        # Tworzymy obiekt podobny do CompletedProcess
        result = type('CompletedProcess', (), {
            'returncode': process.returncode,
            'stdout': stdout,
            'stderr': stderr
        })
        
        # Sprawdzamy kod wyjścia
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, cmd, output=stdout, stderr=stderr
            )
        
        return result 