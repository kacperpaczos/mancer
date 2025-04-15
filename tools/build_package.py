#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path

def activate_venv():
    """
    Checks if we are in a virtual environment, if not - tries to activate it
    """
    # Check if we are already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Already in virtual environment")
        return True
    
    # Define the path to venv activation
    if sys.platform == 'win32':
        activate_script = '.venv\\Scripts\\activate'
        py_cmd = ['.venv\\Scripts\\python']
    else:
        activate_script = '.venv/bin/activate'
        py_cmd = ['.venv/bin/python']
    
    if not os.path.exists(activate_script):
        print(f"Error: Could not find virtual environment activation script: {activate_script}")
        print("Is the development environment installed? Run tools/install_dev.py first")
        return False
    
    # Run the same script in the virtual environment
    try:
        print("Activating virtual environment and rerunning...")
        script_path = os.path.abspath(__file__)
        
        # Pass all arguments to the new script instance
        script_args = ' '.join(sys.argv[1:])
        
        if sys.platform == 'win32':
            activate_cmd = f"call {activate_script} && python {script_path} {script_args}"
            subprocess.run(["cmd", "/c", activate_cmd], check=True)
        else:
            activate_cmd = f"source {activate_script} && python {script_path} {script_args}"
            subprocess.run(["bash", "-c", activate_cmd], check=True)
        
        # If we got here, the script was run in venv, so we can end this instance
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Error activating virtual environment: {e}")
        return False

def install_build_requirements():
    """
    Installs dependencies needed to build the package
    """
    print("Installing package building tools...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "wheel", "setuptools", "build", "twine"
        ], check=True)
        
        print("Build tools successfully installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing build tools: {e}")
        return False

def clean_directories():
    """
    Cleans build, dist and *.egg-info directories
    """
    print("Cleaning temporary directories...")
    
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"Removing directory {dir_name}")
            shutil.rmtree(dir_name)
    
    # Remove all *.egg-info directories
    for egg_info in Path('.').glob('**/*.egg-info'):
        if egg_info.is_dir():
            print(f"Removing directory {egg_info}")
            shutil.rmtree(egg_info)
    
    return True

def build_package(args):
    """
    Builds the Python package
    """
    print("Building package...")
    
    try:
        # Build distribution packages
        build_cmd = [sys.executable, "-m", "build"]
        
        if args.wheel_only:
            build_cmd.append("--wheel")
        elif args.sdist_only:
            build_cmd.append("--sdist")
        
        subprocess.run(build_cmd, check=True)
        
        print("Package built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building package: {e}")
        return False

def check_package():
    """
    Checks the built package using twine
    """
    print("Checking built package...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "twine", "check", "dist/*"
        ], check=True)
        
        print("Package validation completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error checking package: {e}")
        return False

def install_locally(args):
    """
    Installs the built package locally (optional)
    """
    if not args.install:
        return True
        
    print("Installing package locally...")
    
    try:
        # Find the latest wheel file in the dist directory
        wheels = list(Path('dist').glob('*.whl'))
        if not wheels:
            print("No wheel file found in dist directory")
            return False
        
        # Sort by modification time (newest last)
        wheels.sort(key=lambda p: p.stat().st_mtime)
        latest_wheel = wheels[-1]
        
        # Install wheel
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--force-reinstall", str(latest_wheel)
        ], check=True)
        
        print(f"Package {latest_wheel.name} installed successfully")
        return True
    except Exception as e:
        print(f"Error installing package: {e}")
        return False

def show_publication_instructions():
    """
    Displays instructions on how to publish the package
    """
    print("\nTo publish the package to PyPI, run:")
    print("  python -m twine upload dist/*")
    print("\nTo publish the package to TestPyPI, run:")
    print("  python -m twine upload --repository testpypi dist/*")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Mancer package building tool")
    
    # Package format
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument("--wheel", dest="wheel_only", action="store_true",
                              help="Build wheel only (.whl file)")
    format_group.add_argument("--sdist", dest="sdist_only", action="store_true",
                              help="Build source distribution only (.tar.gz file)")
    
    # Installation options
    parser.add_argument("-i", "--install", action="store_true",
                        help="Install the built package locally")
    
    # Force
    parser.add_argument("-f", "--force", action="store_true",
                        help="Force operations without asking")
    
    # Skip directory cleaning
    parser.add_argument("--no-clean", dest="no_clean", action="store_true",
                        help="Don't clean directories before building")
    
    args = parser.parse_args()
    
    # Change to the project root directory
    os.chdir(Path(__file__).parent.parent)
    
    # Check if we are in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("Not in a virtual environment.")
        
        if args.force:
            print("Automatically activating virtual environment (forced mode)...")
            activate_venv()
            return 0  # activate_venv will end this process if successful
        
        while True:
            answer = input("Do you want me to activate the virtual environment and build the package? (yes/no): ").lower()
            if answer in ['yes', 'y']:
                activate_venv()
                return 0  # activate_venv will end this process if successful
            elif answer in ['no', 'n']:
                print("To manually activate the virtual environment, run:")
                if sys.platform == 'win32':
                    print("\t.venv\\Scripts\\activate")
                else:
                    print("\tsource .venv/bin/activate")
                return 1
            else:
                print("Please enter 'yes' or 'no'")
    
    # Install build requirements
    if not install_build_requirements():
        print("Error: Failed to install build requirements")
        return 1
    
    # Clean directories (unless user chooses --no-clean option)
    if not args.no_clean:
        if not clean_directories():
            print("Error: Failed to clean directories")
            return 1
    
    # Build package
    if not build_package(args):
        print("Error: Failed to build package")
        return 1
    
    # Check package
    if not check_package():
        print("Error: Package failed validation")
    
    # Local installation (if --install option is selected)
    if args.install and not install_locally(args):
        print("Error: Failed to install package locally")
        return 1
    
    # Display publication instructions
    show_publication_instructions()
    
    print("\nPackage building completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 