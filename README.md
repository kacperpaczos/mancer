# Mancer

A Domain-Driven Design (DDD) framework for system commands that enables version control of tools, local and remote command execution, and processing results in various formats.

> **WARNING**: Mancer is in early development stage (v0.1.0). The API and ABI are not stable and may change without notice in future releases. Use with caution in production environments.

## Installation

The framework can be installed in two ways:

### Quick Installation

```bash
pip uninstall -y mancer
pip install -e .
```

### Installation with Development Environment Setup

```bash
./tools/setup_dev.sh
```

This script:
- Checks system requirements
- Creates a Python virtual environment
- Installs all dependencies
- Configures directories and configuration files
- Sets up git hooks (optional)

## Project Structure

```
mancer/
├── examples/                 # Framework usage examples
├── src/                      # Source code
│   └── mancer/
│       ├── application/      # Application layer
│       ├── config/           # Configuration files
│       ├── domain/           # Domain layer
│       │   ├── interface/    # Interfaces
│       │   ├── model/        # Domain models
│       │   └── service/      # Domain services
│       ├── infrastructure/   # Infrastructure layer
│       │   ├── backend/      # Execution backends
│       │   └── command/      # Command implementations
│       └── interface/        # Interface layer
├── tests/                    # Automated tests
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
└── tools/                    # Utility tools
```

## DDD Architecture Overview

Mancer implements a Domain-Driven Design architecture, organizing code into distinct layers with clear responsibilities. Here's a diagram showing the flow of control and key components:

```
                           ┌─────────────────────────────────────────────┐
                           │               USER CODE                     │
                           └───────────────┬─────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  INTERFACE LAYER                                        │
│                                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  ┌─────────────────────┐ │
│  │ CLI         │  │ API         │  │ CommandFactory          │  │ ResultFormatter     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  └─────────────────────┘ │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                APPLICATION LAYER                                        │
│                                                                                         │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │ CommandExecutor     │  │ CommandChain        │  │ VersionManager                  │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────────────────┘  │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  DOMAIN LAYER                                           │
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │ Models                                                                          │    │
│  │                                                                                 │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │    │
│  │  │ CommandContext  │  │ CommandResult   │  │ VersionInfo     │                  │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │ Interfaces                                                                      │    │
│  │                                                                                 │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │    │
│  │  │ ICommand        │  │ IExecutionBackend│  │ IResultParser   │                 │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │ Services                                                                        │    │
│  │                                                                                 │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │    │
│  │  │ VersionService  │  │ FormatService   │  │ CacheService    │                  │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 INFRASTRUCTURE LAYER                                    │
│                                                                                         │
│  ┌─────────────────────────────────────────────┐  ┌─────────────────────────────────┐   │
│  │ Command Implementations                     │  │ Execution Backends              │   │
│  │                                             │  │                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐           │  │  ┌─────────────┐ ┌────────────┐ │   │
│  │  │ BaseCommand │  │ SystemCommand│          │  │  │ LocalBackend│ │ SSHBackend │ │   │
│  │  └─────┬───────┘  └─────────────┘           │  │  └─────────────┘ └────────────┘ │   │
│  │        │                                    │  │                                 │   │
│  │        ▼                                    │  └─────────────────────────────────┘   │
│  │  ┌─────────────┐  ┌─────────────┐           │                                        │
│  │  │ DFCommand   │  │ LSCommand   │  ...      │  ┌─────────────────────────────────┐   │
│  │  └─────────────┘  └─────────────┘           │  │ Configuration                   │   │
│  │                                             │  │                                 │   │
│  └─────────────────────────────────────────────┘  │  ┌─────────────┐ ┌────────────┐ │   │
│                                                   │  │ ConfigLoader│ │VersionStore│ │   │
│                                                   │  └─────────────┘ └────────────┘ │   │
│                                                   └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Flow of Control

1. User code interacts with the Interface Layer
2. Interface Layer creates and configures commands
3. Application Layer orchestrates command execution
4. Domain Layer contains business logic and interfaces
5. Infrastructure Layer implements concrete commands, backends and external services

### Key Responsibilities by Layer

- **Interface Layer**: User-facing APIs, command factories, and result formatters
- **Application Layer**: Orchestration of command execution, command chaining, and version management
- **Domain Layer**:
  - **Models**: Core domain entities (CommandContext, CommandResult, VersionInfo)
  - **Interfaces**: Abstractions for commands, backends and parsers
  - **Services**: Domain-specific logic for versions, formatting, and caching
- **Infrastructure Layer**: Concrete implementations of commands, execution backends, and external services

## Available Tools

The framework provides several tools to facilitate work:

### Development Environment Setup Script

```bash
./tools/setup_dev.sh
```

### Running Tests

```bash
./tools/run_tests.sh              # All tests
./tools/run_tests.sh --unit       # Only unit tests
./tools/run_tests.sh --coverage   # With code coverage report
```

### Managing Tool Versions

```bash
./tools/update_versions.py list                # List all versions
./tools/update_versions.py list ls             # Versions for a specific tool
./tools/update_versions.py add grep 3.8        # Add a version manually
./tools/update_versions.py detect --all        # Detect and add all versions
./tools/update_versions.py detect ls grep      # Detect specific tools
./tools/update_versions.py remove df 2.34      # Remove a version
```

## Usage Examples

The `examples/` directory contains examples demonstrating various framework capabilities:

- `basic_usage.py` - Basic command usage
- `remote_usage.py` - Remote command execution via SSH
- `remote_sudo_usage.py` - Remote command execution with sudo
- `command_chains.py` - Chaining commands
- `data_formats_usage.py` - Working with different data formats
- `cache_usage.py` - Caching command results
- `version_checking.py` - Checking system tool versions

To run an example:

```bash
cd examples
python basic_usage.py
```

## Tool Versioning Mechanism

Mancer includes a unique system tool versioning mechanism that allows:

1. Defining allowed tool versions in configuration files
2. Automatically detecting tool versions in the system
3. Warning when a version is not on the whitelist
4. **Adapting command behavior based on the detected tool version** for backward compatibility

The configuration of allowed versions is located in the file `~/.mancer/tool_versions.yaml` or `src/mancer/config/tool_versions.yaml`.

### Version Compatibility Example

```python
from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.ls_command import LsCommand

# Create context
context = CommandContext()

# Execute ls command with version verification
ls_command = LsCommand().with_option("-la")
result = ls_command.execute(context)

# Check for version warnings
if result.metadata and "version_warnings" in result.metadata:
    print("Version warnings:")
    for warning in result.metadata["version_warnings"]:
        print(f"  - {warning}")
```

## Command Behavior Adaptation Based on Tool Versions

Mancer allows commands to automatically adapt their behavior based on the detected version of the underlying tool. This is particularly useful for handling changes in command output formats or options across different versions of system tools.

### How Version Adaptation Works

1. **Version Detection**: When a command is executed, it automatically checks the version of the tool it's using.
2. **Method Adaptation**: Based on the detected version, the command can use different parsing methods to handle output.
3. **Backward Compatibility**: This allows your code to work with different tool versions without requiring conditional logic.

### Implementing Version-Specific Behavior

To create a command with version-specific behavior:

1. Define a mapping between version patterns and method names:

```python
class MyVersionedCommand(BaseCommand):
    # Tool name for version checking
    tool_name = "my_tool"
    
    # Version adapters mapping 
    version_adapters = {
        "1.x": "_parse_output_v1",
        "2.x": "_parse_output_v2",
        "3.x": "_parse_output_v3"
    }
```

2. Implement version-specific methods for parsing or other behaviors:

```python
def _parse_output_v1(self, raw_output: str):
    # Parsing logic specific to version 1.x
    # ...

def _parse_output_v2(self, raw_output: str):
    # Enhanced parsing logic for version 2.x
    # ...
```

### Examples

See the following examples for practical implementations:

- `examples/df_command_example.py` - Shows how the `df` command adapts to different versions
- `examples/create_custom_command.py` - Demonstrates creating a custom command with version-specific behavior

## Configuration

The framework uses YAML configuration files:

- `tool_versions.yaml` - Allowed system tool versions
- `settings.yaml` - General framework settings

Configuration files are searched in the following order:
1. Current directory
2. `~/.mancer/`
3. `/etc/mancer/`
4. Package directory `src/mancer/config/`

## Creating Custom Commands

You can create custom commands by extending the `BaseCommand` class:

```python
from mancer.infrastructure.command.base_command import BaseCommand
from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult

class MyCustomCommand(BaseCommand):
    # Define tool name for version checking
    tool_name = "my_tool"
    
    def __init__(self):
        super().__init__("my-command")
        
    def execute(self, context: CommandContext, input_result=None) -> CommandResult:
        # Build command string
        command_str = self.build_command()
        
        # Get appropriate backend
        backend = self._get_backend(context)
        
        # Execute command
        exit_code, output, error = backend.execute(command_str)
        
        # Process result
        return self._prepare_result(
            raw_output=output,
            success=exit_code == 0,
            exit_code=exit_code,
            error_message=error,
            metadata={}
        )
        
    def _parse_output(self, raw_output: str):
        # Convert command output to structured data
        # ...
        return structured_data
```

### Command Usage Examples

There are several ways to use commands in the Mancer framework:

#### Basic Usage

```python
# Create command instance
from mancer.infrastructure.command.system.df_command import DfCommand
df_command = DfCommand()

# Create context
from mancer.domain.model.command_context import CommandContext
context = CommandContext()

# Execute command
result = df_command.execute(context)

# Access results
if result.success:
    print(f"Command succeeded with exit code: {result.exit_code}")
    print(f"Raw output: {result.raw_output}")
    print(f"Structured data: {result.structured_output}")
else:
    print(f"Command failed: {result.error_message}")
```

#### Method Chaining

Commands support method chaining for adding options and arguments:

```python
# Create and configure command using method chaining
ls_command = LsCommand().long_format().all_files().human_readable()

# Execute with context
result = ls_command.execute(context)
```

#### Pipeline Usage

Commands can be combined into pipelines:

```python
# Create a pipeline
from mancer.infrastructure.command.pipeline import CommandPipeline

pipeline = CommandPipeline()
pipeline.add_command(GrepCommand().with_pattern("error"))
pipeline.add_command(WcCommand().count_lines())

# Execute pipeline with input from a file
with open("logfile.txt", "r") as f:
    input_data = f.read()
    
context = CommandContext()
context.add_parameter("input_data", input_data)

# Run pipeline
result = pipeline.execute(context)
```

## Contributor Guide

If you'd like to contribute to the Mancer framework, here's how to get started:

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mancer.git
   cd mancer
   ```

2. Set up the development environment:
   ```bash
   ./tools/setup_dev.sh
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

### Development Workflow

1. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

3. **Run tests** to ensure everything works:
   ```bash
   ./tools/run_tests.sh
   ```

4. **Submit a pull request** with your changes.

### Code Style Guidelines

The project follows these coding standards:

- **Code Formatting**: We use Black for Python code formatting
- **Type Hints**: All functions should include type annotations
- **Documentation**: Use docstrings for all public classes and methods
- **Tests**: Write unit tests for new functionality

### Test Coverage

Before submitting a pull request, run the tests with coverage to ensure proper test coverage:

```bash
./tools/run_tests.sh --coverage
```

### Adding New Commands

When adding new system commands:

1. Create a new class in the appropriate directory under `src/mancer/infrastructure/command/`
2. Inherit from `BaseCommand` and implement required methods
3. Add version-specific parsing methods if needed
4. Create an example showing how to use the command
5. Add unit tests for the command

### Version Support

When adding version-specific behavior:

1. Document supported versions in the class docstring
2. Add version-specific methods using the naming convention `_parse_output_vX`
3. Update the `version_adapters` dictionary with version patterns

## License

This project is available under the [add your chosen license].

## New Logging System

Since version 0.2.0, Mancer includes a new, advanced logging system based on the Icecream library, which significantly simplifies debugging and monitoring commands.

### Main Features

- **Automatic Icecream detection** - if the Icecream library is available, the system uses it for log formatting; otherwise, it uses the standard Python logger
- **Hierarchical logging** - clearly organized logs at different levels (debug, info, warning, error, critical)
- **Pipeline tracking** - automatic logging of command input and output data in chains
- **Execution history** - complete history of executed commands with execution times and statuses
- **Command chain logging** - visualization of command chain structures
- **Support for multiple data formats** - structural formatting of command results

### Usage Example

```python
from src.mancer.infrastructure.logging.mancer_logger import MancerLogger
from src.mancer.domain.service.log_backend_interface import LogLevel

# Get singleton logger instance
logger = MancerLogger.get_instance()

# Configure logger
logger.initialize(
    log_level=LogLevel.DEBUG,   # Logging level
    console_enabled=True,       # Console logging
    file_enabled=True,          # File logging
    log_file="mancer.log"       # Log file name
)

# Logging at different levels
logger.debug("Detailed debugging information")
logger.info("Progress information")
logger.warning("Warning about a potential problem")
logger.error("Error during execution")

# Logging with context (additional data)
logger.info("Connecting to host", {
    "host": "example.com",
    "port": 22,
    "user": "admin"
})
```

### Advanced Features

The new logging system also supports advanced scenarios:

- **Command pipeline tracking**:
  ```python
  # Log input data
  logger.log_command_input("grep", input_data)
  
  # Log output data
  logger.log_command_output("grep", output_data)
  ```

- **Command history export**:
  ```python
  # Export history to JSON file
  history_file = logger.export_history()
  print(f"History exported to: {history_file}")
  ```

- **Command chain visualization**:
  ```python
  # Command chain will be automatically logged during execution
  chain = ls_command.pipe(grep_command).then(wc_command)
  result = chain.execute(context)
  ```

More detailed examples can be found in the `examples/new_logger_example.py` file.

### Backward Compatibility

The new system has been integrated with the existing logging mechanism without breaking backward compatibility. The old `CommandLoggerService` works as an adapter that internally uses the new `MancerLogger` when available.

## Development Lifecycle for Adding New Features

The complete development lifecycle in Mancer follows these steps:

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │     │                │
│  1. Planning   │────►│ 2. Development │────►│   3. Testing   │────►│  4. Versioning │
│                │     │                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
        │                                                                     │
        │                                                                     ▼
┌────────────────┐                                                   ┌────────────────┐
│                │                                                   │                │
│ 7. Maintenance │◄────────────────────────────────────────────────►│  5. Building   │
│                │                                                   │                │
└────────────────┘                                                   └────────────────┘
        ▲                                                                     │
        │                                                                     ▼
        │                                                             ┌────────────────┐
        │                                                             │                │
        └─────────────────────────────────────────────────────────────┤  6. Publishing │
                                                                      │                │
                                                                      └────────────────┘
```

### 1. Planning

- Define requirements for a new feature or command
- Document expected behavior
- Create Interfaces in `domain/interface/`
- Design the domain model in `domain/model/`

### 2. Development

- Implement the domain services in `domain/service/`
- Create concrete command implementations in `infrastructure/command/`
- Implement backend adapters if needed in `infrastructure/backend/`
- Add application services in `application/`
- Create examples in `examples/`

### 3. Testing

- Write unit tests in `tests/unit/`
- Add integration tests in `tests/integration/`
- Run tests with coverage:
  ```bash
  ./dev_tools/run_tests.py --coverage --html
  ```
- Fix any bugs found during testing

### 4. Versioning

- Update version number in `setup.py`
- For minor changes, `install_dev.py` will automatically increment the Z version
- For significant changes, manually update X or Y version
- Document version-specific behaviors if applicable

### 5. Building

- Build package distribution:
  ```bash
  ./dev_tools/build_package.py
  ```
- Test the built package locally:
  ```bash
  ./dev_tools/build_package.py --install
  ```

### 6. Publishing

- Publish to PyPI or internal repository
- Update documentation
- Create release notes

### 7. Maintenance

- Monitor for bug reports
- Implement version-specific adapters for backward compatibility
- Update tool version configurations