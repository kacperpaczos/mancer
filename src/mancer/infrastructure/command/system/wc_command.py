import re
from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class WcCommand(BaseCommand):
    """Command implementation for the 'wc' (word count) command"""

    def __init__(self, file_path: str = ""):
        super().__init__("wc")
        if file_path:
            self._args.append(file_path)

    def execute(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
        """Executes the wc command"""
        # Build the command string
        command_str = self.build_command()

        # Get the appropriate backend
        backend = self._get_backend(context)

        # If we have input from a previous command, use it as stdin
        input_data = None
        if input_result and input_result.raw_output:
            input_data = input_result.raw_output

        # Execute the command
        exit_code, output, error = backend.execute(command_str, input_data=input_data)

        # Check if command was successful
        success = exit_code == 0
        error_message = error if error and not success else None

        # Parse the output
        structured_output = self._parse_output(output)

        # Create and return the result
        return self._prepare_result(
            raw_output=output,
            success=success,
            exit_code=exit_code,
            error_message=error_message,
        )

    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse wc command output into structured format"""
        if not raw_output.strip():
            return [{"lines": 0, "words": 0, "chars": 0, "filename": None}]

        results = []
        lines = raw_output.strip().split("\n")

        for line in lines:
            parts = re.split(r"\s+", line.strip())

            # Default structure for wc output
            result = {}

            # Different format based on options used
            if "-l" in self.options and len(parts) >= 2:
                # Only line count
                result["lines"] = int(parts[0])
                result["filename"] = parts[1] if len(parts) > 1 else None
            elif "-w" in self.options and len(parts) >= 2:
                # Only word count
                result["words"] = int(parts[0])
                result["filename"] = parts[1] if len(parts) > 1 else None
            elif "-c" in self.options and len(parts) >= 2:
                # Only byte/char count
                result["chars"] = int(parts[0])
                result["filename"] = parts[1] if len(parts) > 1 else None
            elif "-m" in self.options and len(parts) >= 2:
                # Only character count
                result["chars"] = int(parts[0])
                result["filename"] = parts[1] if len(parts) > 1 else None
            elif len(parts) >= 4:
                # Standard wc output: lines words chars filename
                result["lines"] = int(parts[0])
                result["words"] = int(parts[1])
                result["chars"] = int(parts[2])
                result["filename"] = parts[3] if len(parts) > 3 else None

            results.append(result)

        return results
