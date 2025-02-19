from typing import Optional
from ..base import ShellCommand
from .ping import create_ping_command
from .ip import create_ip_command
from ...core import Command, CommandResult
import os
from .ls import LsCommand
from .cd import CdCommand
from .mkdir import MkdirCommand

class Shell:
    @staticmethod
    def ls(path: Optional[str] = None, options: str = "", parse_output: bool = False) -> LsCommand:
        return LsCommand(path, options, parse_output)

    @staticmethod
    def cd(path: str) -> CdCommand:
        return CdCommand(path)

    @staticmethod
    def mkdir(path: str, parents: bool = False) -> MkdirCommand:
        return MkdirCommand(path, parents)

    @staticmethod
    def ping(host: str, count: Optional[int] = None) -> Command:
        cmd = create_ping_command(host, count).get_command()
        return Command(cmd)

    @staticmethod
    def ip(action: str, target: Optional[str] = None) -> Command:
        cmd = create_ip_command(action, target).get_command()
        return Command(cmd)

__all__ = ['Shell'] 