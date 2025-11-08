from typing import Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand, ParamValue


class NetstatCommand(BaseCommand):
    """Komenda netstat - wyświetla połączenia sieciowe"""

    def __init__(self):
        super().__init__(name="netstat")

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę netstat"""
        # Budujemy komendę
        cmd_str = self.build_command()

        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)

        # Wykonujemy komendę
        result = backend.execute_command(cmd_str, working_dir=context.current_directory)

        # Parsujemy wynik
        if result.success:
            result.structured_output = self._parse_output(result.raw_output)

        return result

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "NetstatCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: NetstatCommand = self.clone()
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value: ParamValue) -> "NetstatCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: NetstatCommand = self.clone()
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "NetstatCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: NetstatCommand = self.clone()
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "NetstatCommand":
        """Return a new instance marked to require sudo."""
        new_instance: NetstatCommand = self.clone()
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "NetstatCommand":
        """Return a new instance with an added positional argument."""
        new_instance: NetstatCommand = self.clone()
        new_instance.args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "NetstatCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: NetstatCommand = self.clone()
        new_instance.preferred_data_format = format_type
        return new_instance

    def _parse_output(self, raw_output: str) -> List[Dict[str, str]]:
        """Parsuje wynik netstat do listy słowników z informacjami o połączeniach"""
        result: List[Dict[str, str]] = []
        lines = raw_output.strip().split("\n")

        # Znajdź linię nagłówkową
        header_index = -1
        for i, line in enumerate(lines):
            if "Proto" in line and "Local Address" in line:
                header_index = i
                break

        if header_index == -1 or header_index >= len(lines) - 1:
            return result

        # Parsuj nagłówek
        header = lines[header_index]
        column_names = []
        column_positions = []

        # Znajdź pozycje kolumn
        current_pos = 0
        for term in [
            "Proto",
            "Recv-Q",
            "Send-Q",
            "Local Address",
            "Foreign Address",
            "State",
        ]:
            pos = header.find(term, current_pos)
            if pos != -1:
                column_positions.append(pos)
                column_names.append(term.lower().replace("-", "_"))
                current_pos = pos + len(term)

        # Dodaj końcową pozycję
        column_positions.append(len(header) + 1)

        # Parsuj dane
        for i in range(header_index + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue

            connection = {}
            for j in range(len(column_names)):
                start = column_positions[j]
                end = column_positions[j + 1] if j + 1 < len(column_positions) else len(line)

                value = line[start:end].strip()
                connection[column_names[j]] = value

            result.append(connection)

        return result

    # Metody specyficzne dla netstat

    def tcp(self) -> "NetstatCommand":
        """Opcja -t - pokazuje tylko połączenia TCP"""
        return self.with_option("-t")

    def udp(self) -> "NetstatCommand":
        """Opcja -u - pokazuje tylko połączenia UDP"""
        return self.with_option("-u")

    def listening(self) -> "NetstatCommand":
        """Opcja -l - pokazuje tylko nasłuchujące sockety"""
        return self.with_option("-l")

    def all(self) -> "NetstatCommand":
        """Opcja -a - pokazuje wszystkie połączenia"""
        return self.with_option("-a")

    def numeric(self) -> "NetstatCommand":
        """Opcja -n - adresy w formie numerycznej, bez tłumaczenia nazw"""
        return self.with_option("-n")

    def programs(self) -> "NetstatCommand":
        """Opcja -p - pokazuje programy/PID używające portów"""
        return self.with_option("-p")

    def continuous(self, interval: int = 1) -> "NetstatCommand":
        """Opcja -c - ciągłe odświeżanie (co określony interwał)"""
        return self.with_option("-c").with_param("interval", str(interval))

    def routes(self) -> "NetstatCommand":
        """Opcja -r - pokazuje tablice routingu"""
        return self.with_option("-r")
