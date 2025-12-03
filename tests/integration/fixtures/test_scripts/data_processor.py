#!/usr/bin/env python3
"""
Data processing script for integration testing.

This script reads JSON data, processes it, and outputs results
to validate Python execution in LXC containers.
"""

import json
import sys
from pathlib import Path


def process_users(users_data):
    """Process user data and return statistics."""
    if not users_data:
        return {"error": "No users data provided"}

    total_users = len(users_data)
    avg_age = sum(user.get("age", 0) for user in users_data) / total_users

    return {"total_users": total_users, "average_age": round(avg_age, 2), "processed_at": "integration_test"}


def main():
    """Main processing function."""
    try:
        # Read input from stdin or file
        input_data = None

        if len(sys.argv) > 1:
            # Read from file
            input_file = Path(sys.argv[1])
            if input_file.exists():
                with open(input_file, "r") as f:
                    input_data = json.load(f)
        else:
            # Read from stdin
            input_data = json.load(sys.stdin)

        if not input_data:
            print(json.dumps({"error": "No input data"}))
            sys.exit(1)

        # Process users data
        if "test_users" in input_data:
            result = process_users(input_data["test_users"])
            print(json.dumps(result))
        else:
            print(json.dumps({"error": "No test_users data found"}))

    except Exception as e:
        print(json.dumps({"error": f"Processing failed: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
