from typing import List, Optional

from .base import ShellCommand, Tool


class NetworkScanner(Tool):
    def __init__(self, network: str):
        super().__init__("network_scanner")
        self.network = network

    def setup(self) -> None:
        # Dodaj kroki skanowania
        self.add_step(ShellCommand(["nmap", "-sn", self.network]))
        self.add_step(ShellCommand(["arp", "-a"]))


class Ping(ShellCommand):
    def __init__(self, host: str, count: Optional[int] = None):
        cmd = ["ping"]
        if count:
            cmd.extend(["-c", str(count)])
        cmd.append(host)
        super().__init__(cmd)
