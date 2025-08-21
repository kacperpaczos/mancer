#!/usr/bin/env python3
"""
Example of using execution history for debugging and analysis.
This example demonstrates:
1. Advanced tracking of command execution history
2. Analyzing execution time for each step
3. Identifying problems in command chains
"""

import json
import os
import sys
import time
from datetime import datetime
from pprint import pprint

# Add mancer module path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.model.data_format import DataFormat
from src.mancer.domain.model.execution_history import ExecutionHistory
from src.mancer.infrastructure.command.custom.custom_command import CustomCommand
from src.mancer.infrastructure.command.system.find_command import FindCommand
from src.mancer.infrastructure.command.system.grep_command import GrepCommand
from src.mancer.infrastructure.command.system.ls_command import LsCommand
from src.mancer.infrastructure.command.system.ps_command import PsCommand
from src.mancer.infrastructure.command.system.wc_command import WcCommand


def analyze_execution_history(history):
    """Analyzes execution history for timing and issues"""
    print("\n=== Execution History Analysis ===")

    # If history is empty
    if not history.get_steps_count():
        print("History is empty.")
        return

    # General information
    total_steps = history.get_steps_count()
    successful_steps = sum(1 for step in history if step.success)

    print(f"Number of steps: {total_steps}")
    print(
        f"Successful steps: {successful_steps}/{total_steps} ({successful_steps/total_steps*100:.1f}%)"
    )

    # Time analysis
    if total_steps > 1:
        start_time = history.steps[0].timestamp
        end_time = history.steps[-1].timestamp
        total_execution_time = (end_time - start_time).total_seconds()
        print(f"Total execution time: {total_execution_time:.3f} seconds")

        # Analysis of individual step times
        print("\nExecution time of individual steps:")
        for i in range(1, total_steps):
            step_time = (
                history.steps[i].timestamp - history.steps[i - 1].timestamp
            ).total_seconds()
            print(f"  Step {i} -> {i+1}: {step_time:.3f}s")

    # Problem analysis
    failed_steps = [i for i, step in enumerate(history) if not step.success]
    if failed_steps:
        print("\nProblematic steps:")
        for i in failed_steps:
            step = history.steps[i]
            print(f"  Step {i+1}: {step.command_string}")
            print(f"    Exit code: {step.exit_code}")
            if step.metadata and "error_message" in step.metadata:
                print(f"    Error: {step.metadata['error_message']}")

    # Data format analysis
    print("\nData format usage:")
    format_counts = {}
    for step in history:
        format_name = DataFormat.to_string(step.data_format)
        format_counts[format_name] = format_counts.get(format_name, 0) + 1

    for format_name, count in format_counts.items():
        print(f"  {format_name}: {count} steps ({count/total_steps*100:.1f}%)")


def simulate_command_chain_with_delay():
    """Simulates a command chain with deliberate delays for time analysis demo"""
    # Initialize context
    context = CommandContext()

    # Create a command chain
    command_chain = (
        LsCommand()
        .with_option("-la")
        .then(lambda: time.sleep(0.3) or GrepCommand("py"))
        .then(lambda: time.sleep(0.7) or FindCommand(".").with_param("name", "*.py"))
    )

    # Execute the chain
    result = command_chain.execute(context)

    return result


def simulate_command_chain_with_error():
    """Simulates a command chain with a deliberate error for problem detection demo"""
    # Initialize context
    context = CommandContext()

    # Create a command chain with an error (non-existent command)
    command_chain = (
        PsCommand()
        .with_option("-ef")
        .then(GrepCommand("python"))
        .then(CustomCommand("non_existent_command"))  # This command doesn't exist
    )

    # Execute the chain
    try:
        result = command_chain.execute(context)
    except Exception as e:
        print(f"Caught exception: {str(e)}")
        # In practice, we can still have partial history even after an exception
        return command_chain.get_history()

    return result.get_history()


def simulate_data_format_chain():
    """Simulates a command chain with different data formats"""
    # Initialize context
    context = CommandContext()

    # Create a command chain with different data formats
    command_chain = (
        LsCommand()
        .with_option("-la")
        .with_data_format(DataFormat.LIST)
        .then(GrepCommand("py").with_data_format(DataFormat.JSON))
        .then(WcCommand().with_option("-l").with_data_format(DataFormat.DATAFRAME))
    )

    # Execute the chain
    try:
        result = command_chain.execute(context)
        return result
    except Exception as e:
        print(f"Caught exception in data format chain: {str(e)}")
        return command_chain.get_history()


def main():
    print("=== Example 1: Execution Time Analysis ===")
    print("Executing command chain with deliberate delays...")
    result = simulate_command_chain_with_delay()

    # Analyze execution history
    analyze_execution_history(result.get_history())

    print("\n=== Example 2: Problem Detection in Command Chains ===")
    print("Executing command chain with a deliberate error...")
    history = simulate_command_chain_with_error()

    # Analyze execution history
    analyze_execution_history(history)

    print("\n=== Example 3: Data Format Conversion Chain ===")
    print("Executing command chain with different data formats...")
    format_result = simulate_data_format_chain()

    # If we got a result object, analyze its history
    if hasattr(format_result, "get_history"):
        analyze_execution_history(format_result.get_history())
    else:
        # Otherwise, it's already a history object
        analyze_execution_history(format_result)

    print("\n=== Example 4: Execution History Visualization ===")
    print("Execution history as JSON:")
    history_dict = result.get_history().to_dict()
    print(json.dumps(history_dict, indent=2)[:500] + "...")  # Show first 500 chars


if __name__ == "__main__":
    main()
