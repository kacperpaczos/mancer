from typing import List, Dict, Any, Optional
from ..base_command import BaseCommand
from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult

class CatCommand(BaseCommand):
    """Command implementation for the 'cat' command"""
    
    def __init__(self, file_path: str = ""):
        super().__init__("cat")
        if file_path:
            self._args.append(file_path)
    
    def execute(self, context: CommandContext, 
                input_result: Optional[CommandResult] = None) -> CommandResult:
        """Executes the cat command"""
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
            error_message=error_message
        )
    
    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse cat command output into structured format"""
        lines = raw_output.split('\n')
        
        # Create a structured representation of the file content
        results = []
        for i, line in enumerate(lines):
            results.append({
                'line_number': i + 1,  # 1-based line numbers
                'content': line
            })
        
        return results 