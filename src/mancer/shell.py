from .core import Command, CommandResult
import os
from typing import Optional

class Shell:
    @staticmethod
    def cd(path: str) -> CommandResult:
        try:
            os.chdir(path)
            return CommandResult(
                stdout=f"Changed directory to {os.getcwd()}",
                stderr="",
                return_code=0
            )
        except Exception as e:
            return CommandResult("", str(e), 1)
    
    @staticmethod
    def ls(path: Optional[str] = None, options: str = "") -> Command:
        cmd = ["ls"]
        if options:
            cmd.extend(options.split())
        if path:
            cmd.append(path)
        return Command(cmd)

# Utworzenie globalnej instancji
shell = Shell() 