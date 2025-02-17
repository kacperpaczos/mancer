import subprocess
import os
from typing import Optional, List, Union

class CommandResult:
    def __init__(self, stdout: str, stderr: str, return_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code

class Command:
    def __init__(self, cmd: Union[str, List[str]]):
        self.cmd = cmd if isinstance(cmd, list) else cmd.split()
    
    def run(self) -> CommandResult:
        try:
            process = subprocess.run(
                self.cmd,
                capture_output=True,
                text=True
            )
            return CommandResult(
                process.stdout,
                process.stderr,
                process.returncode
            )
        except Exception as e:
            return CommandResult("", str(e), 1) 