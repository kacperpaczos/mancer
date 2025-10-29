#!/usr/bin/env python3
"""
Script to check Mancer versions installed in prototype environments.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_environment(env_path, prototype_name):
    """Check Mancer version in a given environment."""
    activate_script = os.path.join(env_path, "bin", "activate")

    if not os.path.exists(activate_script):
        return {
            "prototype": prototype_name,
            "status": "error",
            "error": "Activate script not found",
        }

    try:
        # Command to get Mancer version
        cmd = (
            f"source {activate_script} && python -c "
            f"\"import pkg_resources; print(pkg_resources.get_distribution('mancer').version)\""
        )

        # Run the command
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash")

        if result.returncode != 0:
            return {
                "prototype": prototype_name,
                "status": "error",
                "error": f"Mancer is not installed: {result.stderr.strip()}",
            }

        return {
            "prototype": prototype_name,
            "status": "success",
            "version": result.stdout.strip(),
        }

    except Exception as e:
        return {"prototype": prototype_name, "status": "error", "error": str(e)}


def main():
    """Main function to check all prototype environments."""
    workspace_dir = Path(os.getcwd())
    prototypes_dir = workspace_dir / "prototypes"

    if not prototypes_dir.exists():
        print("Error: Prototypes directory does not exist!")
        return 1

    results = []

    # Check main environment first
    main_venv = workspace_dir / ".venv"
    if main_venv.exists():
        main_result = check_environment(main_venv, "main")
        results.append(main_result)

    # Check all prototype environments
    for prototype_dir in prototypes_dir.iterdir():
        if prototype_dir.is_dir():
            prototype_name = prototype_dir.name
            venv_dir = prototype_dir / ".venv"

            if venv_dir.exists():
                result = check_environment(venv_dir, prototype_name)
                results.append(result)

    # Print results
    print(f"\nMancer versions in environments ({len(results)}):")
    print("-" * 50)

    # Get latest version from setup.py
    setup_path = workspace_dir / "setup.py"
    latest_version = "unknown"

    if setup_path.exists():
        with open(setup_path, "r") as f:
            for line in f:
                if "version" in line and "=" in line:
                    try:
                        latest_version = line.split("=")[1].strip().replace('"', "").replace("'", "").replace(",", "")
                        break
                    except Exception:
                        pass

    print(f"Latest Mancer version: {latest_version}\n")

    for result in results:
        prototype = result["prototype"]
        status = result["status"]

        if status == "success":
            version = result["version"]
            outdated = version != latest_version
            status_text = f"{version} {'(outdated)' if outdated else '(current)'}"
        else:
            status_text = f"ERROR: {result.get('error', 'Unknown error')}"

        print(f"Prototype: {prototype:20} - {status_text}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
