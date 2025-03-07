from ....core import Command
from typing import List

class SystemdManager:
    def __init__(self):
        self._systemctl = "systemctl"
    
    def list_units(self) -> Command:
        return Command([self._systemctl, "list-units"])
    
    def status(self, unit_name: str) -> Command:
        return Command([self._systemctl, "status", unit_name])
    
    def restart(self, unit_name: str) -> Command:
        return Command([self._systemctl, "restart", unit_name])
    
    def start(self, unit_name: str) -> Command:
        return Command([self._systemctl, "start", unit_name])
    
    def stop(self, unit_name: str) -> Command:
        return Command([self._systemctl, "stop", unit_name])

# Utworzenie globalnej instancji
systemd = SystemdManager() 