"""
Narzędzia pomocnicze dla Mancer Terminal
"""

__version__ = "1.0.0"
__description__ = "Narzędzia pomocnicze i parsery"

from .ssh_command_parser import SSHCommandParser, SSHConnectionParams

__all__ = ["SSHCommandParser", "SSHConnectionParams"]
