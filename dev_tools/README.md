# Mancer Development Tools

This directory contains helper tools for working with the Mancer project in development mode.

## Universal Development Tool

For a simpler experience, you can use the all-in-one development tool:

```bash
./dev_tools/mancer_tools.sh
```

This interactive script provides a menu-based interface for all development tasks:
- Installing/uninstalling the development environment
- Running the application
- Running different types of tests with various options
- Building distribution packages
- Checking and updating the version

It combines all the functionality of individual scripts described below in a user-friendly interface.

### Command Line Parameters

The script can also be used in non-interactive mode with command line parameters:

```bash
# Display help
./dev_tools/mancer_tools.sh --help

# Install development environment
./dev_tools/mancer_tools.sh --install

# Run application
./dev_tools/mancer_tools.sh --run

# Run tests (with options)
./dev_tools/mancer_tools.sh --test unit --verbose --coverage

# Build package
./dev_tools/mancer_tools.sh --build wheel --install

# Uninstall environment (force mode)
./dev_tools/mancer_tools.sh --uninstall --force

# Display version
./dev_tools/mancer_tools.sh --version
```

Available options:
- `-h, --help` - Display help
- `-i, --install` - Install development environment
- `-r, --run` - Run Mancer application
- `-t, --test [type]` - Run tests (all, unit, integration, privileged)
- `-b, --build [format]` - Build package (all, wheel, sdist)
- `-u, --uninstall` - Uninstall development environment
- `-v, --version` - Display current Mancer version
- `-f, --force` - Force operations without asking

## Development Environment Installation

To install the project in development mode, run:

```bash
./tools/install_dev.py
```

This script:
1. Automatically increments the version number in `setup.py` file (Z part in X.Y.Z format)
2. Creates a Python virtual environment in the `.venv` directory (if it doesn't exist yet)
3. Installs all dependencies from the `requirements.txt` file
4. Installs the Mancer package in development mode (`pip install -e .`)
5. Asks if you want to automatically activate the virtual environment in a new terminal

Options:
- `--force` or `-f` - skips prompts and forces installation
- `--activate` or `-a` - automatically activates the environment after installation

## Running the Application

To run the application in the development environment, use:

```bash
./tools/run_dev.py
```

This script:
1. Automatically detects if you are in a virtual environment
2. If not, activates the environment and reruns itself
3. Runs the Mancer application from the current development version

## Running Tests

To run the framework tests, use:

```bash
./tools/run_tests.py
```

This script:
1. Automatically detects if you are in a virtual environment
2. Installs required test dependencies (pytest, coverage, etc.)
3. Runs tests according to the options provided

Options:
- `--type {all,unit,integration,privileged}` - specifies the type of tests to run
- `-v, --verbose` - detailed display of test results
- `-p [N], --parallel [N]` - runs tests in parallel (N processes, default: number of cores)
- `-c, --coverage` - generates code coverage report
- `--html` - generates code coverage report in HTML format
- `-f, --force` - forces operations without prompting

Examples:
```bash
# Run all tests
./tools/run_tests.py

# Run only unit tests with code coverage measurement
./tools/run_tests.py --type unit --coverage

# Run integration tests in verbose mode
./tools/run_tests.py --type integration -v

# Run tests in parallel with HTML coverage report
./tools/run_tests.py -p -c --html
```

## Building the Package

To build a distribution package, use:

```bash
./tools/build_package.py
```

This script:
1. Automatically detects if you are in a virtual environment
2. Installs required build dependencies (wheel, setuptools, build, twine)
3. Cleans temporary directories (build, dist, *.egg-info)
4. Builds the package in wheel and source distribution formats
5. Checks the package for PyPI compatibility
6. Optionally installs the built package locally

Options:
- `--wheel` - builds only the wheel format package (.whl)
- `--sdist` - builds only the source distribution format package (.tar.gz)
- `-i, --install` - installs the built package locally
- `-f, --force` - forces operations without prompting
- `--no-clean` - doesn't clean directories before building

Examples:
```bash
# Build package in all formats
./tools/build_package.py

# Build and install wheel package
./tools/build_package.py --wheel --install

# Build package without cleaning directories
./tools/build_package.py --no-clean
```

## Uninstalling the Development Environment

If you want to remove the development environment, you can use:

```bash
./tools/uninstall_dev.py
```

This script:
1. Checks if you're not currently in a virtual environment
2. If you are, asks for manual deactivation (command `deactivate`)
3. Asks for confirmation before removal (can be skipped with the `--force` flag)
4. Removes the virtual environment directory `.venv`
5. Removes installation files (`.egg-info`, `__pycache__`, `.pyc` files)
6. Removes `build` and `dist` directories if they exist

⚠️ **Important:** Before running the script, make sure the virtual environment is not active.
If you see `(.venv)` at the beginning of the command prompt, type `deactivate` before running the script.

If after executing `deactivate` the script still detects an active environment, use the `--ignore-venv` flag:

```bash
./tools/uninstall_dev.py --ignore-venv
```

Your source code and project files will remain intact.

## Tips

- Scripts work on both Linux/macOS and Windows systems
- Every time you run `install_dev.py`, the application version is automatically incremented
- Scripts automatically manage the virtual environment, activating it when needed
- Use the `--force` or `-f` flag with any script to skip prompts and confirmations
- Use `install_dev.py --activate` to automatically activate the environment after installation
- For tests, you can use `run_tests.py` with various options, tailoring to your needs
- Use `build_package.py --install` to build and immediately install the package
- If you have problems deactivating the environment, use `uninstall_dev.py --ignore-venv`
- To deactivate the environment, always use the `deactivate` command directly in the terminal

## Troubleshooting

If you encounter problems:

1. Make sure you have Python 3.8 or newer installed
2. Check if you have write permissions in the project directory
3. If you have problems with dependencies, check the `requirements.txt` file
4. If after executing `deactivate` the script still detects the environment:
   - Run a new terminal without activating the environment
   - Use the `--ignore-venv` flag to force removal
5. Always use activation/deactivation commands directly in the terminal:
   - Activation: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
   - Deactivation: `deactivate` (all systems)

For questions or issues, contact the author: kacperpaczos2024@proton.me

## DDD Architecture Visualization

The `visualize_ddd.sh` script generates a graphical representation of the Domain-Driven Design (DDD) architecture of the Mancer project, using the `tach` tool for dependency analysis and Graphviz for diagram creation.

### Requirements

- Python 3
- `tach` library (automatically installed by the script)
- Graphviz (`dot` command)

### Usage

```bash
./dev_tools/visualize_ddd.sh [options]
```

### Options

- `--output-dir PATH` - Output directory for files (default: ./diagrams)
- `--format FORMAT` - Output format (dot, png, svg, pdf) (default: png)
- `--detailed` - Generate detailed diagram
- `--help` - Show help

### Examples

```bash
# Generate standard diagram
./dev_tools/visualize_ddd.sh

# Generate detailed diagram
./dev_tools/visualize_ddd.sh --detailed

# Generate diagram in SVG format
./dev_tools/visualize_ddd.sh --format svg

# Generate diagram to a specific directory
./dev_tools/visualize_ddd.sh --output-dir ./ddd_arch
```

The generated diagram shows DDD layers, modules, and dependencies between them. When using the `--detailed` option, the diagram includes additional information about subdomains and more precise dependencies.

The script is interactive and will prompt for format and detail level if not specified as command-line arguments. 