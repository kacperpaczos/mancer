import platform
from abc import ABC, abstractmethod
from ..core import Command, CommandResult

class PlatformCommand(ABC):
    """Bazowa klasa dla poleceń specyficznych dla platformy"""
    @abstractmethod
    def get_command(self) -> list[str]:
        pass

class ShellCommand:
    """Podstawowa klasa dla poleceń powłoki"""
    def __init__(self, cmd: list[str]):
        self.cmd = cmd
    
    def execute(self) -> CommandResult:
        return Command(self.cmd).run()

def get_platform() -> str:
    system = platform.system().lower()
    if system == 'linux':
        return 'linux'
    elif system == 'windows':
        return 'windows'
    else:
        raise NotImplementedError(f"Platform {system} is not supported") 