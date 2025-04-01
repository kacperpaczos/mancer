from typing import List, Dict, Any, Optional
import re
from ..base_command import BaseCommand
from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult

class GrepCommand(BaseCommand):
    """Command implementation for the 'grep' command"""
    
    def __init__(self, pattern: str = ""):
        super().__init__("grep")
        if pattern:
            self._args.append(pattern)
    
    def execute(self, context: CommandContext, 
                input_result: Optional[CommandResult] = None) -> CommandResult:
        """Executes the grep command"""
        # Build the command string
        command_str = self.build_command()
        
        # Get the appropriate backend
        backend = self._get_backend(context)
        
        # If we have input from a previous command, use it
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
        """Parse grep command output into structured format"""
        if not raw_output.strip():
            return []
        
        lines = raw_output.strip().split('\n')
        results = []
        
        line_number_regex = re.compile(r'^(\d+):(.*)$')
        
        for line in lines:
            if not line.strip():
                continue
            
            # Check if output includes line numbers (grep -n)
            line_num_match = line_number_regex.match(line)
            if line_num_match:
                line_number = int(line_num_match.group(1))
                content = line_num_match.group(2)
                results.append({
                    'line_number': line_number,
                    'content': content
                })
            else:
                # Regular grep output without line numbers
                results.append({
                    'content': line
                })
        
        return results 