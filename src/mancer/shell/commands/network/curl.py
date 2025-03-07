"""Curl command implementation."""
import subprocess
from typing import Dict, List, Optional, Any

from mancer.core.interfaces.command import CommandBuilder


class CurlCommand(CommandBuilder['CurlCommand']):
    """Curl command builder."""

    def __init__(self) -> None:
        """Initialize curl command."""
        self.url: Optional[str] = None
        self.method: str = "GET"
        self.headers: Dict[str, str] = {}
        self.data: Optional[str] = None
        self.output_file: Optional[str] = None
        self.follow_redirects: bool = False
        self.insecure: bool = False

    def to(self, url: str) -> 'CurlCommand':
        """Set target URL.
        
        Args:
            url: Target URL
            
        Returns:
            CurlCommand: Current instance for chain calling
        """
        self.url = url
        return self

    def using_method(self, method: str) -> 'CurlCommand':
        """Set HTTP method.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            
        Returns:
            CurlCommand: Current instance for chain calling
        """
        self.method = method.upper()
        return self

    def with_header(self, name: str, value: str) -> 'CurlCommand':
        """Add HTTP header.
        
        Args:
            name: Header name
            value: Header value
            
        Returns:
            CurlCommand: Current instance for chain calling
        """
        self.headers[name] = value
        return self

    def with_data(self, data: str) -> 'CurlCommand':
        """Set request body data.
        
        Args:
            data: Request body data
            
        Returns:
            CurlCommand: Current instance for chain calling
        """
        self.data = data
        return self

    def save_to(self, file_path: str) -> 'CurlCommand':
        """Save response to file.
        
        Args:
            file_path: Output file path
            
        Returns:
            CurlCommand: Current instance for chain calling
        """
        self.output_file = file_path
        return self

    def follow_redirects(self) -> 'CurlCommand':
        """Enable following redirects.
        
        Returns:
            CurlCommand: Current instance for chain calling
        """
        self.follow_redirects = True
        return self

    def allow_insecure(self) -> 'CurlCommand':
        """Allow insecure SSL connections.
        
        Returns:
            CurlCommand: Current instance for chain calling
        """
        self.insecure = True
        return self

    def build_command(self) -> List[str]:
        """Build curl command.
        
        Returns:
            List[str]: List of command arguments
        """
        cmd = ["curl"]
        
        # Dodaj metodę HTTP
        if self.method != "GET":
            cmd.extend(["-X", self.method])
            
        # Dodaj nagłówki
        for name, value in self.headers.items():
            cmd.extend(["-H", f"{name}: {value}"])
            
        # Dodaj dane
        if self.data:
            cmd.extend(["-d", self.data])
            
        # Dodaj plik wyjściowy
        if self.output_file:
            cmd.extend(["-o", self.output_file])
            
        # Dodaj opcje
        if self.follow_redirects:
            cmd.append("-L")
            
        if self.insecure:
            cmd.append("-k")
            
        # Dodaj URL
        if self.url:
            cmd.append(self.url)
            
        return cmd

    def validate(self) -> Dict[str, str]:
        """Validate curl command.
        
        Returns:
            Dict[str, str]: Dictionary of validation errors (empty if all OK)
        """
        errors = {}
        
        if not self.url:
            errors["url"] = "URL jest wymagany"
            
        if self.method not in ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]:
            errors["method"] = f"Nieobsługiwana metoda HTTP: {self.method}"
            
        return errors

    def _execute(self) -> Any:
        """Execute curl command.
        
        Returns:
            Any: Command execution result
            
        Raises:
            subprocess.CalledProcessError: When command returns non-zero exit code
        """
        cmd = self.build_command()
        return subprocess.run(cmd, check=True, text=True, capture_output=True) 