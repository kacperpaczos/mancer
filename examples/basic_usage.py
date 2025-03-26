#!/usr/bin/env python3
"""
Basic usage example for Mancer framework.
This example demonstrates:
1. Creating and executing simple commands
2. Using command chains with then() and pipe() methods
3. Working with different data formats
4. Tracking execution history
"""

import os
import sys
import json
from datetime import datetime

# Add mancer module path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.model.data_format import DataFormat
from src.mancer.infrastructure.command.system.ls_command import LsCommand
from src.mancer.infrastructure.command.system.ps_command import PsCommand
from src.mancer.infrastructure.command.system.grep_command import GrepCommand
from src.mancer.infrastructure.command.system.echo_command import EchoCommand
from src.mancer.infrastructure.command.system.df_command import DfCommand
from src.mancer.domain.model.command_result import CommandResult

def display_result_info(result, title="Command Result"):
    """Display information about command result including data format and history"""
    try:
        print(f"\n=== {title} ===")
        print(f"Success: {'✓' if result.is_success() else '✗'}")
        print(f"Data format: {result.data_format}")
        print(f"Exit code: {result.exit_code}")
        
        # Display the command that was executed
        history = result.get_history()
        if history and history.get_steps_count() > 0:
            last_step = history.get_last_step()
            if last_step:
                print(f"Wykonana komenda: {last_step.command_string}")
                print(f"Typ komendy: {last_step.command_type}")
        
        # Display a sample of the output
        print("\nOutput sample:")
        if result.raw_output:
            lines = result.raw_output.strip().split('\n')
            for i, line in enumerate(lines[:2]):  # Show only first 2 lines
                print(f"  {line}")
            if len(lines) > 2:
                print("  ...")
        else:
            print("  (No raw output)")
        
        # Display structured data sample
        print("\nStructured data sample:")
        if result.structured_output is not None and len(result.structured_output) > 0:
            try:
                for i, item in enumerate(result.structured_output[:1]):  # Show only first item
                    print(f"  Item 1: {str(item)[:150]}")  # Limit string length
                if len(result.structured_output) > 1:
                    print("  ...")
            except Exception as e:
                print(f"  Error displaying structured data: {str(e)}")
        else:
            print("  (No structured data)")
        
        # Flush output to ensure it's displayed immediately
        sys.stdout.flush()
        
    except Exception as e:
        print(f"\nError displaying result info: {str(e)}")
        sys.stdout.flush()

def main():
    # Initialize command context
    context = CommandContext()
    
    try:
        print("=== Basic Command Execution ===")
        # Create and execute a simple ls command
        ls_command = LsCommand().with_option("-la")
        result = ls_command.execute(context)
        display_result_info(result, "List Directory Contents")
        
        # Filter processes by name using pipe with short timeout
        print("\n=== Command Pipeline Example ===")
        pipeline = (
            PsCommand().with_option("-ef")
            .pipe(GrepCommand("python"))
        )
        result = pipeline.execute(context)
        display_result_info(result, "Filter Processes Containing 'python'")
        
        # Display disk usage information
        print("\n=== Working with Different Data Formats ===")
        df_command = DfCommand().with_flag("human-readable")
        result = df_command.execute(context)
        display_result_info(result, "Disk Usage Information")
        
        print("\nTest zakończony pomyślnie!")
        sys.stdout.flush()
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        sys.stdout.flush()
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

if __name__ == "__main__":
    main()
