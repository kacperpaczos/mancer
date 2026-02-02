from typing import Any, Dict, List, Optional, Type, cast

from ...domain.interface.command_interface import CommandInterface
from ..command.file.cat_command import CatCommand
from ..command.file.cd_command import CdCommand
from ..command.file.cp_command import CpCommand
from ..command.file.find_command import FindCommand
from ..command.file.grep_command import GrepCommand
from ..command.file.head_command import HeadCommand
from ..command.file.ls_command import LsCommand
from ..command.file.mkdir_command import MkdirCommand
from ..command.file.mv_command import MvCommand
from ..command.file.rm_command import RmCommand
from ..command.file.tail_command import TailCommand
from ..command.file.touch_command import TouchCommand
from ..command.network.curl_command import CurlCommand
from ..command.network.netstat_command import NetstatCommand
from ..command.network.ping_command import PingCommand
from ..command.network.ssh_command import SshCommand
from ..command.network.wget_command import WgetCommand
from ..command.system.cron_command import CronCommand
from ..command.system.df_command import DfCommand
from ..command.system.echo_command import EchoCommand
from ..command.system.hostname_command import HostnameCommand
from ..command.system.kill_command import KillCommand
from ..command.system.ps_command import PsCommand
from ..command.system.service_command import ServiceCommand
from ..command.system.systemctl_command import SystemctlCommand
from ..command.system.wc_command import WcCommand


class CommandFactory:
    """Fabryka komend – rejestr wszystkich komend z infrastructure.command (kanoniczny zestaw)."""

    def __init__(self, backend_type: str = "bash"):
        self.backend_type = backend_type
        self._command_types: Dict[str, Type[CommandInterface]] = {}
        self._configured_commands: Dict[str, CommandInterface] = {}
        self._initialize_commands()

    def _initialize_commands(self) -> None:
        """Rejestruje dostępne typy komend (file, system, network)."""
        # Komendy plikowe
        self._command_types["ls"] = LsCommand
        self._command_types["cp"] = CpCommand
        self._command_types["cd"] = CdCommand
        self._command_types["find"] = FindCommand
        self._command_types["grep"] = GrepCommand
        self._command_types["cat"] = CatCommand
        self._command_types["tail"] = TailCommand
        self._command_types["head"] = HeadCommand
        self._command_types["mkdir"] = MkdirCommand
        self._command_types["mv"] = MvCommand
        self._command_types["rm"] = RmCommand
        self._command_types["touch"] = TouchCommand

        # Komendy systemowe
        self._command_types["ps"] = PsCommand
        self._command_types["systemctl"] = SystemctlCommand
        self._command_types["hostname"] = HostnameCommand
        self._command_types["df"] = DfCommand
        self._command_types["echo"] = EchoCommand
        self._command_types["wc"] = WcCommand
        self._command_types["kill"] = KillCommand
        self._command_types["cron"] = CronCommand
        self._command_types["service"] = ServiceCommand

        # Komendy sieciowe
        self._command_types["netstat"] = NetstatCommand
        self._command_types["ping"] = PingCommand
        self._command_types["curl"] = CurlCommand
        self._command_types["wget"] = WgetCommand
        self._command_types["ssh"] = SshCommand

    def create_command(self, command_name: str) -> Optional[CommandInterface]:
        """Tworzy nową instancję komendy"""
        if command_name not in self._command_types:
            return None

        # Tworzymy nową instancję
        return self._command_types[command_name]()

    def register_command(self, alias: str, command: CommandInterface) -> None:
        """Rejestruje prekonfigurowaną komendę pod aliasem"""
        self._configured_commands[alias] = command

    def get_command(self, alias: str) -> Optional[CommandInterface]:
        """Pobiera prekonfigurowaną komendę według aliasu"""
        if alias not in self._configured_commands:
            return None

        # Zwracamy kopię, aby uniknąć modyfikacji oryginalnej komendy
        return cast(Optional[CommandInterface[Any]], self._configured_commands[alias].clone())

    def list_command_names(self) -> List[str]:
        """Zwraca listę nazw zarejestrowanych komend (do tworzenia przez create_command)."""
        return sorted(self._command_types.keys())
