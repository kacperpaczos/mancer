from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand


class GrepCommand(BaseCommand):
    """Komenda grep - wyszukuje wzorce w plikach"""

    def __init__(self):
        super().__init__("grep")

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę grep"""
        # Jeśli mamy dane wejściowe, używamy ich jako standardowego wejścia
        stdin_data = None
        if input_result and input_result.raw_output:
            stdin_data = input_result.raw_output

        # Budujemy komendę
        cmd_str = self.build_command()

        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)

        # Wykonujemy komendę
        exit_code, output, error = backend.execute(
            cmd_str, input_data=stdin_data, working_dir=context.current_directory
        )

        # Sprawdzamy, czy komenda zakończyła się sukcesem
        success = exit_code == 0
        error_message = error if error and not success else None

        # Parsujemy wynik
        structured_output = self._parse_output(output)

        # Tworzymy i zwracamy wynik
        return CommandResult(
            raw_output=output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_message,
        )

    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parsuje wynik grep do listy słowników z dopasowaniami"""
        result = []
        lines = raw_output.strip().split("\n")

        for line in lines:
            if not line.strip():
                continue

            # Próbujemy rozpoznać format wyjścia
            # Standardowy format: plik:linia:treść
            parts = line.split(":", 2)

            if len(parts) >= 3:
                match_info = {
                    "file": parts[0],
                    "line_number": parts[1],
                    "content": parts[2],
                }
            elif len(parts) == 2:
                match_info = {"file": parts[0], "content": parts[1]}
            else:
                match_info = {"content": line}

            result.append(match_info)

        return result

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "GrepCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: GrepCommand = self.clone()
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value) -> "GrepCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: GrepCommand = self.clone()
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "GrepCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: GrepCommand = self.clone()
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "GrepCommand":
        """Return a new instance marked to require sudo."""
        new_instance: GrepCommand = self.clone()
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "GrepCommand":
        """Return a new instance with an added positional argument."""
        new_instance: GrepCommand = self.clone()
        new_instance._args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "GrepCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: GrepCommand = self.clone()
        new_instance.preferred_data_format = format_type
        return new_instance

    # Metody specyficzne dla grep

    def pattern(self, pattern: str) -> "GrepCommand":
        """Ustawia wzorzec do wyszukiwania"""
        # Wzorzec musi być pierwszym argumentem
        new_instance = self.clone()
        # Usuwamy wszystkie argumenty i dodajemy wzorzec jako pierwszy
        new_instance._args = []
        return new_instance.add_arg(pattern)

    def file(self, file_path: str) -> "GrepCommand":
        """Ustawia plik, w którym będzie wyszukiwany wzorzec"""
        return self.add_arg(file_path)

    def recursive(self) -> "GrepCommand":
        """Opcja -r - rekurencyjne wyszukiwanie w katalogach"""
        return self.with_option("-r")

    def ignore_case(self) -> "GrepCommand":
        """Opcja -i - ignoruje wielkość liter"""
        return self.with_option("-i")

    def line_number(self) -> "GrepCommand":
        """Opcja -n - pokazuje numery linii"""
        return self.with_option("-n")

    def count(self) -> "GrepCommand":
        """Opcja -c - pokazuje tylko liczbę dopasowanych linii"""
        return self.with_option("-c")

    def only_matching(self) -> "GrepCommand":
        """Opcja -o - pokazuje tylko dopasowane części linii"""
        return self.with_option("-o")

    def invert_match(self) -> "GrepCommand":
        """Opcja -v - pokazuje linie, które NIE pasują do wzorca"""
        return self.with_option("-v")

    def fixed_strings(self) -> "GrepCommand":
        """Opcja -F - traktuje wzorzec jako zwykły ciąg znaków, nie wyrażenie regularne"""
        return self.with_option("-F")

    def extended_regexp(self) -> "GrepCommand":
        """Opcja -E - używa rozszerzonych wyrażeń regularnych"""
        return self.with_option("-E")

    def clone(self) -> "GrepCommand":
        """Tworzy kopię komendy z tą samą konfiguracją"""
        new_instance: GrepCommand = super().clone()  # type: ignore
        new_instance._args = self._args.copy()
        return new_instance
