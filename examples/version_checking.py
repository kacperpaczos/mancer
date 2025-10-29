#!/usr/bin/env python3
"""
Demonstration example of the tool version checking mechanism in Mancer

This example shows:
1. How system tool versions are detected
2. How version mismatch warnings work
3. How to register your own tool versions
4. How commands adapt their behavior based on tool versions

Run this script with administrative privileges if you want to check tools that require elevated permissions.
"""

import logging
import os
import sys
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Add path to mancer module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.service.tool_version_service import ToolVersionService

# Create a sample version-adaptive command to demonstrate behavior changes
from src.mancer.infrastructure.command.base_command import BaseCommand
from src.mancer.infrastructure.command.system.cat_command import CatCommand
from src.mancer.infrastructure.command.system.df_command import DfCommand
from src.mancer.infrastructure.command.system.grep_command import GrepCommand
from src.mancer.infrastructure.command.system.ls_command import LsCommand
from src.mancer.infrastructure.command.system.ps_command import PsCommand

logger = logging.getLogger(__name__)


class DemoVersionAdaptiveCommand(BaseCommand):
    """Demo command that adapts its behavior based on the detected tool version"""

    tool_name = "ls"  # We'll use ls as the underlying tool

    # Define version-specific adapters
    version_adapters = {
        "8.x": "_parse_output_v8",
        "9.x": "_parse_output_v9",
    }

    def __init__(self):
        super().__init__("ls")

    def execute(self, context: CommandContext, input_result=None):
        # Call the base method to check tool version
        super().execute(context, input_result)

        # Build the command string
        command_str = self.build_command()

        # Get the appropriate backend
        backend = self._get_backend(context)

        # Execute the command
        exit_code, output, error = backend.execute(command_str)

        # Create result
        return self._prepare_result(
            raw_output=output,
            success=exit_code == 0,
            exit_code=exit_code,
            error_message=error if error and exit_code != 0 else None,
        )

    def _parse_output(self, raw_output):
        """Default parser for unknown versions"""
        return [
            {
                "message": "Using default parser for unknown version",
                "data": raw_output[:100],
            }
        ]

    def _parse_output_v8(self, raw_output):
        """Parser specific to version 8.x"""
        return [{"message": "Using v8.x specific parser", "data": raw_output[:100]}]

    def _parse_output_v9(self, raw_output):
        """Parser specific to version 9.x"""
        return [{"message": "Using v9.x specific parser", "data": raw_output[:100]}]


def detect_tool_versions():
    """Detects and displays system tool versions"""
    service = ToolVersionService()

    # List of tools to check
    tools = ["ls", "grep", "cat", "ps", "df", "find", "wc", "systemctl"]

    print("\n=== Detected Tool Versions ===")
    for tool in tools:
        tool_version = service.detect_tool_version(tool)
        if tool_version:
            print(f"{tool:12} --> {tool_version.version}")
        else:
            print(f"{tool:12} --> not detected")


def execute_with_version_check(command_name: str, command, context: CommandContext) -> None:
    """Executes a command with version checking enabled"""
    print(f"\n=== Executing command {command_name} with version verification ===")
    result = command.execute(context)

    print(f"Success: {'✓' if result.is_success() else '✗'}")

    # Check for version warnings
    if result.metadata and "version_warnings" in result.metadata:
        print("\nVersion warnings:")
        for warning in result.metadata["version_warnings"]:
            print(f"  - {warning}")
    else:
        print("\nNo version warnings")

    # Check for tool version information
    if result.metadata and "tool_version" in result.metadata:
        version_info = result.metadata["tool_version"]
        print(f"\nTool version: {version_info['name']} v{version_info['version']}")

    # Show a sample of the result
    if result.structured_output and len(result.structured_output) > 0:
        print("\nSample output data:")
        for i, item in enumerate(result.structured_output[:2]):
            print(f"  Item {i+1}: {str(item)[:150]}")
        if len(result.structured_output) > 2:
            print("  ...")


def register_custom_version():
    """Registers a custom tool version"""
    print("\n=== Registering custom allowed version of 'ls' ===")

    # Get current ls version
    service = ToolVersionService()
    ls_version = service.detect_tool_version("ls")

    if ls_version:
        print(f"Current ls version: {ls_version.version}")

        # Add current version to allowed versions
        LsCommand.register_allowed_version(ls_version.version)
        print(f"Registered version {ls_version.version} as allowed for 'ls'")
    else:
        print("Could not detect 'ls' version")


def demonstrate_version_adaptive_behavior():
    """Demonstrates command behavior adaptation based on tool version"""
    print("\n=== Demonstrating version-adaptive behavior ===")

    # Create context
    context = CommandContext()

    # Get ls version
    service = ToolVersionService()
    ls_version = service.detect_tool_version("ls")

    if ls_version:
        print(f"Detected ls version: {ls_version.version}")

        # Create and execute adaptive command
        adaptive_command = DemoVersionAdaptiveCommand()
        result = adaptive_command.execute(context)

        print(f"Success: {'✓' if result.is_success() else '✗'}")

        # Show which parser was used
        if result.structured_output and len(result.structured_output) > 0:
            message = result.structured_output[0].get("message", "No message")
            print(f"Parser used: {message}")
    else:
        print("Could not detect 'ls' version, cannot demonstrate version adaptation")


def main():
    try:
        # Detect tool versions
        detect_tool_versions()

        # Create execution context
        context = CommandContext()

        # Execute ls command
        ls_command = LsCommand().with_option("-la")
        execute_with_version_check("ls", ls_command, context)

        # Execute df command
        df_command = DfCommand().with_flag("human-readable")
        execute_with_version_check("df", df_command, context)

        # Register custom version
        register_custom_version()

        # Execute ls command again after registering custom version
        context = CommandContext()  # New context to clear warnings
        execute_with_version_check("ls (after custom version registration)", ls_command, context)

        # Demonstrate version-adaptive behavior
        demonstrate_version_adaptive_behavior()

        print("\nVersion checking demonstration completed successfully!")

    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
