# DDD Architecture Overview

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
│  │  └─────────────────┘  └─────────────────────┘  └─────────────────┘                  │    │
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

## Flow of Control

1. **User Code** interacts with the Interface Layer
2. **Interface Layer** creates and configures commands
3. **Application Layer** orchestrates command execution
4. **Domain Layer** contains business logic and interfaces
5. **Infrastructure Layer** implements concrete commands, backends and external services

## Key Responsibilities by Layer

### Interface Layer
- **CLI**: Command-line interface for user interaction
- **API**: Programmatic interface for library users
- **CommandFactory**: Creates and configures command objects
- **ResultFormatter**: Formats command results for different outputs

### Application Layer
- **CommandExecutor**: Orchestrates command execution
- **CommandChain**: Manages command pipelines and workflows
- **VersionManager**: Handles tool version compatibility

### Domain Layer
- **Models**: Core domain entities (CommandContext, CommandResult, VersionInfo)
- **Interfaces**: Abstractions for commands, backends and parsers
- **Services**: Domain-specific logic for versions, formatting, and caching

### Infrastructure Layer
- **Command Implementations**: Concrete command classes (DFCommand, LSCommand, etc.)
- **Execution Backends**: Local (bash) and remote (SSH) execution engines
- **Configuration**: Configuration loading and version storage

## Core Domain Models

### CommandContext
Represents the execution context for commands:
- Working directory
- Environment variables
- Remote execution settings
- Execution parameters

### CommandResult
Contains the result of command execution:
- Raw output (stdout/stderr)
- Structured output (parsed data)
- Exit code
- Execution metadata
- Execution history

### VersionInfo
Manages tool version information:
- Tool name and version
- Version compatibility
- Version-specific behavior adapters

## Design Principles

### Separation of Concerns
Each layer has a specific responsibility and doesn't know about the implementation details of other layers.

### Dependency Inversion
High-level modules (Application) don't depend on low-level modules (Infrastructure). Both depend on abstractions defined in the Domain layer.

### Single Responsibility
Each class has one reason to change and one responsibility.

### Open/Closed Principle
The system is open for extension (new commands, backends) but closed for modification (existing interfaces remain stable).

## Extensibility Points

### Adding New Commands
1. Create a new class inheriting from `BaseCommand`
2. Implement required methods (`execute`, `_parse_output`)
3. Add version-specific parsing if needed
4. Register in the command factory

### Adding New Backends
1. Implement the `IExecutionBackend` interface
2. Add backend-specific configuration
3. Register in the backend factory
4. Update configuration files

### Adding New Data Formats
1. Extend the `DataFormat` enum
2. Implement format conversion in `DataConverterService`
3. Add format-specific parsing logic

## Benefits of This Architecture

1. **Maintainability**: Clear separation of concerns makes code easier to understand and modify
2. **Testability**: Each layer can be tested independently with mocks
3. **Extensibility**: New features can be added without modifying existing code
4. **Scalability**: The layered approach supports growth and complexity
5. **Team Development**: Different developers can work on different layers simultaneously
