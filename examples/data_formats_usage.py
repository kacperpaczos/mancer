#!/usr/bin/env python3
"""
Example of using Polars DataFrame format and transformations in command chains.
This example demonstrates:
1. Executing commands with Polars DataFrame format
2. Transforming DataFrames with map_df
3. Chaining commands with structural data processing
"""

import os
import sys

import polars as pl

# Add mancer module path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.model.data_format import DataFormat
from src.mancer.infrastructure.command.system.ls_command import LsCommand
from src.mancer.infrastructure.command.system.ps_command import PsCommand


def print_separator():
    print("\n" + "=" * 60 + "\n")


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
    print("=== Example 1: Using Polars DataFrame Format ===")
    print_separator()

    # POLARS format (default)
    print("POLARS Format (default):")
    ls_command = LsCommand().with_option("-la")
    result_polars = ls_command.execute(context)
    print(f"Data type: {type(result_polars.structured_output)}")
    print(f"Data format: {result_polars.data_format}")
    print("DataFrame schema:")
    print(result_polars.structured_output.schema)
    print("\nFirst 3 rows:")
    print(result_polars.structured_output.head(3))

    # Display history summary
    print("\nExecution history summary:")
    display_history_summary(result_polars)

    print_separator()

    # JSON format conversion
    print("Converting to JSON Format:")
    json_converted = result_polars.to_format(DataFormat.JSON)
    print(f"Converted data type: {type(json_converted.structured_output)}")
    print(f"Converted data format: {json_converted.data_format}")
    print(f"JSON snippet: {json_converted.structured_output[:100]}...")

    # Display history summary
    print("\nConversion history summary:")
    display_history_summary(json_converted)

    print_separator()
    print("=== Example 2: DataFrame Transformations with map_df ===")
    print_separator()

    print("Filtering ls results to show only directories (fluent methods):")
    # Create a chain with fluent DataFrame transformations
    chain = (LsCommand().with_option("-la")
             .filter(pl.col("is_directory") == True)  # Filter directories
             .head(3)  # Take only first 3
             .select(["filename", "size", "permissions"]))  # Select specific columns

    result_chain = chain.execute(context)

    print("Transformed DataFrame:")
    print(result_chain.structured_output)
    print(f"Shape: {result_chain.structured_output.shape}")

    print_separator()
    print("=== Example 3a: Direct CommandResult transformations ===")
    print_separator()

    print("Transform CommandResult directly:")
    result = LsCommand().with_option("-la").execute(context)

    # Transform the result directly
    filtered = (result
                .filter(pl.col("size") > 1000)  # Files larger than 1KB
                .sort("size", descending=True)   # Sort by size descending
                .head(3))                        # Take top 3

    print("Top 3 largest files:")
    print(filtered.structured_output)

    # Display history summary
    print("\nChain execution history summary:")
    display_history_summary(result_chain)

    print_separator()
    print("=== Example 4: Advanced Data Analysis ===")
    print_separator()

    print("Group processes by user and count:")
    ps_result = PsCommand().execute(context)

    # Group by user and count processes
    user_stats = (ps_result
                  .group_by("USER", pl.len().alias("process_count"))
                  .sort("process_count", descending=True)
                  .head(5))

    print("Top users by process count:")
    print(user_stats.structured_output)

    print_separator()
    print("=== Example 5: Command Chaining with Structural Processing ===")
    print_separator()

    print("LS -> Filter Python files -> Grep for 'test':")
    # Chain commands with structural processing - fluent + pipe
    from src.mancer.infrastructure.command.system.grep_command import GrepCommand

    chain2 = (LsCommand().with_option("-la")
              .filter(pl.col("filename").str.contains("\\.py$"))  # Filter Python files
              .select(["filename", "size"])  # Select relevant columns
              .pipe(GrepCommand("test")))  # Pipe to grep for pattern matching

    result_chain2 = chain2.execute(context)

    print("Final result (grep matches):")
    print(result_chain2.structured_output)

    # Display history summary
    print("\nChain execution history summary:")
    display_history_summary(result_chain2)

    print_separator()
    print("=== Example 4: Data Analysis Using Polars ===")
    print_separator()

    print("Data analysis using fluent methods:")
    ps_result = PsCommand().execute(context)

    print("Process count by user (using fluent methods):")
    user_counts = (ps_result
                   .group_by("USER", pl.len().alias("count"))
                   .sort("count", descending=True)
                   .head(5))
    print(user_counts.structured_output)

    print("\nMemory usage statistics (using fluent methods):")
    if "RSS" in ps_result.as_polars().columns:
        rss_stats = (ps_result
                     .select([pl.col("RSS").min().alias("min_rss"),
                              pl.col("RSS").max().alias("max_rss"),
                              pl.col("RSS").mean().alias("avg_rss"),
                              pl.col("RSS").median().alias("median_rss")]))
        print(rss_stats.structured_output)

    print_separator()
    print("=== Example 6: Advanced Filtering Language ===")
    print_separator()

    print("Safe mathematical operations and advanced filtering:")
    ls_result = LsCommand().with_option("-la").execute(context)

    # Safe mathematical operations
    result = (ls_result
              .safe_add_columns("size", "size", "double_size")  # size * 2
              .safe_divide_columns("double_size", "size", "ratio")  # Should be 2.0
              .filter_numeric_range("size", 1000, 10000)  # Files 1KB-10KB
              .filter_string_pattern("filename", r"\.(txt|md)$", case_insensitive=True)  # Text files
              .head(3))

    print("Filtered text files (1KB-10KB):")
    print(result.structured_output)

    print("\nMatrix operations:")
    matrix_result = (ls_result
                     .slice_rows(0, 10, 2)  # Every other row
                     .slice_columns(["filename", "size"])  # Select columns
                     .head(3))

    print("Matrix slice result:")
    print(matrix_result.structured_output)

    print_separator()
    print("=== Example 7: Data Extraction and Inspection ===")
    print_separator()

    print("Data inspection methods:")
    result = LsCommand().with_option("-la").execute(context)

    print(f"DataFrame shape: {result.get_shape()}")
    print(f"Column names: {result.get_headers()}")
    print(f"First row: {result.get_row(0)}")

    # Extract specific rows
    first_three = result.get_rows([0, 1, 2])
    print("First 3 rows:")
    print(first_three.structured_output)

    print_separator()
    print("=== Example 8: Data Cleaning ===")
    print_separator()

    print("Data cleaning operations:")
    # Create sample data with duplicates and nulls
    from mancer.infrastructure.command.custom.custom_command import CustomCommand

    # Simulate data with issues
    data_cmd = CustomCommand("echo").add_arg("'[")
    data_cmd = data_cmd.add_arg('{"name": "Alice", "age": 25},')
    data_cmd = data_cmd.add_arg('{"name": "Bob", "age": 30},')
    data_cmd = data_cmd.add_arg('{"name": "Alice", "age": 25},')  # duplicate
    data_cmd = data_cmd.add_arg('{"name": "Charlie", "age": null}')  # null
    data_cmd = data_cmd.add_arg("]'")

    try:
        data_result = data_cmd.execute(context)

        print("Original data:")
        print(data_result.structured_output)

        # Clean the data
        cleaned = (data_result
                  .drop_duplicates()  # Remove duplicates
                  .fill_nulls(0, columns=["age"]))  # Fill nulls

        print("After cleaning:")
        print(cleaned.structured_output)

    except Exception as e:
        print(f"Data cleaning example skipped: {e}")

    print_separator()
    print("=== Example 9: Statistical Analysis ===")
    print_separator()

    print("Statistical operations:")
    ls_result = LsCommand().with_option("-la").execute(context)

    # Add some numeric data for demo
    with_numbers = ls_result.add_columns("size", "size", "double_size")

    print("Descriptive statistics:")
    stats = with_numbers.describe()
    print(stats.structured_output)

    print("Value counts for file types:")
    # This would work better with actual file data
    try:
        counts = ls_result.value_counts("permissions")
        print(counts.structured_output)
    except Exception as e:
        print(f"Value counts example: {e}")

    print_separator()
    print("=== Example 10: String Operations ===")
    print_separator()

    print("String manipulation:")
    ls_result = LsCommand().with_option("-la").execute(context)

    print("Original filenames:")
    print(ls_result.structured_output["filename"].head(3))

    # Convert to uppercase
    upper = ls_result.str_upper("filename")
    print("Uppercase:")
    print(upper.structured_output["filename"].head(3))

    # Check for patterns
    pattern_check = ls_result.str_contains("filename", ".txt", "is_text")
    print("Text file check:")
    print(pattern_check.structured_output[["filename", "is_text"]].head(3))

    # Display history summary
    print("\nAnalysis history summary:")
    display_history_summary(ps_result)


if __name__ == "__main__":
    main()
