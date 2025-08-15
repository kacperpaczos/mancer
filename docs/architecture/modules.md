# Modules

## Application Layer
- **command_manager.py**: Manages command execution and chaining
- **command_cache.py**: Handles command result caching
- **service/**: Application services (e.g., remote config, systemd inspector)

## Domain Layer
- **model/**: Data models (CommandContext, CommandResult, etc.)
- **service/**: Domain services (command chains, logging, versioning)
- **interface/**: Abstractions for commands and backends

## Infrastructure Layer
- **backend/**: System backends (bash, ssh, powershell)
- **command/**: Command implementations (file, network, system)
- **factory/**: Factories for commands and backends
- **logging/**: Logging backends
- **web/**: Web/Flask integration

## Interfaces
- **api_interface.py**: API interface
- **cli_interface.py**: Command-line interface
- **command_builder.py**: Command construction utilities
