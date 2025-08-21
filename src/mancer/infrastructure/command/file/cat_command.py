from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class CatCommand(BaseCommand):
    """Komenda cat - wyświetla zawartość plików"""

    def __init__(self):
        super().__init__("cat")

    def execute(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
        """Wykonuje komendę cat"""
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
        """Parsuje wynik cat do listy słowników z liniami pliku"""
        result = []
        lines = raw_output.split("\n")

        for i, line in enumerate(lines):
            result.append({"line_number": i + 1, "content": line})

        return result

    # Metody specyficzne dla cat

    def file(self, file_path: str) -> "CatCommand":
        """Ustawia plik do wyświetlenia"""
        return self.add_arg(file_path)

    def files(self, file_paths: List[str]) -> "CatCommand":
        """Ustawia wiele plików do wyświetlenia"""
        return self.add_args(file_paths)

    def show_line_numbers(self) -> "CatCommand":
        """Opcja -n - pokazuje numery linii"""
        return self.with_option("-n")

    def show_ends(self) -> "CatCommand":
        """Opcja -E - pokazuje znaki końca linii jako $"""
        return self.with_option("-E")

    def show_tabs(self) -> "CatCommand":
        """Opcja -T - pokazuje znaki tabulacji jako ^I"""
        return self.with_option("-T")

    def show_all(self) -> "CatCommand":
        """Opcja -A - pokazuje wszystkie znaki kontrolne"""
        return self.with_option("-A")

    def squeeze_blank(self) -> "CatCommand":
        """Opcja -s - zastępuje wiele pustych linii jedną"""
        return self.with_option("-s")

    def to_file(self, file_path: str, append: bool = False) -> "CatCommand":
        """
        Przekierowuje wyjście do pliku

        Args:
            file_path: Ścieżka do pliku
            append: Czy dopisać do pliku (True) czy nadpisać (False)
        """
        new_instance = self.clone()
        # Dodajemy przekierowanie do pliku
        if append:
            new_instance.pipeline = f">> {file_path}"
        else:
            new_instance.pipeline = f"> {file_path}"
        return new_instance

    def clone(self) -> "CatCommand":
        """Tworzy kopię komendy z tą samą konfiguracją"""
        new_instance = super().clone()
        return new_instance
