#!/usr/bin/env python3
"""
Script to install dependencies for prototypes and install Mancer
framework in development mode.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def create_venv(venv_path):
    """Create a virtual environment at the given path."""
    if os.path.exists(venv_path):
        print(f"Virtual environment already exists at {venv_path}")
        return True

    try:
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True, capture_output=True)
        print(f"Created virtual environment at {venv_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        print(f"Stdout: {e.stdout.decode() if e.stdout else ''}")
        print(f"Stderr: {e.stderr.decode() if e.stderr else ''}")
        return False


def install_dependencies(venv_path, requirements_file=None, dev_mode=True):
    """Install dependencies in the virtual environment."""
    activate_script = os.path.join(venv_path, "bin", "activate")

    if not os.path.exists(activate_script):
        print(f"Error: Activate script not found at {venv_path}")
        return False

    try:
        # Install dependencies from requirements file
        if requirements_file and os.path.exists(requirements_file):
            print(f"Installing dependencies from {requirements_file}...")

            cmd = f"source {activate_script} && pip install -r {requirements_file}"
            result = subprocess.run(cmd, shell=True, executable="/bin/bash")

            if result.returncode != 0:
                print(f"Error installing dependencies from {requirements_file}")
                return False

            print(f"Installed dependencies from {requirements_file}")

        # Install Mancer in development mode
        if dev_mode:
            print("Installing Mancer in development mode...")

            # Get path to main workspace directory (where setup.py is located)
            workspace_dir = Path(os.getcwd())

            cmd = f"source {activate_script} && pip install -e {workspace_dir}"
            result = subprocess.run(cmd, shell=True, executable="/bin/bash")

            if result.returncode != 0:
                print("Error installing Mancer in development mode")
                return False

            print("Installed Mancer in development mode")

        return True

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def setup_prototype(prototype_dir, force=False):
    """Set up a prototype with its own virtual environment and dependencies."""
    if not os.path.isdir(prototype_dir):
        print(f"Error: Directory {prototype_dir} does not exist")
        return False

    prototype_name = os.path.basename(prototype_dir)
    print(f"\nConfiguring prototype: {prototype_name}")
    print("-" * 50)

    # Create virtual environment
    venv_path = os.path.join(prototype_dir, ".venv")

    if os.path.exists(venv_path) and force:
        import shutil

        print(f"Removing existing virtual environment at {venv_path}")
        shutil.rmtree(venv_path)

    if not create_venv(venv_path):
        return False

    # Check for requirements.txt in prototype directory
    requirements_file = os.path.join(prototype_dir, "requirements.txt")
    if not os.path.exists(requirements_file):
        print(f"Warning: requirements.txt not found in {prototype_dir}")
        # Check for requirements.txt in workspace
        workspace_requirements = os.path.join(os.getcwd(), "requirements.txt")
        if os.path.exists(workspace_requirements):
            print("Using requirements.txt from main project directory")
            requirements_file = workspace_requirements
        else:
            requirements_file = None

    # Install dependencies
    result = install_dependencies(venv_path, requirements_file)

    if result:
        print(f"Prototype {prototype_name} configured successfully!")
    else:
        print(f"Errors occurred while configuring prototype {prototype_name}")

    return result


def main():
    """Main function to set up prototype environments."""
    parser = argparse.ArgumentParser(description="Install dependencies for prototypes")
    parser.add_argument("prototype", nargs="?", help="Prototype directory name to configure")
    parser.add_argument("--all", action="store_true", help="Configure all prototypes")
    parser.add_argument("--force", action="store_true", help="Force recreation of virtual environment")
    args = parser.parse_args()

    workspace_dir = Path(os.getcwd())
    prototypes_dir = workspace_dir / "prototypes"

    if not prototypes_dir.exists():
        print("Error: Prototypes directory does not exist!")
        return 1

    if args.prototype:
        # Set up a specific prototype
        prototype_path = prototypes_dir / args.prototype
        if not prototype_path.exists():
            print(f"Error: Prototype {args.prototype} does not exist")
            return 1

        if setup_prototype(prototype_path, args.force):
            print(f"\nPrototype {args.prototype} configured successfully!")
        else:
            print(f"\nErrors occurred while configuring prototype {args.prototype}")

    elif args.all:
        # Set up all prototypes
        success_count = 0
        failure_count = 0

        for prototype_dir in prototypes_dir.iterdir():
            if prototype_dir.is_dir():
                if setup_prototype(prototype_dir, args.force):
                    success_count += 1
                else:
                    failure_count += 1

        print(f"\nSummary: {success_count} prototypes configured successfully, " f"{failure_count} with errors")

    else:
        # List available prototypes
        print("Available prototypes:")
        for prototype_dir in prototypes_dir.iterdir():
            if prototype_dir.is_dir():
                print(f"  - {prototype_dir.name}")

        print("\nUsage: install_prototype_deps.py <prototype_name> or --all " "to configure all prototypes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
