"""
Moduł shell do wykonywania komend powłoki.

Ten moduł dostarcza interfejs do wykonywania komend powłoki w sposób obiektowy.
"""

from mancer.shell.terminal import Terminal
from mancer.shell.bash_commands import (
    BASH_COMMANDS, get_command_info, get_all_commands, get_commands_by_category
)

__all__ = [
    'Terminal',
    'BASH_COMMANDS', 'get_command_info', 'get_all_commands', 'get_commands_by_category'
]
