import os
from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ..base_command import BaseCommand


class FindCommand(BaseCommand):
    """Command implementation for the 'find' command"""

    def __init__(self, name: str = "find", path: str = "."):
        """Initialize find command.

        Args:
            name: Command name (default: "find").
            path: Path to search in (default: ".").
        """
        super().__init__(name=name)
        self.args.append(path)

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Executes the find command"""
        # Build the command string
        command_str = self.build_command()

        # Get the appropriate backend
        backend = self._get_backend(context)

        # Execute the command
        exit_code, output, error = backend.execute(command_str)

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

    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse find command output into structured format"""
        if not raw_output.strip():
            return []

        lines = raw_output.strip().split("\n")
        results = []

        for line in lines:
            path = line.strip()
            if not path:
                continue

            # Get file information
            try:
                basename = os.path.basename(path)
                dirname = os.path.dirname(path)
                is_dir = os.path.isdir(path)
                is_file = os.path.isfile(path)
                is_link = os.path.islink(path)
                extension = os.path.splitext(path)[1][1:] if os.path.splitext(path)[1] else ""

                results.append(
                    {
                        "path": path,
                        "basename": basename,
                        "dirname": dirname,
                        "is_directory": is_dir,
                        "is_file": is_file,
                        "is_link": is_link,
                        "extension": extension,
                    }
                )
            except Exception:
                # If there's an error getting file info, add just the path
                results.append({"path": path})

        return results
