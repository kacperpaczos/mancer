from typing import List, Any, Optional, Dict
import re
from ..base_command import BaseCommand
from ...backend.bash_backend import BashBackend
from ....domain.model.command_result import CommandResult
from ....domain.model.command_context import CommandContext
from ....domain.model.data_format import DataFormat

class PsCommand(BaseCommand):
    """Command implementation for 'ps' to display running processes."""

    # Tool name
    tool_name = "ps"
    
    def __init__(self):
        super().__init__("ps")
        self.preferred_data_format = DataFormat.TABLE
    
    def execute(self, context: CommandContext,
                input_result: Optional[CommandResult] = None) -> CommandResult:
        """Execute the ps command and return a structured result."""
        super().execute(context, input_result)

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
            metadata=metadata
        )
    
    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse ps output to a list of dictionaries with process information."""
        result = []
        lines = raw_output.strip().split('\n')

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
                end = col_positions[j+1] if j+1 < len(col_positions) else len(line)
                
                # Przytnij białe znaki
                value = line[start:end].strip()
                
                # Dodaj do informacji o procesie
                process_info[col_names[j].lower()] = value
            
            result.append(process_info)
        
        return result
    
    # ps specific helpers

    def all(self) -> 'PsCommand':
        """Option -e: show all processes."""
        return self.with_option("-e")
    
    def full_format(self) -> 'PsCommand':
        """Option -f: full format."""
        return self.with_option("-f")
    
    def long_format(self) -> 'PsCommand':
        """Option -l: long format."""
        return self.with_option("-l")
    
    def user(self, username: str) -> 'PsCommand':
        """Option -u: processes for a specific user."""
        return self.with_param("u", username)
    
    def search(self, pattern: str) -> 'PsCommand':
        """Pipe ps output through grep with the given pattern."""
        new_instance = self.clone()
        new_instance.pipeline = f"grep {pattern}"
        return new_instance
        
    def aux(self) -> 'PsCommand':
        """Option aux: show processes for all users with extra info."""
        return self.with_option("aux")