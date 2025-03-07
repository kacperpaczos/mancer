"""Process management command implementation."""
import subprocess
from typing import Dict, List, Optional, Any

from mancer.core.interfaces.command import CommandBuilder


class ProcessCommand(CommandBuilder['ProcessCommand']):
    """Process management command builder."""

    def __init__(self) -> None:
        """Initialize process command."""
        self.pid: Optional[int] = None
        self.signal: Optional[int] = None
        self.command: Optional[str] = None
        self.background: bool = False

    def kill(self, pid: int) -> 'ProcessCommand':
        """Kill process with given PID.
        
        Args:
            pid: Process ID to kill
            
        Returns:
            ProcessCommand: Current instance for chain calling
        """
        self.pid = pid
        self.command = "kill"
        return self

    def ps(self) -> 'ProcessCommand':
        """List processes.
        
        Returns:
            ProcessCommand: Current instance for chain calling
        """
        self.command = "ps"
        return self

    def run_in_background(self) -> 'ProcessCommand':
        """Run command in background.
        
        Returns:
            ProcessCommand: Current instance for chain calling
        """
        self.background = True
        return self

    def build_command(self) -> List[str]:
        """Build process command.
        
        Returns:
            List[str]: List of command arguments
        """
        cmd: List[str] = []
        
        if self.command == "kill" and self.pid is not None:
            cmd = ["kill", str(self.pid)]
        elif self.command == "ps":
            cmd = ["ps", "aux"]
            
        if self.background:
            cmd.append("&")
            
        return cmd

    def validate(self) -> Dict[str, str]:
        """Validate process command.
        
        Returns:
            Dict[str, str]: Dictionary of validation errors (empty if all OK)
        """
        errors = {}
        
        if not self.command:
            errors["command"] = "Komenda jest wymagana"
            
        if self.command == "kill" and self.pid is None:
            errors["pid"] = "PID jest wymagany dla komendy kill"
            
        return errors

    def _execute(self) -> Any:
        """Execute process command.
        
        Returns:
            Any: Command execution result
            
        Raises:
            subprocess.CalledProcessError: When command returns non-zero exit code
        """
        cmd = self.build_command()
        return subprocess.run(cmd, check=True, text=True, capture_output=True) 