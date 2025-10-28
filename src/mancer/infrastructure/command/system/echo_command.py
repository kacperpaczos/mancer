from typing import Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class EchoCommand(BaseCommand):
    """Command implementation for 'echo' to print text to stdout."""

    def __init__(self, message: str = ""):
        """Initialize echo command.

        Args:
            message: Optional text to print.
        """
        super().__init__("echo")
        if message:
            self.add_arg(message)

    def execute(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
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
