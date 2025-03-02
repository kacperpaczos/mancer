# shell/factory.py
from .commands import SSHCommand, SCPCommand, CopyCommand, MoveCommand, SystemctlCommand

class CommandFactory:
    """Factory for creating command instances."""
    
    @staticmethod
    def ssh() -> SSHCommand:
        """Create SSH command."""
        return SSHCommand()
    
    @staticmethod
    def scp() -> SCPCommand:
        """Create SCP command."""
        return SCPCommand()
    
    @staticmethod
    def copy() -> CopyCommand:
        """Create copy command."""
        return CopyCommand()
    
    @staticmethod
    def move() -> MoveCommand:
        """Create move command."""
        return MoveCommand()
    
    @staticmethod
    def systemctl() -> SystemctlCommand:
        """Create systemctl command."""
        return SystemctlCommand()