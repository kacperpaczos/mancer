from typing import Any, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand


class CpCommand(BaseCommand):
    """Komenda cp - kopiuje pliki i katalogi"""

    def __init__(self):
        super().__init__("cp")

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę cp"""
        # Budujemy komendę z uwzględnieniem kontekstu
        cmd_str = self.build_command()

        # Jeśli nie mamy źródła ani celu, a otrzymaliśmy wynik z poprzedniej komendy
        if "source" not in self.parameters and input_result and input_result.is_success():
            # Próbujemy znaleźć pliki w structured_output
            if input_result.structured_output:
                if isinstance(input_result.structured_output, list):
                    # Jeśli mamy listę słowników (np. z ls), używamy nazw plików
                    if (
                        isinstance(input_result.structured_output[0], dict)
                        and "name" in input_result.structured_output[0]
                    ):
                        sources = [item["name"] for item in input_result.structured_output]
                        cmd_str = f"{cmd_str} {' '.join(sources)}"
                    elif isinstance(input_result.structured_output[0], str):
                        # Jeśli mamy listę stringów, używamy ich bezpośrednio
                        sources = input_result.structured_output
                        cmd_str = f"{cmd_str} {' '.join(sources)}"

        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)

        # Wykonujemy komendę
        result = backend.execute_command(cmd_str, working_dir=context.current_directory)

        return result

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "CpCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: CpCommand = self.clone()  # type: ignore
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value) -> "CpCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: CpCommand = self.clone()  # type: ignore
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "CpCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: CpCommand = self.clone()  # type: ignore
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "CpCommand":
        """Return a new instance marked to require sudo."""
        new_instance: CpCommand = self.clone()  # type: ignore
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "CpCommand":
        """Return a new instance with an added positional argument."""
        new_instance: CpCommand = self.clone()  # type: ignore
        new_instance._args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "CpCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: CpCommand = self.clone()  # type: ignore
        new_instance.preferred_data_format = format_type
        return new_instance

    def _format_parameter(self, name: str, value: Any) -> str:
        """Specjalne formatowanie dla cp"""
        if name == "source" or name == "destination":
            return ""  # Te parametry są obsługiwane przez _get_additional_args
        return super()._format_parameter(name, value)

    def _get_additional_args(self) -> List[str]:
        """Dodaje źródło i cel, jeśli są ustawione"""
        args = super()._get_additional_args().copy()
        if "source" in self.parameters:
            if isinstance(self.parameters["source"], list):
                args.extend(self.parameters["source"])
            else:
                args.append(str(self.parameters["source"]))

        if "destination" in self.parameters:
            args.append(str(self.parameters["destination"]))

        return args

    # Metody specyficzne dla cp

    def recursive(self) -> "CpCommand":
        """Opcja -r - kopiuje rekurencyjnie katalogi"""
        return self.with_option("-r")

    def preserve(self) -> "CpCommand":
        """Opcja -p - zachowuje atrybuty plików"""
        return self.with_option("-p")

    def force(self) -> "CpCommand":
        """Opcja -f - wymusza nadpisanie plików"""
        return self.with_option("-f")

    def interactive(self) -> "CpCommand":
        """Opcja -i - pyta przed nadpisaniem plików"""
        return self.with_option("-i")

    def verbose(self) -> "CpCommand":
        """Opcja -v - wyświetla komunikaty o postępie"""
        return self.with_option("-v")

    def from_source(self, source: str) -> "CpCommand":
        """Ustawia źródło kopiowania"""
        return self.with_param("source", source)

    def to_destination(self, destination: str) -> "CpCommand":
        """Ustawia cel kopiowania"""
        return self.with_param("destination", destination)
