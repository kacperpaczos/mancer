from .core import Command, CommandResult
import os
from typing import Optional, List, NamedTuple
from datetime import datetime

class FileInfo(NamedTuple):
    name: str
    size: int
    permissions: str
    modified_time: datetime
    is_directory: bool
    owner: str
    group: str

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
    def ls(path: Optional[str] = None, options: str = "", parse_output: bool = False) -> Command:
        cmd = ["ls"]
        if options:
            cmd.extend(options.split())
        if path:
            cmd.append(path)
            
        command = Command(cmd)
        
        if parse_output:
            return LsCommand(command)
        return command

class LsCommand(Command):
    def __init__(self, command: Command):
        super().__init__(command.cmd)
        
    def run(self) -> CommandResult:
        result = super().run()
        if result.return_code != 0:
            return result
            
        return self._parse_ls_output(result)
    
    def _parse_ls_output(self, result: CommandResult) -> CommandResult:
        files: List[FileInfo] = []
        
        # Dodajemy -l do opcji, jeśli nie ma, żeby uzyskać szczegółowe informacje
        if "-l" not in " ".join(self.cmd):
            self.cmd.insert(1, "-l")
            result = super().run()
            
        for line in result.stdout.splitlines():
            if line.startswith('total') or not line.strip():
                continue
                
            parts = line.split()
            if len(parts) < 8:
                continue
                
            permissions = parts[0]
            owner = parts[2]
            group = parts[3]
            size = int(parts[4])
            date_str = " ".join(parts[5:8])
            name = " ".join(parts[8:])
            
            try:
                modified_time = datetime.strptime(date_str, "%b %d %H:%M")
                modified_time = modified_time.replace(year=datetime.now().year)
            except ValueError:
                try:
                    modified_time = datetime.strptime(date_str, "%b %d %Y")
                except ValueError:
                    modified_time = datetime.now()
            
            files.append(FileInfo(
                name=name,
                size=size,
                permissions=permissions,
                modified_time=modified_time,
                is_directory=permissions.startswith('d'),
                owner=owner,
                group=group
            ))
            
        result.parsed_files = files
        return result

# Utworzenie globalnej instancji
shell = Shell() 