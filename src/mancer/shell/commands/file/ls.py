from ...base import PlatformCommand, ShellCommand
from typing import Optional, List
from datetime import datetime
from ....core import Command, CommandResult

class LsCommand(ShellCommand):
    def __init__(self, path: Optional[str] = None, options: str = "", parse_output: bool = False):
        cmd = ["ls"]
        if options:
            cmd.extend(options.split())
        if path:
            cmd.append(path)
        super().__init__(cmd)
        self.parse_output = parse_output

    def execute(self) -> CommandResult:
        result = super().execute()
        if self.parse_output:
            return self._parse_output(result)
        return result

    def _parse_output(self, result: CommandResult) -> CommandResult:
        # Implementacja parsowania wyjścia ls
        # Możemy przenieść istniejącą logikę z poprzedniej implementacji
        return result 