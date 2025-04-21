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

## Nowy System Logowania

Od wersji 0.2.0 Mancer zawiera nowy, zaawansowany system logowania oparty na bibliotece Icecream, który znacznie ułatwia debugowanie i monitorowanie komend.

### Główne Cechy

- **Automatyczne wykrywanie Icecream** - jeśli biblioteka Icecream jest dostępna, system używa jej do formatowania logów, w przeciwnym razie używa standardowego loggera Pythona
- **Hierarchiczne logowanie** - jasno zorganizowane logi na różnych poziomach (debug, info, warning, error, critical)
- **Śledzenie pipeline'ów** - automatyczne logowanie danych wejściowych i wyjściowych komend w łańcuchach
- **Historia wykonania** - pełna historia wykonanych komend z czasami wykonania i statusami
- **Logowanie łańcuchów komend** - wizualizacja struktury łańcuchów komend
- **Wsparcie dla wielu formatów danych** - formatowanie strukturalne wyników komend

### Przykład Użycia

```python
from src.mancer.infrastructure.logging.mancer_logger import MancerLogger
from src.mancer.domain.service.log_backend_interface import LogLevel

# Pobierz singleton instancję loggera
logger = MancerLogger.get_instance()

# Skonfiguruj logger
logger.initialize(
    log_level=LogLevel.DEBUG,  # Poziom logowania
    console_enabled=True,      # Logowanie do konsoli
    file_enabled=True,         # Logowanie do pliku
    log_file="mancer.log"      # Nazwa pliku logu
)

# Logowanie na różnych poziomach
logger.debug("Szczegółowe informacje debugowania")
logger.info("Informacja o postępie")
logger.warning("Ostrzeżenie o potencjalnym problemie")
logger.error("Błąd podczas wykonania")

# Logowanie z kontekstem (dodatkowymi danymi)
logger.info("Połączenie z hostem", {
    "host": "example.com",
    "port": 22,
    "user": "admin"
})
```

### Zaawansowane Funkcje

Nowy system logowania obsługuje również zaawansowane scenariusze:

- **Śledzenie pipeline'ów komend**:
  ```python
  # Loguj dane wejściowe
  logger.log_command_input("grep", input_data)
  
  # Loguj dane wyjściowe
  logger.log_command_output("grep", output_data)
  ```

- **Eksport historii komend**:
  ```python
  # Eksportuj historię do pliku JSON
  history_file = logger.export_history()
  print(f"Historia wyeksportowana do: {history_file}")
  ```

- **Wizualizacja łańcucha komend**:
  ```python
  # Łańcuch komend będzie automatycznie logowany podczas wykonania
  chain = ls_command.pipe(grep_command).then(wc_command)
  result = chain.execute(context)
  ```

Bardziej szczegółowe przykłady znajdują się w pliku `examples/new_logger_example.py`.

### Kompatybilność Wsteczna

Nowy system został zintegrowany z istniejącym mechanizmem logowania bez naruszania kompatybilności wstecznej. Stary `CommandLoggerService` działa jako adapter, który wewnętrznie korzysta z nowego `MancerLogger` gdy jest dostępny.