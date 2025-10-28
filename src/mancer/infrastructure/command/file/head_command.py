from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class HeadCommand(BaseCommand):
    """Komenda head - wyświetla początkowe linie pliku"""

    def __init__(self):
        super().__init__("head")

    def execute(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
        """Wykonuje komendę head"""
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
        """Parsuje wynik head do listy słowników z liniami pliku"""
        result = []
        lines = raw_output.split("\n")

        # Sprawdzamy, czy wynik zawiera nagłówki plików (gdy używamy wielu plików)
        has_headers = False
        for line in lines:
            if line.startswith("==> ") and line.endswith(" <=="):
                has_headers = True
                break

        if has_headers:
            # Parsowanie wyniku z wieloma plikami
            current_file = None
            line_number = 0

            for line in lines:
                if line.startswith("==> ") and line.endswith(" <=="):
                    # Znaleziono nagłówek pliku
                    current_file = line[4:-4]  # Wyodrębniamy nazwę pliku
                    line_number = 0
                else:
                    line_number += 1
                    result.append(
                        {
                            "file": current_file,
                            "line_number": line_number,
                            "content": line,
                        }
                    )
        else:
            # Parsowanie wyniku z jednym plikiem
            for i, line in enumerate(lines):
                result.append({"line_number": i + 1, "content": line})

        return result

    def _format_parameter(self, name: str, value: Any) -> str:
        """Specjalne formatowanie dla head"""
        if name == "n":
            return f"-n{value}"  # Format -n5 zamiast --n=5
        return super()._format_parameter(name, value)

    # Metody specyficzne dla head

    def file(self, file_path: str) -> "HeadCommand":
        """Ustawia plik do wyświetlenia"""
        return self.add_arg(file_path)

    def files(self, file_paths: List[str]) -> "HeadCommand":
        """Ustawia wiele plików do wyświetlenia"""
        return self.add_args(file_paths)

    def lines(self, num_lines: int) -> "HeadCommand":
        """Opcja -n - określa liczbę linii do wyświetlenia"""
        return self.with_param("n", str(num_lines))

    def bytes(self, num_bytes: int) -> "HeadCommand":
        """Opcja -c - określa liczbę bajtów do wyświetlenia"""
        return self.with_param("c", str(num_bytes))

    def quiet(self) -> "HeadCommand":
        """Opcja -q - nie wyświetla nagłówków przy wyświetlaniu wielu plików"""
        return self.with_option("-q")

    def verbose(self) -> "HeadCommand":
        """Opcja -v - zawsze wyświetla nagłówki przy wyświetlaniu plików"""
        return self.with_option("-v")

    def clone(self) -> "HeadCommand":
        """Tworzy kopię komendy z tą samą konfiguracją"""
        new_instance: HeadCommand = super().clone()
        return new_instance
