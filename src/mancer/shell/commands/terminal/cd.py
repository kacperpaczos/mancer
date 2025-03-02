from ...base import ShellCommand
from ....core import CommandResult
import os

class CdCommand(ShellCommand):
    def __init__(self, path: str):
        self.path = path
        super().__init__(["cd", path])

    def execute(self) -> CommandResult:
        try:
            os.chdir(self.path)
            return CommandResult(
                stdout=f"Changed directory to {os.getcwd()}",
                stderr="",
                return_code=0
            )
        except Exception as e:
            return CommandResult("", str(e), 1) 