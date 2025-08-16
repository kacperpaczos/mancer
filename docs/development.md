# Development

## Documentation prerequisites
Install docs toolchain locally:
```bash
pip install mkdocs-material mkdocstrings[python]
```
Run docs server or build:
```bash
./dev_tools/mancer_tools.sh --docs dev    # mkdocs serve
./dev_tools/mancer_tools.sh --docs build  # mkdocs build
```

## Architecture for Developers
See [Architecture](architecture/overview.md) for a high-level overview.

For detailed architecture information:
- [DDD Architecture Overview](architecture/ddd-overview.md) - Complete architecture with diagrams
- [Feature Lifecycle](development/feature-lifecycle.md) - Development process and workflow
- [Version Adaptation](development/version-adaptation.md) - Tool version compatibility
- [Contributing Guide](development/contributing.md) - How to contribute to Mancer

## Core Classes: ShellRunner vs CommandManager

Mancer provides two main approaches for command execution, each serving different use cases:

### ShellRunner
- **Location**: `src/mancer/application/shell_runner.py`
- **Purpose**: High-level interface for quick command execution
- **Features**:
  - Automatic context management (working directory, environment variables)
  - Built-in remote execution support via SSH
  - Simplified API for common use cases
  - Automatic command result formatting

```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
result = runner.execute(runner.create_command("ls").long())
```

### CommandManager
- **Location**: `src/mancer/application/command_manager.py`
- **Purpose**: Lower-level interface for advanced command orchestration
- **Features**:
  - Manual context management for fine-grained control
  - Command chaining and pipelines with explicit control
  - Advanced features like execution history and caching
  - Direct access to command execution internals

```python
from mancer.application.command_manager import CommandManager
from mancer.domain.model.command_context import CommandContext

manager = CommandManager()
context = CommandContext()
result = manager.execute_command("ls -la", context)
```

### When to Use Which?

- **Use ShellRunner** for:
  - Quick scripts and automation
  - Simple command execution
  - Remote execution over SSH
  - When you don't need fine-grained control

- **Use CommandManager** for:
  - Complex command orchestration
  - Custom execution workflows
  - When you need to manage execution context manually
  - Advanced features like execution history analysis

## Testing

### Test Structure
- Unit tests are in the `tests/unit/` directory
- Integration tests are in `tests/integration/`
- Smoke tests are in `tests/smoke/`
- Docker-based tests are in `tests/docker/`

### Running Tests
Use `pytest` to run tests:
```bash
# All tests
pytest

# Only unit tests
pytest tests/unit/

# Only integration tests
pytest tests/integration/

# With coverage
pytest --cov=src/mancer --cov-report=html

# Specific test file
pytest tests/unit/test_base_command.py

# Specific test function
pytest tests/unit/test_base_command.py::test_command_execution
```

### Test Scripts
The project provides several test scripts:
```bash
# Run all tests
./scripts/run_tests.sh

# Run only unit tests
./scripts/run_tests.sh --unit

# Run with coverage
./scripts/run_tests.sh --coverage

# Run tests in Docker
./scripts/unittest_docker.sh

# Run tests in virtual environment
./scripts/venv_unit_tests.sh
```

### Test Coverage
Maintain high test coverage:
```bash
# Generate coverage report
pytest --cov=src/mancer --cov-report=html --cov-report=term

# View coverage in browser
open htmlcov/index.html
```

## Code Style

### Python Code Standards
- Follow PEP8 for Python code
- Use meaningful variable and function names
- Use type hints for all function parameters and return values
- Maximum line length: 88 characters (Black formatter)

### Code Formatting
The project uses several tools for code quality:
```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Check code style with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

### Pre-commit Hooks
Install pre-commit hooks for automatic code formatting:
```bash
pip install pre-commit
pre-commit install
```

## Development Workflow

### Setting Up Development Environment
1. Clone the repository:
   ```bash
   git clone https://github.com/Liberos-Systems/mancer.git
   cd mancer
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Development Process
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
   pytest
   ```

4. **Check code quality**:
   ```bash
   black --check src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

5. **Submit a pull request** with your changes.

### Adding New Commands
When adding new system commands:

1. Create a new class in the appropriate directory under `src/mancer/infrastructure/command/`
2. Inherit from `BaseCommand` and implement required methods
3. Add version-specific parsing methods if needed
4. Create an example showing how to use the command
5. Add unit tests for the command

### Adding New Backends
When adding new execution backends:

1. Create a new file in `src/mancer/infrastructure/backend/`
2. Implement the backend class, inheriting from the appropriate base class
3. Register your backend in the backend factory
4. Add unit tests for the backend

## Version Support

When adding version-specific behavior:

1. Document supported versions in the class docstring
2. Add version-specific methods using the naming convention `_parse_output_vX`
3. Update the `version_adapters` dictionary with version patterns
4. Add tests for different version scenarios

For detailed information on version adaptation, see [Version Adaptation](development/version-adaptation.md).

## Building and Packaging

### Building the Package
```bash
# Build source distribution
python setup.py sdist

# Build wheel
python setup.py bdist_wheel

# Build both
python setup.py sdist bdist_wheel
```

### Development Installation
```bash
# Install in editable mode
pip install -e .

# Install with development extras
pip install -e ".[dev]"
```

## Continuous Integration

### GitHub Actions
The project uses GitHub Actions for CI/CD. See `.github/workflows/` for configuration.

### Local CI Simulation
Run CI checks locally:
```bash
# Run all CI checks
./scripts/pipeline/local.sh

# Run specific stage
./scripts/pipeline/stage.sh

# Run quick checks
./scripts/pipeline/quick.sh
```

## Troubleshooting

### Common Issues
1. **Import errors**: Make sure you're in the virtual environment
2. **Test failures**: Check if all dependencies are installed
3. **Code formatting issues**: Run `black` and `isort` on your code

### Getting Help
- Check the [FAQ](faq.md)
- Search existing [GitHub Issues](https://github.com/Liberos-Systems/mancer/issues)
- Create a new issue for bugs or feature requests
- Contact: kacperpaczos2024@proton.me

## Contributing Guidelines

### Code Review Process
1. All changes must pass CI checks
2. Code must have adequate test coverage
3. Documentation must be updated for new features
4. Follow the established code style and patterns

### Documentation Standards
- Update relevant documentation when adding new features
- Include code examples in docstrings
- Update README.md for user-facing changes
- Update development.md for developer-facing changes

### Testing Standards
- Write unit tests for new functionality
- Maintain test coverage above 80%
- Include integration tests for complex features
- Test both success and failure scenarios

For comprehensive contributing information, see [Contributing Guide](development/contributing.md).
