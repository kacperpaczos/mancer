from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class GrepCommand(BaseCommand):
    """Command implementation for the 'grep' command"""

    # Zdefiniuj nazwę narzędzia
    tool_name: ClassVar[str] = "grep"

    def __init__(self, name: str = "grep", pattern=None):
        """Initialize grep command.

        Args:
            name: Command name (default: "grep").
            pattern: Optional pattern to search for.
        """
        super().__init__(name=name)

        if pattern:
            self._args.append(pattern)

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Executes the grep command"""

        # Build command string based on provided parameters
        command_str = self.build_command()

        # Handle pipeline input
        if input_result and input_result.raw_output:
            backend = self._get_backend(context)
            exit_code, output, error = backend.execute_with_input(command_str, input_result.raw_output)
        else:
            # Execute the command with the appropriate backend
            backend = self._get_backend(context)
            exit_code, output, error = backend.execute(command_str)

        # Determine success
        success = exit_code == 0
        error_message = error if error and not success else None

        # Dodaj ostrzeżenia o wersji do metadanych
        metadata = {}
        warnings = context.get_parameter("warnings", [])
        if warnings:
            metadata["version_warnings"] = warnings

        # Create and return result
        return self._prepare_result(
            raw_output=output,
            success=success,
            exit_code=exit_code,
            error_message=error_message,
            metadata=metadata,
        )

    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse grep command output into structured format"""
        lines = raw_output.strip().split("\n")
        results = []

        for line in lines:
            if not line.strip():
                continue

            # Basic parsing - each line is a match
            results.append({"line": line, "text": line})  # For compatibility with other commands

        return results
