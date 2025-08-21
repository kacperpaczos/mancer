#!/usr/bin/env python3
"""
Script to generate requirements.txt files for prototypes
based on imports in their source code.
"""

import argparse
import importlib.metadata
import os
import re
import subprocess
import sys
from pathlib import Path

# List of standard Python libraries
STANDARD_LIBS = set(
    [
        "abc",
        "argparse",
        "asyncio",
        "base64",
        "collections",
        "concurrent",
        "contextlib",
        "copy",
        "csv",
        "datetime",
        "decimal",
        "difflib",
        "enum",
        "functools",
        "getpass",
        "glob",
        "hashlib",
        "html",
        "http",
        "io",
        "itertools",
        "json",
        "logging",
        "math",
        "multiprocessing",
        "os",
        "pathlib",
        "pickle",
        "platform",
        "random",
        "re",
        "shutil",
        "signal",
        "socket",
        "sqlite3",
        "ssl",
        "statistics",
        "string",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
        "time",
        "traceback",
        "types",
        "typing",
        "urllib",
        "uuid",
        "warnings",
        "xml",
        "zipfile",
    ]
)


def find_imports(file_path):
    """Find all import statements in a Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern for import statements
    import_pattern = re.compile(r"^import\s+([a-zA-Z0-9_.]+)", re.MULTILINE)
    from_pattern = re.compile(r"^from\s+([a-zA-Z0-9_.]+)\s+import", re.MULTILINE)

    # Find all matches
    import_matches = import_pattern.findall(content)
    from_matches = from_pattern.findall(content)

    # Combine and extract top-level package names
    all_imports = set()
    for imp in import_matches + from_matches:
        # Get the top-level package name
        package = imp.split(".")[0]
        all_imports.add(package)

    # Remove standard library imports
    external_imports = all_imports - STANDARD_LIBS

    return external_imports


def find_python_files(directory):
    """Find all Python files in a directory recursively."""
    python_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    return python_files


def get_package_version(package_name):
    """Get the installed version of a package."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        # Try finding it with pip freeze
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"],
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.splitlines():
                if line.lower().startswith(package_name.lower() + "=="):
                    return line.split("==")[1]

            # If we can't find the version but the package exists
            # If we can't find it using pip freeze, try pip list
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list"],
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0].lower() == package_name.lower():
                    return parts[1]

            return None
        except subprocess.CalledProcessError:
            return None


def generate_requirements(prototype_dir):
    """Generate requirements.txt for a prototype."""
    if not os.path.isdir(prototype_dir):
        print(f"Error: Directory {prototype_dir} does not exist")
        return False

    prototype_name = os.path.basename(prototype_dir)
    print(f"\nGenerating requirements for prototype: {prototype_name}")
    print("-" * 50)

    # Find all Python files
    python_files = find_python_files(prototype_dir)

    if not python_files:
        print(f"No Python files found in {prototype_dir}")
        return False

    print(f"Found {len(python_files)} Python files")

    # Find all imports
    all_imports = set()
    for py_file in python_files:
        try:
            imports = find_imports(py_file)
            all_imports.update(imports)
        except Exception as e:
            print(f"Error analyzing {py_file}: {str(e)}")

    # Check if mancer is in imports and make sure it's included
    all_imports.add("mancer")

    if not all_imports:
        print("No external imports found")
        return False

    # Generate requirements.txt
    requirements_file = os.path.join(prototype_dir, "requirements.txt")

    with open(requirements_file, "w", encoding="utf-8") as f:
        f.write("# Automatically generated requirements for prototype\n")
        f.write("# Generated by make_requirements.py\n\n")

        # Add each package with its version
        for package in sorted(all_imports):
            version = get_package_version(package)
            if version:
                f.write(f"{package}=={version}\n")
            else:
                f.write(f"{package}\n")

    print(f"Found {len(all_imports)} external packages")
    print(f"Saved requirements file to {requirements_file}")

    return True


def main():
    """Main function to generate requirements.txt files."""
    parser = argparse.ArgumentParser(description="Generate requirements.txt for prototypes")
    parser.add_argument(
        "prototype",
        nargs="?",
        help="Name of the prototype to generate requirements for",
    )
    parser.add_argument(
        "--all", action="store_true", help="Generate requirements for all prototypes"
    )
    args = parser.parse_args()

    workspace_dir = Path(os.getcwd())
    prototypes_dir = workspace_dir / "prototypes"

    if not prototypes_dir.exists():
        print("Error: Prototypes directory does not exist!")
        return 1

    if args.prototype:
        # Generate requirements for a specific prototype
        prototype_path = prototypes_dir / args.prototype
        if not prototype_path.exists():
            print(f"Error: Prototype {args.prototype} does not exist")
            return 1

        if generate_requirements(prototype_path):
            print(f"\nRequirements for prototype {args.prototype} generated successfully!")
        else:
            print(f"\nErrors occurred while generating requirements for prototype {args.prototype}")

    elif args.all:
        # Generate requirements for all prototypes
        success_count = 0
        failure_count = 0

        for prototype_dir in prototypes_dir.iterdir():
            if prototype_dir.is_dir():
                if generate_requirements(prototype_dir):
                    success_count += 1
                else:
                    failure_count += 1

        print(
            f"\nSummary: {success_count} requirements files generated successfully, {failure_count} with errors"
        )

    else:
        # List available prototypes
        print("Available prototypes:")
        for prototype_dir in prototypes_dir.iterdir():
            if prototype_dir.is_dir():
                print(f"  - {prototype_dir.name}")

        print("\nUsage: make_requirements.py <prototype_name> or --all to generate requirements")

    return 0


if __name__ == "__main__":
    sys.exit(main())
