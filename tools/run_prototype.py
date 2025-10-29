#!/usr/bin/env python3
"""
Script to run prototypes in their own virtual environments.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def find_main_script(prototype_dir):
    """Find the main script in the prototype directory."""
    # Common main script patterns
    main_patterns = [
        "main.py",
        "__main__.py",
        f"{os.path.basename(prototype_dir)}.py",
        "app.py",
        "run.py",
        "start.py",
    ]

    # First, look for scripts that match common patterns
    for pattern in main_patterns:
        main_script = os.path.join(prototype_dir, pattern)
        if os.path.exists(main_script):
            return main_script

    # If no common pattern is found, look for any .py file that might be the main script
    py_files = [
        f for f in os.listdir(prototype_dir) if f.endswith(".py") and os.path.isfile(os.path.join(prototype_dir, f))
    ]

    if py_files:
        # If there's only one .py file, assume it's the main script
        if len(py_files) == 1:
            return os.path.join(prototype_dir, py_files[0])

        # Otherwise, return None and let the user specify
        return None

    return None


def run_prototype(prototype_dir, script_path=None, args=None):
    """Run a prototype in its own virtual environment."""
    if not os.path.isdir(prototype_dir):
        print(f"Error: Directory {prototype_dir} does not exist")
        return False

    prototype_name = os.path.basename(prototype_dir)
    print(f"\nRunning prototype: {prototype_name}")
    print("-" * 50)

    # Check for virtual environment
    venv_path = os.path.join(prototype_dir, ".venv")
    activate_script = os.path.join(venv_path, "bin", "activate")

    if not os.path.exists(activate_script):
        print(f"Error: Virtual environment not found at {venv_path}")
        print("First run install_prototype_deps.py to configure the environment")
        return False

    # Find the main script if not specified
    if not script_path:
        script_path = find_main_script(prototype_dir)

        if not script_path:
            print(f"Error: Main script not found in {prototype_dir}")
            print("Specify the script using the --script parameter")
            return False

    # Ensure script exists
    if not os.path.exists(script_path):
        print(f"Error: Script {script_path} does not exist")
        return False

    # Run the prototype
    try:
        # Prepare command
        args_str = " ".join(args) if args else ""
        script_name = os.path.basename(script_path)
        cmd = f"cd {prototype_dir} && source {activate_script} && " f"python {script_name} {args_str}"

        # Run the command
        print(f"Executing: {os.path.basename(script_path)} {args_str}")
        proc = subprocess.run(cmd, shell=True, executable="/bin/bash")

        return proc.returncode == 0

    except Exception as e:
        print(f"An error occurred while running the prototype: {str(e)}")
        return False


def list_prototypes():
    """List all available prototypes."""
    workspace_dir = Path(os.getcwd())
    prototypes_dir = workspace_dir / "prototypes"

    if not prototypes_dir.exists():
        print("Error: Prototypes directory does not exist!")
        return []

    prototypes = []

    for prototype_dir in prototypes_dir.iterdir():
        if prototype_dir.is_dir():
            prototype_info = {
                "name": prototype_dir.name,
                "path": str(prototype_dir),
                "has_venv": (prototype_dir / ".venv").exists(),
                "main_script": find_main_script(prototype_dir),
            }
            prototypes.append(prototype_info)

    return prototypes


def main():
    """Main function to run a prototype."""
    parser = argparse.ArgumentParser(description="Run a prototype in its own virtual environment")
    parser.add_argument("prototype", nargs="?", help="Name of the prototype to run")
    parser.add_argument("--list", action="store_true", help="Display list of available prototypes")
    parser.add_argument("--script", help="Path to the main script (default: main.py)")
    parser.add_argument("prototype_args", nargs="*", help="Arguments to pass to the prototype")
    args = parser.parse_args()

    if args.list or not args.prototype:
        prototypes = list_prototypes()

        if not prototypes:
            print("No prototypes found")
            return 1

        print("\nAvailable prototypes:")
        print("-" * 50)

        for p in prototypes:
            venv_status = "✓" if p["has_venv"] else "✗"
            main_script = os.path.basename(p["main_script"]) if p["main_script"] else "Not found"

            print(f"{p['name']:20} | Environment: {venv_status} | Main script: {main_script}")

        if not args.prototype:
            print("\nUsage: run_prototype.py <prototype_name> to run a prototype")
            return 0

    # Get prototype directory
    workspace_dir = Path(os.getcwd())
    prototype_dir = workspace_dir / "prototypes" / args.prototype

    # Determine script path
    script_path = None
    if args.script:
        # User specified a script path
        if os.path.isabs(args.script):
            script_path = args.script
        else:
            script_path = os.path.join(prototype_dir, args.script)

    # Run the prototype
    if run_prototype(prototype_dir, script_path, args.prototype_args):
        print(f"\nPrototype {args.prototype} completed successfully")
        return 0
    else:
        print(f"\nErrors occurred while running prototype {args.prototype}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
