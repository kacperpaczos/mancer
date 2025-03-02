# shell/commands/file/mv.py
from mancer.core.base.command import BaseCommand
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

class MoveCommand(BaseCommand):
    """Move command implementation."""
    
    def __init__(self, executor=None):
        super().__init__(executor)
        self.source = None
        self.destination = None
        self.force = False
        self.verbose = False
        self.options = {}
    
    def set_source(self, source: Union[str, Path]) -> 'MoveCommand':
        """Set source path."""
        self.source = str(source)
        return self
    
    def set_destination(self, destination: Union[str, Path]) -> 'MoveCommand':
        """Set destination path."""
        self.destination = str(destination)
        return self
    
    def set_force(self, force: bool = True) -> 'MoveCommand':
        """Force move by removing destination file if needed."""
        self.force = force
        return self
    
    def set_verbose(self, verbose: bool = True) -> 'MoveCommand':
        """Enable verbose output."""
        self.verbose = verbose
        return self
    
    def set_option(self, key: str, value: Any) -> 'MoveCommand':
        """Set additional mv option."""
        self.options[key] = value
        return self
    
    def validate(self) -> Dict[str, str]:
        """Validate command parameters."""
        errors = {}
        
        if not self.source:
            errors["source"] = "Source path must be specified"
        
        if not self.destination:
            errors["destination"] = "Destination path must be specified"
        
        return errors
    
    def build_command(self) -> List[str]:
        """Build mv command as list of arguments."""
        cmd = ["mv"]
        
        # Add options
        if self.force:
            cmd.append("-f")
        
        if self.verbose:
            cmd.append("-v")
        
        # Add other options
        for key, value in self.options.items():
            if value is True:
                cmd.append(f"-{key}")
            elif value is not None:
                cmd.extend([f"-{key}", str(value)])
        
        # Add source and destination
        cmd.append(self.source)
        cmd.append(self.destination)
        
        return cmd