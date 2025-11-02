# Mancer

Mancer — Multisystem Programmable Engine

A domain-driven framework for programmable system automation: local bash and remote SSH, composable commands, structured results (JSON/DataFrame/ndarray), execution history, and version-aware behavior.

> **Status: Early-stage development version 0.1** - This is a pre-release version under active development. The API may evolve between releases. We appreciate feedback and contributions.

> **⚠️ Platform Support: Linux Only** - Mancer currently supports Linux systems only. Windows and macOS support is planned for future releases.

## Installation

### From PyPI (recommended)
```bash
pip install -U mancer
```

### From source
```bash
git clone https://github.com/Liberos-Systems/mancer.git
cd mancer
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## What is Mancer?
- Execute system commands locally (bash) or remotely (SSH) via a unified API
- Compose commands into pipelines and reusable building blocks
- Get structured results (JSON / pandas DataFrame / NumPy ndarray)
- Track execution history and metadata for auditing and analysis
- Adapt to tool versions with version‑aware behavior
- Extend with your own commands and backends

## Quickstart
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
cmd = runner.create_command("echo").text("hello mancer")
result = runner.execute(cmd)
print(result.raw_output)
```

## Examples
- Quick Examples: [User Guide Examples](docs/user-guide/examples.md)
- All Examples: [Examples Directory](docs/examples/all-examples.md)

## Documentation
- Getting Started: [Installation Guide](docs/getting-started/installation.md)
- User Guide: [Commands & Usage](docs/user-guide/commands.md)
- API Reference: [API Documentation](docs/api.md)
- Development: [Developer Guide](docs/development.md)

## How Mancer differs from Plumbum
Mancer is a domain-focused automation framework; Plumbum is a lightweight Pythonic shell toolbox. Both are valuable, but they serve different purposes.

- Domain model & history
  - Mancer: CommandResult with execution history/metadata for analysis and reporting
  - Plumbum: Emphasis on concise shell combinators and piping
- Data conversion
  - Mancer: Built-in converters to JSON/DataFrame/ndarray
  - Plumbum: Operates on stdio/strings; conversions left to user
- Version-aware behavior
  - Mancer: Detects tool versions and adapts parsing/behavior
  - Plumbum: No built-in tool version compatibility layer
- Extensibility via commands/backends
  - Mancer: Extensible command classes and execution backends
  - Plumbum: Focused on shell DSL and process primitives
- Orchestration and context
  - Mancer: Unified CommandContext (env, cwd, remote) and ShellRunner orchestration
  - Plumbum: Excellent primitives; orchestration remains in user code

See Plumbum: https://github.com/tomerfiliba/plumbum

## How Mancer differs from Fabric
Fabric is a Python library primarily focused on remote execution over SSH and task automation via `fab` tasks. Mancer is a domain-driven automation framework unifying local Bash and remote SSH with structured results and version-aware commands.

- Focus and model
  - Mancer: Domain model, structured `CommandResult`, execution history, composable commands and chains
  - Fabric: Task runner and SSH orchestration (fabfile tasks, run/sudo wrappers)
- Local vs remote
  - Mancer: Unified API for local Bash and remote SSH backends
  - Fabric: Strong focus on SSH (local execution available but not the primary model)
- Data handling
  - Mancer: Built-in adapters to JSON/DataFrame/ndarray for downstream processing
  - Fabric: Returns stdout/stderr; structuring data left to the user
- Version-aware behavior
  - Mancer: Detects tool versions and adapts parsing/behavior
  - Fabric: No built-in per-tool version compatibility layer

See Fabric: https://www.fabfile.org/

## Roadmap & Status
- Status: Early development version 0.1, API subject to change
- Planned: richer CLI, more system commands, more backends, Windows/PowerShell maturity, extended data adapters
- **Platform Support**: Linux (current), Windows and macOS (planned)

## Contributing
```bash
git clone https://github.com/Liberos-Systems/mancer.git
cd mancer
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest -q
```

## Versioning and Releases
- Semantic Versioning (pre‑1.0 semantics apply)
- Release notes in GitHub Releases

## License
MIT

## Links
- Repository: https://github.com/Liberos-Systems/mancer
- Issues: https://github.com/Liberos-Systems/mancer/issues
- Documentation: [docs/](docs/)

## Available Tools

The framework provides several tools to facilitate work:

### Development Environment Setup Script

```bash
./tools/mancer_tools.sh
```

### Running Tests

```bash
./scripts/run_tests.sh              # All tests
./scripts/run_tests.sh --unit       # Only unit tests
./scripts/run_tests.sh --coverage   # With code coverage report
```

### Managing Tool Versions

```bash
./tools/mancer_tools.sh --versions list                # List all versions
./tools/mancer_tools.sh --versions list ls             # Versions for a specific tool
./tools/mancer_tools.sh --versions add grep 3.8        # Add a version manually
./tools/mancer_tools.sh --versions detect --all        # Detect and add all versions
./tools/mancer_tools.sh --versions detect ls grep      # Detect specific tools
./tools/mancer_tools.sh --versions remove df 2.34      # Remove a version
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

## Core Classes: ShellRunner vs CommandManager

Mancer provides two main approaches for command execution:

### ShellRunner (Recommended for most users)
- **High-level interface** for quick command execution
- **Automatic context management** (working directory, environment variables)
- **Built-in remote execution** support via SSH
- **Simplified API** for common use cases

```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
result = runner.execute(runner.create_command("ls").long())
```

### CommandManager
- **Lower-level interface** for advanced command orchestration
- **Manual context management** for fine-grained control
- **Command chaining and pipelines** with explicit control
- **Advanced features** like execution history and caching

```python
from mancer.application.command_manager import CommandManager
from mancer.domain.model.command_context import CommandContext

manager = CommandManager()
context = CommandContext()
result = manager.execute_command("ls -la", context)
```

For most users, **ShellRunner** is the recommended starting point. Use **CommandManager** when you need advanced features or fine-grained control over command execution.

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

## New Logging System

Since version 0.1.0, Mancer includes an advanced logging system based on the Icecream library, which significantly simplifies debugging and monitoring commands.

### Main Features

- **Automatic Icecream detection** - if the Icecream library is available, the system uses it for log formatting; otherwise, it uses the standard Python logger
- **Hierarchical logging** - clearly organized logs at different levels (debug, info, warning, error, critical)
- **Pipeline tracking** - automatic logging of command input and output data in chains
- **Execution history** - complete history of executed commands with execution times and statuses
- **Command chain logging** - visualization of command chain structures
- **Support for multiple data formats** - structural formatting of command results

### Usage Example

```python
from mancer.infrastructure.logging.mancer_logger import MancerLogger
from mancer.domain.service.log_backend_interface import LogLevel

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

More detailed examples can be found in the `examples/new_logger_example.py` file.

## License

This project is available under the [MIT license](LICENSE).