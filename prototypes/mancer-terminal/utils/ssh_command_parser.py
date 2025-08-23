"""
Parser komend SSH - wyciąga parametry połączenia z tradycyjnej komendy SSH
"""

import os
import re
import shlex
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class SSHConnectionParams:
    """Parametry połączenia SSH wyciągnięte z komendy"""

    hostname: str
    username: Optional[str] = None
    port: int = 22
    key_filename: Optional[str] = None
    proxy_command: Optional[str] = None
    additional_options: Dict[str, str] = None

    def __post_init__(self):
        if self.additional_options is None:
            self.additional_options = {}


class SSHCommandParser:
    """Parser komend SSH"""

    def __init__(self):
        # Wzorce dla różnych opcji SSH
        self.patterns = {
            "port": r"-p\s+(\d+)",
            "key": r"-i\s+([^\s]+)",
            "username": r"([a-zA-Z0-9_.-]+)@([a-zA-Z0-9_.-]+)",
            "proxy": r"-o\s+ProxyCommand=([^\s]+)",
            "hostname": r"(?:ssh\s+)?(?:[a-zA-Z0-9_.-]+@)?([a-zA-Z0-9_.-]+(?:\.[a-zA-Z0-9_.-]+)*)",
        }

    def parse_ssh_command(self, command: str) -> SSHConnectionParams:
        """
        Parsuje komendę SSH i wyciąga parametry połączenia

        Args:
            command: Komenda SSH (np. "ssh -p 2222 user@host")

        Returns:
            SSHConnectionParams z wyciągniętymi parametrami
        """
        # Usuń 'ssh' z początku jeśli istnieje
        command = command.strip()
        if command.startswith("ssh "):
            command = command[4:].strip()

        # Wyciągnij parametry
        params = SSHConnectionParams(hostname="")

        # Port
        port_match = re.search(self.patterns["port"], command)
        if port_match:
            params.port = int(port_match.group(1))

        # Klucz prywatny
        key_match = re.search(self.patterns["key"], command)
        if key_match:
            params.key_filename = key_match.group(1)

        # Proxy command
        proxy_match = re.search(self.patterns["proxy"], command)
        if proxy_match:
            params.proxy_command = proxy_match.group(1)

        # Username i hostname
        user_host_match = re.search(self.patterns["username"], command)
        if user_host_match:
            params.username = user_host_match.group(1)
            params.hostname = user_host_match.group(2)
        else:
            # Tylko hostname
            hostname_match = re.search(self.patterns["hostname"], command)
            if hostname_match:
                params.hostname = hostname_match.group(1)

        # Dodatkowe opcje -o
        self._parse_additional_options(command, params)

        return params

    def _parse_additional_options(self, command: str, params: SSHConnectionParams):
        """Parsuje dodatkowe opcje SSH (-o)"""
        # Znajdź wszystkie opcje -o
        options = re.findall(r"-o\s+([^-\s]+)=([^\s]+)", command)
        for key, value in options:
            if key not in ["ProxyCommand"]:  # ProxyCommand już obsłużone
                params.additional_options[key] = value

    def build_ssh_command(self, params: SSHConnectionParams) -> str:
        """
        Buduje komendę SSH z parametrów

        Args:
            params: Parametry połączenia

        Returns:
            Komenda SSH jako string
        """
        parts = ["ssh"]

        # Port
        if params.port != 22:
            parts.extend(["-p", str(params.port)])

        # Klucz prywatny
        if params.key_filename:
            parts.extend(["-i", params.key_filename])

        # Proxy command
        if params.proxy_command:
            parts.extend(["-o", f"ProxyCommand={params.proxy_command}"])

        # Dodatkowe opcje
        for key, value in params.additional_options.items():
            parts.extend(["-o", f"{key}={value}"])

        # Username@hostname
        if params.username:
            parts.append(f"{params.username}@{params.hostname}")
        else:
            parts.append(params.hostname)

        return " ".join(parts)

    def validate_connection_params(self, params: SSHConnectionParams) -> Tuple[bool, str]:
        """
        Waliduje parametry połączenia

        Returns:
            Tuple (is_valid, error_message)
        """
        if not params.hostname:
            return False, "Hostname jest wymagany"

        if params.port < 1 or params.port > 65535:
            return False, "Port musi być w zakresie 1-65535"

        return True, ""

    def extract_from_ssh_config(self, hostname: str) -> Optional[SSHConnectionParams]:
        """
        Próbuje wyciągnąć parametry z ~/.ssh/config

        Args:
            hostname: Nazwa hosta

        Returns:
            SSHConnectionParams lub None jeśli nie znaleziono
        """
        try:
            config_path = os.path.expanduser("~/.ssh/config")
            if not os.path.exists(config_path):
                return None

            with open(config_path, "r") as f:
                content = f.read()

            # Znajdź sekcję dla danego hosta
            host_pattern = rf"Host\s+{re.escape(hostname)}\s*\n(.*?)(?=\nHost|\Z)"
            match = re.search(host_pattern, content, re.DOTALL)

            if not match:
                return None

            host_config = match.group(1)
            params = SSHConnectionParams(hostname=hostname)

            # Parsuj opcje
            for line in host_config.split("\n"):
                line = line.strip()
                if line.startswith("HostName"):
                    params.hostname = line.split()[1]
                elif line.startswith("User"):
                    params.username = line.split()[1]
                elif line.startswith("Port"):
                    params.port = int(line.split()[1])
                elif line.startswith("IdentityFile"):
                    params.key_filename = line.split()[1]
                elif line.startswith("ProxyCommand"):
                    params.proxy_command = line.split(" ", 1)[1]

            return params

        except Exception:
            return None


# Przykład użycia
if __name__ == "__main__":
    parser = SSHCommandParser()

    # Test parsowania
    test_commands = [
        "ssh -p 2222 user@192.168.1.100",
        "ssh -i ~/.ssh/id_rsa admin@server.example.com",
        "ssh -o ProxyCommand='nc -X connect -x proxy:8080 %h %p' user@host",
        "192.168.1.100",
        "user@hostname",
    ]

    for cmd in test_commands:
        print(f"Komenda: {cmd}")
        params = parser.parse_ssh_command(cmd)
        print(f"  Hostname: {params.hostname}")
        print(f"  Username: {params.username}")
        print(f"  Port: {params.port}")
        print(f"  Key: {params.key_filename}")
        print(f"  Proxy: {params.proxy_command}")
        print()
