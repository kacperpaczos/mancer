from typing import List, Dict, Any, Optional
from ..base_command import BaseCommand
from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult

class LsCommand(BaseCommand):
    """Command implementation for the 'ls' command"""
    
    # Zdefiniuj nazwę narzędzia
    tool_name = "ls"
    
    def __init__(self):
        super().__init__("ls")
    
    def execute(self, context: CommandContext, 
                input_result: Optional[CommandResult] = None) -> CommandResult:
        """Executes the ls command"""
        # Wywołaj metodę bazową aby sprawdzić wersję narzędzia
        super().execute(context, input_result)
        
        # Build the command string
        command_str = self.build_command()
        
        # Get the appropriate backend
        backend = self._get_backend(context)
        
        # Execute the command
        exit_code, output, error = backend.execute(command_str)
        
        # Check if command was successful
        success = exit_code == 0
        error_message = error if error and not success else None
        
        # Dodaj ostrzeżenia o wersji do metadanych
        metadata = {}
        warnings = context.get_parameter("warnings", [])
        if warnings:
            metadata["version_warnings"] = warnings
        
        # Parse the output
        structured_output = self._parse_output(output)
        
        # Create and return the result
        return self._prepare_result(
            raw_output=output,
            success=success,
            exit_code=exit_code,
            error_message=error_message,
            metadata=metadata
        )
    
    def _parse_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse ls command output into structured format"""
        lines = raw_output.strip().split('\n')
        results = []
        
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split()
            if len(parts) < 8:
                continue
            
            # Standard format for ls -l output
            permissions = parts[0]
            links = parts[1]
            owner = parts[2]
            group = parts[3]
            size = parts[4]
            month = parts[5]
            day = parts[6]
            
            # The rest could be time or year and filename
            time_or_year = parts[7]
            filename = ' '.join(parts[8:])
            
            # If ls -la was used, skip . and .. entries from results if needed
            # if filename in ['.', '..']:
            #     continue
            
            results.append({
                'permissions': permissions,
                'links': links,
                'owner': owner,
                'group': group,
                'size': size,
                'month': month,
                'day': day,
                'time_or_year': time_or_year,
                'filename': filename,
                'is_directory': permissions.startswith('d'),
                'is_link': permissions.startswith('l'),
                'is_executable': 'x' in permissions
            })
        
        return results 