import json
import re
from typing import Optional

import polars as pl

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class CustomCommand(BaseCommand):
    """Command implementation for any custom command.
    Allows for executing arbitrary shell commands.
    """

    def __init__(self, command_name: str = ""):
        super().__init__(command_name or "echo")

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Executes the custom command"""
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
        self._parse_output(output)

        # Create and return the result
        return self._prepare_result(
            raw_output=output,
            success=success,
            exit_code=exit_code,
            error_message=error_message,
        )

    def _parse_output(self, raw_output: str) -> pl.DataFrame:
        """Parse command output into polars DataFrame.
        Attempts to parse as JSON if the output looks like a JSON array or object.
        Otherwise, returns the raw output lines.
        """
        if not raw_output.strip():
            return pl.DataFrame()

        # Check if output is JSON
        try:
            if (raw_output.strip().startswith("[") and raw_output.strip().endswith("]")) or (
                raw_output.strip().startswith("{") and raw_output.strip().endswith("}")
            ):
                json_data = json.loads(raw_output)

                # If JSON is a list, convert to DataFrame
                if isinstance(json_data, list):
                    return pl.DataFrame(json_data)
                # If JSON is an object, wrap it in a list and convert
                elif isinstance(json_data, dict):
                    return pl.DataFrame([json_data])
        except json.JSONDecodeError:
            pass  # Not valid JSON, continue with line-based parsing

        # Default line-based parsing
        lines = raw_output.strip().split("\n")
        records = []

        for line in lines:
            if not line.strip():
                continue

            # Try to parse each line as a key-value pair (common format)
            kv_match = re.match(r"^([^:]+):\s*(.*)$", line)
            if kv_match:
                key = kv_match.group(1).strip()
                value = kv_match.group(2).strip()
                records.append({"raw_line": line, key: value})
            else:
                # Just a plain line
                records.append({"raw_line": line, "line": line.strip()})

        return pl.DataFrame(records)
