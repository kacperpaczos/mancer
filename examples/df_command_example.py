#!/usr/bin/env python3
"""
Example of using DfCommand with version adaptation

This example demonstrates:
1. How to create and execute a DfCommand
2. How the command adapts its behavior based on the detected tool version
3. How to register allowed versions for the command
4. How to handle version warnings
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.model.tool_version import ToolVersion
from src.mancer.domain.service.tool_version_service import ToolVersionService
from src.mancer.infrastructure.command.system.df_command import DfCommand


def demonstrate_basic_usage():
    """Demonstrate basic usage of the df command"""
    print("\n=== Basic df command usage ===")

    # Create command instance
    df_command = DfCommand()

    # Create context (default)
    context = CommandContext()

    # Execute command
    result = df_command.execute(context)

    # Check if command was successful
    if result.success:
        print(f"Command executed successfully with exit code: {result.exit_code}")

        # Access parsed data
        filesystems = result.structured_output
        print(f"Found {len(filesystems)} filesystems")

        # Print the first filesystem info
        if filesystems:
            fs = filesystems[0]
            print("\nSample filesystem info:")
            for key, value in fs.items():
                print(f"  {key}: {value}")
    else:
        print(f"Command failed with error: {result.error_message}")


def demonstrate_version_detection():
    """Demonstrate version detection for df command"""
    print("\n=== df command version detection ===")

    # Create command instance
    df_command = DfCommand()

    # Create context
    context = CommandContext()

    # Get tool version service
    version_service = ToolVersionService()

    # Detect df version
    df_version = version_service.detect_tool_version("df")

    if df_version:
        print(f"Detected df version: {df_version.version_str}")
        print(f"Version details: {df_version.major}.{df_version.minor}.{df_version.patch}")
    else:
        print("Could not detect df version")


def demonstrate_version_adaptation():
    """Demonstrate how df command adapts behavior based on version"""
    print("\n=== df command version adaptation ===")

    # Create command instance
    df_command = DfCommand()

    # Create context
    context = CommandContext()

    # Execute command with automatic version detection
    result = df_command.execute(context)

    if result.success:
        # Get the detected version
        detected_version = df_command.detected_version

        if detected_version:
            print(f"Command adapted to df version: {detected_version.version_str}")
            print(
                f"Using parser method: {df_command.version_adapters.get(detected_version.get_version_x_format(), '_parse_output')}"
            )

            # Check for version-specific information in the results
            sample_entry = result.structured_output[0] if result.structured_output else {}
            if "parser_version" in sample_entry:
                print(f"Parser version marker in output: {sample_entry['parser_version']}")

            # Show version-specific features
            if detected_version.get_version_x_format() == "9.x" and "usage_ratio" in sample_entry:
                print(f"Version 9.x specific feature - Usage ratio: {sample_entry['usage_ratio']}")
        else:
            print("Command executed, but no version was detected. Using default parser.")
    else:
        print(f"Command failed with error: {result.error_message}")


def demonstrate_registering_versions():
    """Demonstrate how to register allowed versions"""
    print("\n=== Registering allowed versions for df ===")

    # Get tool version service
    version_service = ToolVersionService()

    # Current df version
    current_version = version_service.detect_tool_version("df")

    if current_version:
        # Register as allowed
        version_service.register_allowed_version("df", current_version.version_str)
        print(f"Registered df version {current_version.version_str} as allowed")

        # Check for allowed versions
        allowed_versions = version_service.get_allowed_versions("df")
        print(f"Allowed df versions: {', '.join(allowed_versions)}")
    else:
        print("Could not detect df version to register")


def main():
    """Main function executing all examples"""
    print("Mancer Framework - df Command Example with Version Adaptation")

    demonstrate_basic_usage()
    demonstrate_version_detection()
    demonstrate_version_adaptation()
    demonstrate_registering_versions()

    print("\nExample completed successfully")


if __name__ == "__main__":
    main()
