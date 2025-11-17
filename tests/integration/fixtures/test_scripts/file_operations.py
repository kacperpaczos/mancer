#!/usr/bin/env python3
"""
File operations script for integration testing.

This script performs various file operations to validate
filesystem access and manipulation in LXC containers.
"""

import json
import os
import sys
from pathlib import Path


def create_test_files(base_dir):
    """Create test files in the specified directory."""
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    files_created = []

    # Create sample text file
    text_file = base_path / "sample.txt"
    text_file.write_text("This is a test file.\nCreated by integration test.\n")
    files_created.append(str(text_file))

    # Create CSV file
    csv_file = base_path / "data.csv"
    csv_file.write_text("name,value,timestamp\nAlice,100,2024-01-01\nBob,200,2024-01-02\n")
    files_created.append(str(csv_file))

    # Create subdirectory with file
    subdir = base_path / "subdir"
    subdir.mkdir(exist_ok=True)
    nested_file = subdir / "nested.txt"
    nested_file.write_text("This is a nested file.\n")
    files_created.append(str(nested_file))

    return files_created


def read_and_process_files(base_dir):
    """Read and process files in the directory."""
    base_path = Path(base_dir)
    results = {}

    # Read text file
    text_file = base_path / "sample.txt"
    if text_file.exists():
        results["sample_content"] = text_file.read_text().strip()

    # Count files
    total_files = 0
    for root, dirs, files in os.walk(base_dir):
        total_files += len([f for f in files if not f.startswith(".")])

    results["total_files"] = str(total_files)
    results["directories"] = str(len([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]))

    return results


def main():
    """Main file operations function."""
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "Usage: script.py <operation> [directory]"}))
            sys.exit(1)

        operation = sys.argv[1]

        if operation == "create":
            if len(sys.argv) < 3:
                target_dir = "/tmp/integration_test"
            else:
                target_dir = sys.argv[2]

            files_created = create_test_files(target_dir)
            result = {
                "operation": "create",
                "target_directory": target_dir,
                "files_created": files_created,
                "success": True,
            }

        elif operation == "read":
            if len(sys.argv) < 3:
                target_dir = "/tmp/integration_test"
            else:
                target_dir = sys.argv[2]

            if not os.path.exists(target_dir):
                result = {"operation": "read", "error": f"Directory {target_dir} does not exist", "success": False}
            else:
                data = read_and_process_files(target_dir)
                result = {"operation": "read", "target_directory": target_dir, "data": data, "success": True}

        else:
            result = {"error": f"Unknown operation: {operation}", "success": False}

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({"error": f"File operation failed: {str(e)}", "success": False}))
        sys.exit(1)


if __name__ == "__main__":
    main()
