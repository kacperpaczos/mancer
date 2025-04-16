#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
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

def install_test_requirements():
    """
    Installs dependencies needed for tests if they are not already installed
    """
    print("Checking and installing test requirements...")
    try:
        # Install pytest and other testing tools
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest>=7.0.0", 
            "pytest-cov>=4.0.0", 
            "pytest-xdist>=3.0.0", 
            "pytest-mock>=3.8.0"
        ], check=True)
        
        print("Test requirements successfully installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing test requirements: {e}")
        return False

def run_tests(args):
    """
    Runs tests according to the provided arguments
    """
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Verbose mode
    if args.verbose:
        cmd.append("-v")
    
    # Parallel test execution
    if args.parallel:
        workers = args.parallel
        if workers == 0:  # Automatically use the number of available cores
            import multiprocessing
            workers = multiprocessing.cpu_count()
        cmd.extend(["-n", str(workers)])
    
    # Generate code coverage report
    if args.coverage:
        cmd.extend(["--cov=src/mancer", "--cov-report=term"])
        if args.coverage_html:
            cmd.append("--cov-report=html")
    
    # Select specific tests
    if args.test_type == "unit":
        cmd.append("tests/unit")
    elif args.test_type == "integration":
        cmd.append("-m")
        cmd.append("integration")
    elif args.test_type == "privileged":
        cmd.append("-m")
        cmd.append("privileged")
    
    # Additional arguments passed directly to pytest
    if args.pytest_args:
        cmd.extend(args.pytest_args)
    
    # Run tests
    print(f"Running tests: {' '.join(cmd)}")
    try:
        process = subprocess.run(cmd, check=False)
        return process.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Mancer framework testing tool")
    
    # Test type
    parser.add_argument("--type", dest="test_type", choices=["all", "unit", "integration", "privileged"],
                        default="all", help="Type of tests to run (default: all)")
    
    # Verbose mode
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display detailed test information")
    
    # Parallel tests
    parser.add_argument("-p", "--parallel", type=int, metavar="N", nargs="?", const=0,
                        help="Run tests in parallel (N = number of processes, default: number of cores)")
    
    # Code coverage
    parser.add_argument("-c", "--coverage", action="store_true",
                        help="Generate code coverage report")
    
    parser.add_argument("--html", dest="coverage_html", action="store_true",
                        help="Generate HTML code coverage report")
    
    # Force
    parser.add_argument("-f", "--force", action="store_true",
                        help="Force operations without asking")
    
    # Additional arguments for pytest
    parser.add_argument("pytest_args", nargs="*",
                        help="Additional arguments passed directly to pytest")
    
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
            answer = input("Do you want me to activate the virtual environment and run tests? (yes/no): ").lower()
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
    
    # We are in a virtual environment, install test requirements
    if not install_test_requirements():
        print("Error: Failed to install test requirements")
        return 1
    
    # Run tests
    return run_tests(args)

if __name__ == "__main__":
    sys.exit(main()) 