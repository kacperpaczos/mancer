from ...base import PlatformCommand, ShellCommand
from typing import Optional
import os

class MkdirCommand(ShellCommand):
    def __init__(self, path: str, parents: bool = False):
        cmd = ["mkdir"]
        if parents:
            cmd.append("-p")
        cmd.append(path)
        super().__init__(cmd) 