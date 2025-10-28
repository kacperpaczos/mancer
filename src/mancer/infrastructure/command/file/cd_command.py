import os
from typing import List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand


class CdCommand(BaseCommand):
    """Komenda cd - zmienia aktualny katalog"""

    def __init__(self):
        super().__init__("cd")

    def execute(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
        """Wykonuje komendę cd - zmienia katalog w kontekście"""
        # Pobieramy ścieżkę docelową
        target_path = None

        # Jeśli otrzymaliśmy wynik z poprzedniej komendy
        if input_result and input_result.is_success() and "directory" not in self.parameters:
            # Próbujemy znaleźć katalog w structured_output
            if input_result.structured_output:
                if (
                    isinstance(input_result.structured_output[0], dict)
                    and "name" in input_result.structured_output[0]
                ):
                    # Jeśli mamy listę słowników (np. z ls), bierzemy pierwszy element
                    target_path = input_result.structured_output[0]["name"]
                elif isinstance(input_result.structured_output[0], str):
                    # Jeśli mamy listę stringów, bierzemy pierwszy
                    target_path = input_result.structured_output[0]

        # Jeśli nie znaleźliśmy ścieżki w wyniku, sprawdzamy parametry
        if target_path is None:
            target_path = self.parameters.get("directory", ".")

        # Budujemy pełną ścieżkę względem bieżącego katalogu
        if not os.path.isabs(target_path):
            full_path = os.path.normpath(os.path.join(context.current_directory, target_path))
        else:
            full_path = target_path

        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)

        # W przypadku zdalnego wykonania, musimy sprawdzić, czy katalog istnieje
        if context.is_remote():
            # Wykonujemy komendę "test -d <path>" na zdalnym hoście
            test_cmd = f"test -d {full_path} && echo 'exists' || echo 'not_exists'"
            test_result = backend.execute_command(test_cmd)

            if "not_exists" in test_result.raw_output:
                return CommandResult(
                    raw_output="",
                    success=False,
                    structured_output=[],
                    exit_code=1,
                    error_message=f"cd: {target_path}: Nie ma takiego pliku ani katalogu",
                )
        else:
            # Lokalnie sprawdzamy, czy katalog istnieje
            if not os.path.isdir(full_path):
                return CommandResult(
                    raw_output="",
                    success=False,
                    structured_output=[],
                    exit_code=1,
                    error_message=f"cd: {target_path}: Nie ma takiego pliku ani katalogu",
                )

        # Aktualizujemy kontekst
        context.change_directory(full_path)

        # Zwracamy sukces
        return CommandResult(
            raw_output="", success=True, structured_output=[full_path], exit_code=0
        )

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "CdCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: CdCommand = self.clone()  # type: ignore
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value) -> "CdCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: CdCommand = self.clone()  # type: ignore
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "CdCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: CdCommand = self.clone()  # type: ignore
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "CdCommand":
        """Return a new instance marked to require sudo."""
        new_instance: CdCommand = self.clone()  # type: ignore
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "CdCommand":
        """Return a new instance with an added positional argument."""
        new_instance: CdCommand = self.clone()  # type: ignore
        new_instance._args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "CdCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: CdCommand = self.clone()  # type: ignore
        new_instance.preferred_data_format = format_type
        return new_instance

    def _get_additional_args(self) -> List[str]:
        """Dodaje ścieżkę docelową, jeśli jest ustawiona"""
        if "directory" in self.parameters:
            return [self.parameters["directory"]]
        return []

    def to_directory(self, directory: str) -> "CdCommand":
        """Ustawia katalog docelowy"""
        return self.with_param("directory", directory)
