#!/usr/bin/env python3
"""
Example of using command chains (CommandChain) with execution history.
This example demonstrates:
1. Creating command chains using then() and pipe()
2. Tracking command execution history
3. Accessing data at different stages of execution
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
from src.mancer.infrastructure.command.system.grep_command import GrepCommand
from src.mancer.infrastructure.command.system.cat_command import CatCommand
from src.mancer.infrastructure.command.system.wc_command import WcCommand

def display_execution_history(result):
    """Displays the execution history of a command"""
    print("\n=== Execution History ===")
    history = result.get_history()
    for i, step in enumerate(history):
        print(f"Step {i+1}: {step.command_string}")
        print(f"  Command type: {step.command_type}")
        print(f"  Execution time: {step.timestamp.strftime('%H:%M:%S')}")
        print(f"  Status: {'✓' if step.success else '✗'}")
        print(f"  Data format: {DataFormat.to_string(step.data_format)}")
        if step.structured_sample:
            print(f"  Data sample: {step.structured_sample}")
        print("")

def main():
    # Initialize context
    context = CommandContext()
    
    print("=== Example 1: Sequential Command Execution (then) ===")
    # Create a command chain: ls -> grep -> wc
    command_chain = (
        LsCommand()
        .with_option("-la")
        .then(GrepCommand("py"))  # Filter .py files
        .then(WcCommand().with_option("-l"))  # Count lines
    )
    
    # Execute the chain
    result = command_chain.execute(context)
    
    print(f"Result: {result}")
    print(f"Status: {'Success' if result.is_success() else 'Failure'}")
    
    # Display execution history
    display_execution_history(result)
    
    print("\n=== Example 2: Pipeline Command Execution (pipe) ===")
    # Create a pipeline: cat -> grep
    command_pipe = (
        CatCommand("examples/basic_usage.py")
        .pipe(GrepCommand("mancer").with_option("-n"))  # Number lines with results
    )
    
    # Execute the pipeline
    result = command_pipe.execute(context)
    
    print(f"Result (first 3 lines):")
    lines = result.raw_output.split('\n')
    for i, line in enumerate(lines[:3]):
        print(f"  {line}")
    if len(lines) > 3:
        print(f"  ...")  # If more lines exist
    
    # Display execution history
    display_execution_history(result)
    
    print("\n=== Example 3: Command Chain with Data Format Conversion ===")
    # Create a command chain with data format conversion
    format_chain = (
        LsCommand().with_option("-la")
        .with_data_format(DataFormat.LIST)
        .then(GrepCommand("py")
              .with_data_format(DataFormat.JSON))  # Convert to JSON format
    )
    
    # Execute the chain
    result = format_chain.execute(context)
    
    print(f"Final data format: {DataFormat.to_string(result.get_format())}")
    print(f"Data type: {type(result.structured_output)}")
    print(f"Result snippet: {str(result.structured_output)[:100]}...")
    
    # Display execution history
    display_execution_history(result)
    
    print("\n=== Command Chain Metadata ===")
    if result.metadata and 'command_chain' in result.metadata:
        chain_info = result.metadata['command_chain']
        print(f"Number of commands: {chain_info['total_commands']}")
        print(f"Commands:")
        for i, cmd in enumerate(chain_info['commands']):
            pipe_info = " (pipe)" if chain_info['pipeline_steps'][i] else ""
            print(f"  {i+1}. {cmd}{pipe_info}")
    
if __name__ == "__main__":
    main()
