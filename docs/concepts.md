# Core Concepts

## Command Abstraction
Mancer treats every system operation as a command object, making it easy to manage, log, and chain operations.

## Command Chains
You can combine multiple commands into a single chain, allowing for complex workflows and automation.

## Backends
Mancer supports multiple execution backends:
- Bash (local shell)
- SSH (remote shell)
- PowerShell (Windows environments)

## Caching
Command results can be cached to speed up repeated operations and reduce system load.

## Extensibility
You can add your own commands, backends, and plugins to extend Mancer's functionality.

## Glossary
- **Command**: An executable system operation
- **Backend**: The environment in which a command runs
- **Chain**: A sequence of commands executed in order
- **Plugin**: An extension module for custom features
