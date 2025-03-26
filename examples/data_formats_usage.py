#!/usr/bin/env python3
"""
Example of using different data formats and conversions between them.
This example demonstrates:
1. Executing commands with different data formats
2. Converting between formats
3. Using pandas and numpy for data analysis from command results
"""

import os
import sys
import json
import numpy as np
import pandas as pd

# Add mancer module path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.model.data_format import DataFormat
from src.mancer.infrastructure.command.system.ls_command import LsCommand
from src.mancer.infrastructure.command.system.ps_command import PsCommand
from src.mancer.infrastructure.command.custom.custom_command import CustomCommand

def print_separator():
    print("\n" + "="*60 + "\n")

def display_history_summary(result):
    """Displays a summary of the execution history"""
    history = result.get_history()
    print(f"History steps: {history.get_steps_count()}")
    print(f"All successful: {history.all_successful()}")
    if history.get_steps_count() > 0:
        last_step = history.get_last_step()
        print(f"Last command: {last_step.command_string}")
        print(f"Command type: {last_step.command_type}")

def main():
    # Initialize context
    context = CommandContext()
    
    print_separator()
    print("=== Example 1: Using Different Data Formats ===")
    print_separator()
    
    # LIST format (default)
    print("LIST Format (default):")
    ls_command = LsCommand().with_option("-la")
    result_list = ls_command.execute(context)
    print(f"Data type: {type(result_list.structured_output)}")
    print(f"Data format: {result_list.data_format}")
    print(f"First 3 elements: {result_list.structured_output[:3]}")
    
    # Display history summary
    print("\nExecution history summary:")
    display_history_summary(result_list)
    
    print_separator()
    
    # JSON format
    print("JSON Format:")
    ls_json = LsCommand().with_option("-la").with_data_format(DataFormat.JSON)
    result_json = ls_json.execute(context)
    print(f"Data type: {type(result_json.structured_output)}")
    print(f"Data format: {result_json.data_format}")
    print(f"JSON snippet: {result_json.structured_output[:100]}...")  # Show a snippet of JSON
    
    # Display history summary
    print("\nExecution history summary:")
    display_history_summary(result_json)
    
    print_separator()
    
    # DATAFRAME format
    print("DATAFRAME Format:")
    ps_df = PsCommand().with_option("-ef").with_data_format(DataFormat.DATAFRAME)
    result_df = ps_df.execute(context)
    print(f"Data type: {type(result_df.structured_output)}")
    print(f"Data format: {result_df.data_format}")
    print("DataFrame headers:")
    print(result_df.structured_output.columns.tolist())
    print("\nFirst 3 rows:")
    print(result_df.structured_output.head(3))
    
    # Display history summary
    print("\nExecution history summary:")
    display_history_summary(result_df)
    
    print_separator()
    print("=== Example 2: Converting Between Formats ===")
    print_separator()
    
    # Converting from LIST to DATAFRAME
    print("Converting from LIST to DATAFRAME:")
    df_converted = result_list.to_format(DataFormat.DATAFRAME)
    print(f"Original format: {result_list.data_format}")
    print(f"New format: {df_converted.data_format}")
    print(f"Data type: {type(df_converted.structured_output)}")
    print("\nFirst 3 rows:")
    print(df_converted.structured_output.head(3))
    
    print_separator()
    
    # Converting from DATAFRAME to NDARRAY
    print("Converting from DATAFRAME to NDARRAY:")
    ndarray_converted = result_df.to_format(DataFormat.NDARRAY)
    print(f"Original format: {result_df.data_format}")
    print(f"New format: {ndarray_converted.data_format}")
    print(f"Data type: {type(ndarray_converted.structured_output)}")
    print(f"NDARRAY shape: {ndarray_converted.structured_output.shape}")
    print("\nFirst 3 rows (first 5 columns):")
    print(ndarray_converted.structured_output[:3, :5])
    
    print_separator()
    print("=== Example 3: Data Analysis Using Pandas ===")
    print_separator()
    
    # Creating a custom command that generates data
    data_command = CustomCommand("echo").add_arg("'[")
    for i in range(10):
        data_command = data_command.add_arg(f"{{'id': {i}, 'value': {i*10}, 'name': 'item_{i}'}}")
        if i < 9:
            data_command = data_command.add_arg(",")
    data_command = data_command.add_arg("]'")
    
    # Execute command with DATAFRAME format
    result = data_command.with_data_format(DataFormat.DATAFRAME).execute(context)
    df = result.structured_output
    
    print("Input data:")
    print(df)
    
    print("\nData analysis using pandas:")
    print(f"Mean value: {df['value'].mean()}")
    print(f"Maximum value: {df['value'].max()}")
    print(f"Sum of all values: {df['value'].sum()}")
    
    print("\nFiltering data:")
    filtered = df[df['value'] > 50]
    print(filtered)
    
    print("\nGrouping data:")
    grouped = df.groupby(df['id'] % 2 == 0).agg({'value': ['sum', 'mean', 'count']})
    print(grouped)
    
    # Display history summary
    print("\nExecution history summary:")
    display_history_summary(result)
    
if __name__ == "__main__":
    main() 