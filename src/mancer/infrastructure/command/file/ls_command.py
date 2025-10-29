from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand


class LsCommand(BaseCommand):
    """Komenda ls - listuje pliki i katalogi"""

    def __init__(self):
        super().__init__("ls")

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę ls"""
        # Budujemy komendę z uwzględnieniem kontekstu
        cmd_str = self.build_command()

        # Jeśli nie ma ścieżki w parametrach, używamy bieżącego katalogu z kontekstu
        if "path" not in self.parameters:
            cmd_str = f"{cmd_str} {context.current_directory}"

        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)

        # Wykonujemy komendę
        result = backend.execute_command(cmd_str, working_dir=context.current_directory)

        # Parsujemy surowy wynik do formatu strukturalnego
        if result.success:
            result.structured_output = self._parse_output(result.raw_output)

        return result

    def _format_parameter(self, name: str, value: Any) -> str:
        """Specjalne formatowanie dla ls"""
        if name == "path":
            return str(value)
        return super()._format_parameter(name, value)

    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parsuje wyjście ls do listy słowników z informacjami o plikach"""
        result = []
        lines = raw_output.strip().split("\n")

        # Pomijamy pierwszą linię jeśli zaczyna się od "total"
        start_index = 0
        if lines and lines[0].startswith("total"):
            start_index = 1

        for line in lines[start_index:]:
            if not line.strip():
                continue

            parts = line.split(None, 8)  # Maksymalnie 9 części (8 odstępów)

            if len(parts) >= 9:  # Format długiego listingu (-l)
                file_info = {
                    "permissions": parts[0],
                    "links": parts[1],
                    "owner": parts[2],
                    "group": parts[3],
                    "size": parts[4],
                    "month": parts[5],
                    "day": parts[6],
                    "time": parts[7],
                    "name": parts[8],
                }
                result.append(file_info)
            elif len(parts) >= 1:  # Format krótkiego listingu
                result.append({"name": parts[0]})

        return result

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "LsCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: LsCommand = self.clone()  # type: ignore
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value) -> "LsCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: LsCommand = self.clone()  # type: ignore
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "LsCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: LsCommand = self.clone()  # type: ignore
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "LsCommand":
        """Return a new instance marked to require sudo."""
        new_instance: LsCommand = self.clone()  # type: ignore
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "LsCommand":
        """Return a new instance with an added positional argument."""
        new_instance: LsCommand = self.clone()  # type: ignore
        new_instance._args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "LsCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: LsCommand = self.clone()  # type: ignore
        new_instance.preferred_data_format = format_type
        return new_instance

    # Metody specyficzne dla ls

    def all(self) -> "LsCommand":
        """Opcja -a - pokazuje wszystkie pliki, łącznie z ukrytymi"""
        return self.with_option("-a")

    def long(self) -> "LsCommand":
        """Opcja -l - format długiego listingu"""
        return self.with_option("-l")

    def human_readable(self) -> "LsCommand":
        """Opcja -h - pokazuje rozmiary w formacie czytelnym dla człowieka"""
        return self.with_option("-h")

    def sort_by_size(self) -> "LsCommand":
        """Opcja -S - sortuje pliki według rozmiaru"""
        return self.with_option("-S")

    def sort_by_time(self) -> "LsCommand":
        """Opcja -t - sortuje pliki według czasu modyfikacji"""
        return self.with_option("-t")

    def in_directory(self, path: str) -> "LsCommand":
        """Ustawia katalog do listowania"""
        return self.with_param("path", path)
