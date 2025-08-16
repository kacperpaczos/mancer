# Core Concepts

## Command Abstraction
Mancer treats every system operation as a command object, making it easy to manage, log, and chain operations. Commands are represented by classes that inherit from `BaseCommand` and provide a consistent interface for execution.

## Command Chains
You can combine multiple commands into a single chain, allowing for complex workflows and automation. Command chains support piping, conditional execution, and result passing between commands.

## Backends
Mancer supports multiple execution backends:
- **Bash** (local shell) - Default backend for Linux/macOS systems
- **SSH** (remote shell) - Execute commands on remote systems
- **PowerShell** (Windows environments) - Windows command execution

## Caching
Command results can be cached to speed up repeated operations and reduce system load. The caching system automatically determines when to use cached results based on command parameters and context.

## Extensibility
You can add your own commands, backends, and plugins to extend Mancer's functionality. The framework is designed with extensibility in mind, following the Open/Closed principle.

## Version Awareness
Mancer automatically detects tool versions and adapts command behavior for backward compatibility. This ensures your code works across different system tool versions without modification.

## Data Formats
Commands can return results in multiple formats:
- **Raw output** - Original command output
- **Structured data** - Parsed and organized results
- **JSON** - Machine-readable format
- **DataFrame** - pandas DataFrame for analysis
- **NumPy arrays** - Numerical data processing

## Execution Context
Commands execute within a context that includes:
- Working directory
- Environment variables
- Remote execution settings
- Execution parameters

## Glossary
- **Command**: An executable system operation represented by a class
- **Backend**: The environment in which a command runs (bash, SSH, PowerShell)
- **Chain**: A sequence of commands executed in order with result passing
- **Plugin**: An extension module for custom features
- **Context**: The execution environment for commands
- **Result**: The output and metadata from command execution
- **Version Adapter**: Version-specific parsing logic for commands

## Related Documentation
- [Commands](user-guide/commands.md) - How to create and use commands
- [Data Formatting](user-guide/data-formatting.md) - Working with different output formats
- [Configuration](user-guide/configuration.md) - Setting up execution contexts
- [Versioning](user-guide/versioning-compatibility.md) - Tool version compatibility
- [Custom Commands](extending/custom-commands.md) - Creating your own commands
