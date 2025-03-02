# shell/commands/network/scp.py
from mancer.core.base.command import BaseCommand
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

class SCPCommand(BaseCommand):
    """SCP command implementation."""
    
    def __init__(self, executor=None):
        super().__init__(executor)
        self.source = None
        self.destination = None
        self.port = 22
        self.username = None
        self.password = None
        self.key_file = None
        self.recursive = False
        self.preserve = False
        self.quiet = False
        self.options = {}
    
    def set_source(self, source: Union[str, Path]) -> 'SCPCommand':
        """Set source path."""
        self.source = str(source)
        return self
    
    def set_destination(self, destination: Union[str, Path]) -> 'SCPCommand':
        """Set destination path."""
        self.destination = str(destination)
        return self
    
    def set_port(self, port: int) -> 'SCPCommand':
        """Set SSH port."""
        self.port = port
        return self
    
    def set_username(self, username: str) -> 'SCPCommand':
        """Set username for connection."""
        self.username = username
        return self
    
    def set_key_file(self, key_file: str) -> 'SCPCommand':
        """Set identity file for connection."""
        self.key_file = key_file
        return self
    
    def set_recursive(self, recursive: bool = True) -> 'SCPCommand':
        """Set recursive copy mode."""
        self.recursive = recursive
        return self
    
    def set_preserve(self, preserve: bool = True) -> 'SCPCommand':
        """Preserve modification times, access times, and modes."""
        self.preserve = preserve
        return self
    
    def set_quiet(self, quiet: bool = True) -> 'SCPCommand':
        """Quiet mode (don't show progress)."""
        self.quiet = quiet
        return self
    
    def set_option(self, key: str, value: Any) -> 'SCPCommand':
        """Set additional SCP option."""
        self.options[key] = value
        return self
    
    def validate(self) -> Dict[str, str]:
        """Validate command parameters."""
        errors = {}
        
        if not self.source:
            errors["source"] = "Source path must be specified"
        
        if not self.destination:
            errors["destination"] = "Destination path must be specified"
        
        if self.port is not None:
            if not isinstance(self.port, int):
                errors["port"] = "Port must be an integer"
            elif self.port < 1 or self.port > 65535:
                errors["port"] = "Port must be between 1 and 65535"
        
        return errors
    
    def build_command(self) -> List[str]:
        """Build SCP command as list of arguments."""
        cmd = ["scp"]
        
        # Add options
        if self.recursive:
            cmd.append("-r")
        
        if self.preserve:
            cmd.append("-p")
        
        if self.quiet:
            cmd.append("-q")
        
        # Add port option
        if self.port != 22:
            cmd.extend(["-P", str(self.port)])
        
        # Add identity file if specified
        if self.key_file:
            cmd.extend(["-i", self.key_file])
        
        # Add other options
        for key, value in self.options.items():
            if value is True:
                cmd.append(f"-{key}")
            elif value is not None:
                cmd.extend([f"-{key}", str(value)])
        
        # Format source with username if needed
        source = self.source
        if ":" in source and "@" not in source and self.username:
            host, path = source.split(":", 1)
            source = f"{self.username}@{host}:{path}"
        
        # Format destination with username if needed
        destination = self.destination
        if ":" in destination and "@" not in destination and self.username:
            host, path = destination.split(":", 1)
            destination = f"{self.username}@{host}:{path}"
        
        # Add source and destination
        cmd.append(source)
        cmd.append(destination)
        
        return cmd