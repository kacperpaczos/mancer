from ..base import PlatformCommand, get_platform
from typing import Optional

class LinuxPing(PlatformCommand):
    def __init__(self, host: str, count: Optional[int] = None):
        self.host = host
        self.count = count

    def get_command(self) -> list[str]:
        cmd = ["ping"]
        if self.count:
            cmd.extend(["-c", str(self.count)])
        cmd.append(self.host)
        return cmd

class WindowsPing(PlatformCommand):
    def __init__(self, host: str, count: Optional[int] = None):
        self.host = host
        self.count = count

    def get_command(self) -> list[str]:
        cmd = ["ping"]
        if self.count:
            cmd.extend(["-n", str(self.count)])
        cmd.append(self.host)
        return cmd

def create_ping_command(host: str, count: Optional[int] = None) -> PlatformCommand:
    platform = get_platform()
    if platform == 'linux':
        return LinuxPing(host, count)
    elif platform == 'windows':
        return WindowsPing(host, count)
    raise NotImplementedError(f"Ping not implemented for platform {platform}") 