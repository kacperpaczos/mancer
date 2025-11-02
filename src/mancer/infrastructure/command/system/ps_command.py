from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand


class PsCommand(BaseCommand):
    """Command implementation for 'ps' to display running processes."""

    # Tool name
    tool_name = "ps"

    def __init__(self, name: str = "ps"):
        """Initialize ps command.

        Args:
            name: Command name (default: "ps").
        """
        super().__init__(name)
        self.preferred_data_format = DataFormat.TABLE

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Execute the ps command and return a structured result."""
        super().execute(context, input_result)  # type: ignore

        command_str = self.build_command()
        backend = self._get_backend(context)
        exit_code, output, error = backend.execute(command_str)

        success = exit_code == 0
        error_message = error if error and not success else None

        metadata = {}
        warnings = context.get_parameter("warnings", [])
        if warnings:
            metadata["version_warnings"] = warnings

        return self._prepare_result(
            raw_output=output,
            success=success,
            exit_code=exit_code,
            error_message=error_message,
            metadata=metadata,
        )

    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse ps output to a list of dictionaries with process information."""
        result: List[Dict[str, Any]] = []
        lines = raw_output.strip().split("\n")

        if len(lines) < 2:
            return result

        # Parse header to detect column start positions and names
        header = lines[0]
        col_positions = []
        col_names = []
        in_space = True

        for i, char in enumerate(header):
            if char.isspace():
                in_space = True
            elif in_space:
                in_space = False
                col_positions.append(i)

                # Extract the column name from this start position
                col_name = ""
                for j in range(i, len(header)):
                    if header[j].isspace():
                        break
                    col_name += header[j]
                col_names.append(col_name)

        # Parsujemy każdy wiersz danych
        for i in range(1, len(lines)):
            line = lines[i]
            if not line.strip():
                continue

            process_info = {}

            # Dla każdej kolumny, wyodrębnij jej wartość
            for j in range(len(col_positions)):
                start = col_positions[j]
                end = col_positions[j + 1] if j + 1 < len(col_positions) else len(line)

                # Przytnij białe znaki
                value = line[start:end].strip()

                # Dodaj do informacji o procesie
                process_info[col_names[j].lower()] = value

            result.append(process_info)

        return result

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "PsCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: PsCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value) -> "PsCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: PsCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "PsCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: PsCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "PsCommand":
        """Return a new instance marked to require sudo."""
        new_instance: PsCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "PsCommand":
        """Return a new instance with an added positional argument."""
        new_instance: PsCommand = self.clone()  # type: ignore  # type: ignore
        new_instance._args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "PsCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: PsCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.preferred_data_format = format_type
        return new_instance

    # ps specific helpers

    def all(self) -> "PsCommand":
        """Option -e: show all processes."""
        return self.with_option("-e")

    def full_format(self) -> "PsCommand":
        """Option -f: full format."""
        return self.with_option("-f")

    def long_format(self) -> "PsCommand":
        """Option -l: long format."""
        return self.with_option("-l")

    def user(self, username: str) -> "PsCommand":
        """Option -u: processes for a specific user."""
        return self.with_param("u", username)

    def search(self, pattern: str) -> "PsCommand":
        """Pipe ps output through grep with the given pattern."""
        new_instance: PsCommand = self.clone()  # type: ignore
        new_instance.pipeline = f"grep {pattern}"
        return new_instance

    def aux(self) -> "PsCommand":
        """Option aux: show processes for all users with extra info."""
        return self.with_option("aux")
