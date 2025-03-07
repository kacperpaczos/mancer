"""Terminal operations command implementation."""
import os
import subprocess
from typing import Dict, List, Optional, Any

from mancer.core.interfaces.command import CommandBuilder


class TerminalCommand(CommandBuilder['TerminalCommand']):
    """Terminal operations command builder."""

    def __init__(self) -> None:
        """Initialize terminal command."""
        self.command: Optional[str] = None
        self.working_dir: Optional[str] = None
        self.environment: Dict[str, str] = {}
        self.shell: bool = False

    def execute(self, command: str) -> 'TerminalCommand':
        """Set command to execute.
        
        Args:
            command: Command to execute
            
        Returns:
            TerminalCommand: Current instance for chain calling
        """
        self.command = command
        return self

    def in_directory(self, path: str) -> 'TerminalCommand':
        """Set working directory.
        
        Args:
            path: Working directory path
            
        Returns:
            TerminalCommand: Current instance for chain calling
        """
        self.working_dir = path
        return self

    def with_env(self, key: str, value: str) -> 'TerminalCommand':
        """Set environment variable.
        
        Args:
            key: Environment variable name
            value: Environment variable value
            
        Returns:
            TerminalCommand: Current instance for chain calling
        """
        self.environment[key] = value
        return self

    def use_shell(self) -> 'TerminalCommand':
        """Use shell for command execution.
        
        Returns:
            TerminalCommand: Current instance for chain calling
        """
        self.shell = True
        return self

    def build_command(self) -> List[str]:
        """Build terminal command.
        
        Returns:
            List[str]: List of command arguments
        """
        if self.shell:
            return [self.command]
        return self.command.split() if self.command else []

    def validate(self) -> Dict[str, str]:
        """Validate terminal command.
        
        Returns:
            Dict[str, str]: Dictionary of validation errors (empty if all OK)
        """
        errors = {}
        
        if not self.command:
            errors["command"] = "Komenda jest wymagana"
            
        if self.working_dir and not os.path.isdir(self.working_dir):
            errors["working_dir"] = f"Katalog '{self.working_dir}' nie istnieje"
            
        return errors

    def _execute(self) -> Any:
        """Execute terminal command.
        
        Returns:
            Any: Command execution result
            
        Raises:
            subprocess.CalledProcessError: When command returns non-zero exit code
        """
        cmd = self.build_command()
        
        env = os.environ.copy()
        env.update(self.environment)
        
        return subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
            cwd=self.working_dir,
            shell=self.shell,
            env=env
        ) 