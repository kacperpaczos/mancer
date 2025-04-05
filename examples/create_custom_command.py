#!/usr/bin/env python3
"""
Example of creating a custom command with version adaptation

This example demonstrates:
1. How to create a custom command class
2. How to implement version-specific behavior adaptation
3. How to register allowed versions for a custom command
4. How to use version-specific parsers
"""

import sys
import os
import re
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mancer.infrastructure.command.base_command import BaseCommand
from src.mancer.infrastructure.command.versioned_command_mixin import VersionedCommandMixin
from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.model.command_result import CommandResult
from src.mancer.domain.service.tool_version_service import ToolVersionService
from src.mancer.domain.model.tool_version import ToolVersion
from src.mancer.domain.model.data_format import DataFormat


class CustomGreetingCommand(BaseCommand, VersionedCommandMixin):
    """
    Custom command implementation that says hello in different languages
    based on detected version
    """
    
    # Tool name for version checking
    tool_name = "greeting_tool"
    
    # Version adapters mapping
    version_adapters = {
        "1.x": "_generate_output_v1",
        "2.x": "_generate_output_v2",
        "3.x": "_generate_output_v3"
    }
    
    def __init__(self):
        BaseCommand.__init__(self, "greeting")
        self.name = "World"  # Default name to greet
        self.preferred_data_format = DataFormat.TEXT
    
    def execute(self, context: CommandContext, 
                input_result: Optional[CommandResult] = None) -> CommandResult:
        """Execute the greeting command"""
        # Call base method to check tool version
        super().execute(context, input_result)
        
        # Get the name from context parameters if provided
        name = context.get_parameter("name", self.name)
        
        # In a real command, you would build and execute a command string
        # Here we're just generating output based on version
        output = f"Hello, {name}!"
        
        # Create and return the result
        return self._prepare_result(
            raw_output=output,
            success=True,
            exit_code=0,
            error_message=None,
            metadata={}
        )
    
    def _parse_output(self, raw_output: str) -> Dict[str, Any]:
        """Default parser for greeting command output"""
        # Simple parsing of "Hello, {name}!"
        match = re.match(r"Hello, (.+)!", raw_output)
        if match:
            return {"greeting": "Hello", "name": match.group(1)}
        return {"raw": raw_output}
    
    def _generate_output_v1(self, raw_output: str) -> Dict[str, Any]:
        """
        Parser specific to version 1.x - simple English greeting
        """
        match = re.match(r"Hello, (.+)!", raw_output)
        if match:
            return {
                "greeting": "Hello",
                "name": match.group(1),
                "language": "English",
                "version": "1.x"
            }
        return {"raw": raw_output, "version": "1.x"}
    
    def _generate_output_v2(self, raw_output: str) -> Dict[str, Any]:
        """
        Parser specific to version 2.x - adds Spanish greeting
        """
        # First try English format
        match = re.match(r"Hello, (.+)!", raw_output)
        if match:
            return {
                "greeting": "Hello",
                "name": match.group(1),
                "language": "English",
                "version": "2.x",
                "translations": {
                    "es": f"Hola, {match.group(1)}!"
                }
            }
        
        # Then try Spanish format
        match = re.match(r"Hola, (.+)!", raw_output)
        if match:
            return {
                "greeting": "Hola",
                "name": match.group(1),
                "language": "Spanish",
                "version": "2.x",
                "translations": {
                    "en": f"Hello, {match.group(1)}!"
                }
            }
            
        return {"raw": raw_output, "version": "2.x"}
    
    def _generate_output_v3(self, raw_output: str) -> Dict[str, Any]:
        """
        Parser specific to version 3.x - adds French and German greetings
        """
        # Start with v2 parser as base
        result = self._generate_output_v2(raw_output)
        
        # Add additional translations and mark as v3
        result["version"] = "3.x"
        
        if "name" in result:
            name = result["name"]
            # Add French and German translations
            if "translations" not in result:
                result["translations"] = {}
                
            result["translations"]["fr"] = f"Bonjour, {name}!"
            result["translations"]["de"] = f"Hallo, {name}!"
            
            # Add timestamp for v3 feature
            import datetime
            result["timestamp"] = datetime.datetime.now().isoformat()
            
        return result
    
    def with_name(self, name: str) -> 'CustomGreetingCommand':
        """
        Set the name to greet
        
        Args:
            name: Name to greet
            
        Returns:
            Self for method chaining
        """
        self.name = name
        return self


def register_custom_tool_versions():
    """Register custom tool versions for demonstration"""
    version_service = ToolVersionService()
    
    # Register some allowed versions for our custom tool
    version_service.register_allowed_version("greeting_tool", "1.0.0")
    version_service.register_allowed_version("greeting_tool", "2.1.0")
    version_service.register_allowed_version("greeting_tool", "3.0.5")
    
    print("Registered allowed versions for greeting_tool:")
    allowed_versions = version_service.get_allowed_versions("greeting_tool")
    for version in allowed_versions:
        print(f"  - {version}")


def demonstrate_version_adaptation():
    """Demonstrate version-specific behavior adaptation"""
    # Create command instance
    greeting_command = CustomGreetingCommand()
    
    # Register a method to simulate version detection
    # In a real command, this would be detected from the system
    version_service = ToolVersionService()
    
    print("\n=== Testing custom command with different versions ===")
    
    # Test with different versions
    for version_str in ["1.0.0", "2.1.0", "3.0.5"]:
        print(f"\nTesting with version {version_str}:")
        
        # Create a version object
        version = ToolVersion("greeting_tool", version_str)
        
        # Mock version detection
        version_service.detect_tool_version = lambda tool_name: version if tool_name == "greeting_tool" else None
        
        # Create context
        context = CommandContext()
        context.add_parameter("name", "Mancer User")
        
        # Execute command
        result = greeting_command.execute(context)
        
        # Print the result
        print(f"Command output: {result.raw_output}")
        print("Structured output:")
        for key, value in result.structured_output.items():
            if key == "translations":
                print(f"  {key}:")
                for lang, trans in value.items():
                    print(f"    {lang}: {trans}")
            else:
                print(f"  {key}: {value}")


def main():
    """Main function executing all examples"""
    print("Mancer Framework - Custom Command Example with Version Adaptation")
    
    register_custom_tool_versions()
    demonstrate_version_adaptation()
    
    print("\nExample completed successfully")


if __name__ == "__main__":
    main() 