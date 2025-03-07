"""File operations command implementation."""
import os
import subprocess
from typing import Dict, List, Optional, Any

from mancer.core.interfaces.command import CommandBuilder


class FileCommand(CommandBuilder['FileCommand']):
    """File operations command builder."""

    def __init__(self) -> None:
        """Initialize file command."""
        self.source: Optional[str] = None
        self.destination: Optional[str] = None
        self.operation: Optional[str] = None
        self.recursive: bool = False
        self.force: bool = False

    def copy(self, source: str, destination: str) -> 'FileCommand':
        """Copy file or directory.
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            FileCommand: Current instance for chain calling
        """
        self.source = source
        self.destination = destination
        self.operation = "cp"
        return self

    def move(self, source: str, destination: str) -> 'FileCommand':
        """Move file or directory.
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            FileCommand: Current instance for chain calling
        """
        self.source = source
        self.destination = destination
        self.operation = "mv"
        return self

    def remove(self, path: str) -> 'FileCommand':
        """Remove file or directory.
        
        Args:
            path: Path to remove
            
        Returns:
            FileCommand: Current instance for chain calling
        """
        self.source = path
        self.operation = "rm"
        return self

    def recursively(self) -> 'FileCommand':
        """Enable recursive operation.
        
        Returns:
            FileCommand: Current instance for chain calling
        """
        self.recursive = True
        return self

    def force(self) -> 'FileCommand':
        """Force operation without confirmation.
        
        Returns:
            FileCommand: Current instance for chain calling
        """
        self.force = True
        return self

    def build_command(self) -> List[str]:
        """Build file operation command.
        
        Returns:
            List[str]: List of command arguments
        """
        cmd = [self.operation]
        
        if self.recursive:
            cmd.append("-r")
            
        if self.force:
            cmd.append("-f")
            
        cmd.append(self.source)
        
        if self.destination:
            cmd.append(self.destination)
            
        return cmd

    def validate(self) -> Dict[str, str]:
        """Validate file operation command.
        
        Returns:
            Dict[str, str]: Dictionary of validation errors (empty if all OK)
        """
        errors = {}
        
        if not self.operation:
            errors["operation"] = "Operacja jest wymagana"
            
        if not self.source:
            errors["source"] = "Ścieżka źródłowa jest wymagana"
            
        if self.operation in ["cp", "mv"] and not self.destination:
            errors["destination"] = "Ścieżka docelowa jest wymagana"
            
        if self.source and not os.path.exists(self.source):
            errors["source"] = f"Ścieżka '{self.source}' nie istnieje"
            
        return errors

    def _execute(self) -> Any:
        """Execute file operation command.
        
        Returns:
            Any: Command execution result
            
        Raises:
            subprocess.CalledProcessError: When command returns non-zero exit code
        """
        cmd = self.build_command()
        return subprocess.run(cmd, check=True, text=True, capture_output=True) 