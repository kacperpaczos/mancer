from ..base import PlatformCommand, get_platform
from typing import Optional

class LinuxIP(PlatformCommand):
    def __init__(self, action: str, target: Optional[str] = None):
        self.action = action
        self.target = target

    def get_command(self) -> list[str]:
        cmd = ["ip"]
        if self.action == "show":
            cmd.append("addr")
        elif self.action == "route":
            cmd.append("route")
        if self.target:
            cmd.append(self.target)
        return cmd

class WindowsIP(PlatformCommand):
    def __init__(self, action: str, target: Optional[str] = None):
        self.action = action
        self.target = target

    def get_command(self) -> list[str]:
        if self.action == "show":
            return ["ipconfig", "/all"]
        elif self.action == "route":
            return ["route", "print"]
        raise ValueError(f"Unsupported action: {self.action}")

def create_ip_command(action: str, target: Optional[str] = None) -> PlatformCommand:
    platform = get_platform()
    if platform == 'linux':
        return LinuxIP(action, target)
    elif platform == 'windows':
        return WindowsIP(action, target)
    raise NotImplementedError(f"IP command not implemented for platform {platform}") 