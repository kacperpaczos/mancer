from typing import Optional
from ..core import Command, CommandResult
from .base import ShellCommand
import os

class Shell:
    @staticmethod
    def ls(path: Optional[str] = None, options: str = "", parse_output: bool = False) -> Command:
        cmd = ["ls"]
        if options:
            cmd.extend(options.split())
        if path:
            cmd.append(path)
        return Command(cmd)

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