from typing import Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand, ParamValue


class EchoCommand(BaseCommand):
    """Command implementation for 'echo' to print text to stdout."""

    command_str: Optional[str] = None

    def __init__(self, name: str = "echo", message: str = ""):
        """Initialize echo command.

        Args:
            name: Command name (default: "echo").
            message: Optional text to print.
        """
        super().__init__(name=name)
        if message:
            # Bezpośrednio dodaj do _args zamiast używać add_arg (które wywołuje clone)
            self.args.append(message)

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Execute the echo command."""
        # Build the command
        cmd_str = self.build_command()

        # Select backend
        backend = self._get_backend(context)

        # Execute command
        result = backend.execute_command(cmd_str, working_dir=context.current_directory)

        # Parse result: for echo we just capture text
        if result.success:
            result.structured_output = [{"text": result.raw_output.strip()}]

        return result

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "EchoCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: EchoCommand = self.clone()
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value: ParamValue) -> "EchoCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: EchoCommand = self.clone()
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "EchoCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: EchoCommand = self.clone()
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "EchoCommand":
        """Return a new instance marked to require sudo."""
        new_instance: EchoCommand = self.clone()
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "EchoCommand":
        """Return a new instance with an added positional argument."""
        new_instance: EchoCommand = self.clone()
        new_instance.args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "EchoCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: EchoCommand = self.clone()
        new_instance.preferred_data_format = format_type
        return new_instance

    # Metody specyficzne dla echo

    def text(self, message: str) -> "EchoCommand":
        """Set text to print."""
        return self.add_arg(message)

    def no_newline(self) -> "EchoCommand":
        """Option -n: do not output the trailing newline."""
        return self.with_option("-n")

    def enable_backslash_escapes(self) -> "EchoCommand":
        """Option -e: enable interpretation of backslash escapes."""
        return self.with_option("-e")

    def disable_backslash_escapes(self) -> "EchoCommand":
        """Option -E: disable interpretation of backslash escapes."""
        return self.with_option("-E")

    def to_file(self, file_path: str, append: bool = False) -> "EchoCommand":
        """Redirect output to a file.

        Args:
            file_path: Path to the target file.
            append: Append if True, overwrite if False.
        """
        new_instance: EchoCommand = self.clone()
        # Dodajemy przekierowanie do pliku
        if append:
            new_instance.pipeline = f">> {file_path}"
        else:
            new_instance.pipeline = f"> {file_path}"
        return new_instance

    def clone(self) -> "EchoCommand":
        """Tworzy kopię komendy z tą samą konfiguracją"""
        new_instance: EchoCommand = super().clone()
        return new_instance
