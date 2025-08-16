# Contributing Guide

If you'd like to contribute to the Mancer framework, here's how to get started.

## Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Liberos-Systems/mancer.git
cd mancer
```

### 2. Set up the Development Environment
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

### 3. Install Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

### 4. Verify Setup
```bash
# Run tests to ensure everything works
pytest

# Check code quality
black --check src/ tests/
flake8 src/ tests/
```

## Development Workflow

### 1. Create a New Branch
Always create a new branch for your feature or bugfix:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

### 2. Make Your Changes
- Write your code following the project's coding standards
- Include type hints for all functions
- Write docstrings for all public classes and methods
- Add tests for new functionality

### 3. Test Your Changes
```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=src/mancer --cov-report=html

# Run specific test file
pytest tests/unit/test_your_feature.py
```

### 4. Check Code Quality
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check code style
flake8 src/ tests/

# Type checking
mypy src/
```

### 5. Commit Your Changes
```bash
git add .
git commit -m "Description of your changes

- What was changed
- Why it was changed
- Any breaking changes"
```

### 6. Submit a Pull Request
- Push your branch to GitHub
- Create a pull request with a clear description
- Include any relevant issue numbers
- Request review from maintainers

## Code Style Guidelines

### Python Code Standards
- Follow PEP8 for Python code
- Use meaningful variable and function names
- Maximum line length: 88 characters (Black formatter)
- Use type hints for all function parameters and return values

### Code Formatting
The project uses several tools for code quality:
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Code style checking
- **mypy**: Type checking

### Documentation Standards
- Use docstrings for all public classes and methods
- Follow Google docstring format
- Include examples in docstrings when helpful
- Update relevant documentation files

### Testing Standards
- Write unit tests for new functionality
- Maintain test coverage above 80%
- Include integration tests for complex features
- Test both success and failure scenarios
- Use descriptive test names

## Adding New Features

### Adding New Commands
When adding new system commands:

1. **Create the Command Class**
   ```python
   from mancer.infrastructure.command.base_command import BaseCommand
   
   class MyNewCommand(BaseCommand):
       tool_name = "my_tool"
       
       def __init__(self):
           super().__init__("my-command")
           
       def execute(self, context: CommandContext, input_result=None) -> CommandResult:
           # Implementation here
           pass
   ```

2. **Add Version Support** (if needed)
   ```python
   version_adapters = {
       "1.x": "_parse_output_v1",
       "2.x": "_parse_output_v2"
   }
   ```

3. **Create Examples**
   - Add to `examples/` directory
   - Include in relevant documentation

4. **Add Tests**
   - Unit tests in `tests/unit/`
   - Integration tests if needed

### Adding New Backends
When adding new execution backends:

1. **Implement the Interface**
   ```python
   from mancer.domain.interface.backend_interface import IExecutionBackend
   
   class MyNewBackend(IExecutionBackend):
       def execute(self, command: str) -> Tuple[int, str, str]:
           # Implementation here
           pass
   ```

2. **Register in Factory**
   - Update `backend_factory.py`
   - Add configuration options

3. **Add Tests**
   - Test backend functionality
   - Test integration with commands

### Adding New Data Formats
When adding new data formats:

1. **Extend DataFormat Enum**
   ```python
   class DataFormat(Enum):
       LIST = "list"
       TABLE = "table"
       JSON = "json"
       DATAFRAME = "dataframe"
       NDARRAY = "ndarray"
       MY_FORMAT = "my_format"  # New format
   ```

2. **Implement Conversion Logic**
   - Add to `DataConverterService`
   - Handle conversion to/from other formats

3. **Add Tests**
   - Test format conversion
   - Test edge cases

## Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── smoke/          # Smoke tests
└── docker/         # Docker-based tests
```

### Writing Good Tests
```python
def test_command_execution_success():
    """Test successful command execution."""
    # Arrange
    command = MyCommand()
    context = CommandContext()
    
    # Act
    result = command.execute(context)
    
    # Assert
    assert result.success is True
    assert result.exit_code == 0
    assert len(result.raw_output) > 0

def test_command_execution_failure():
    """Test command execution failure."""
    # Arrange
    command = MyCommand()
    context = CommandContext()
    
    # Act
    result = command.execute(context)
    
    # Assert
    assert result.success is False
    assert result.exit_code != 0
    assert result.error_message is not None
```

### Test Coverage
- Aim for at least 80% code coverage
- Test edge cases and error conditions
- Test version compatibility if applicable
- Test backward compatibility

### Running Tests
```bash
# All tests
pytest

# Specific test categories
pytest tests/unit/
pytest tests/integration/

# With coverage
pytest --cov=src/mancer --cov-report=html

# Specific test file
pytest tests/unit/test_my_feature.py

# Specific test function
pytest tests/unit/test_my_feature.py::test_specific_function
```

## Documentation Guidelines

### When to Update Documentation
- Adding new features
- Changing existing APIs
- Fixing bugs that affect user experience
- Adding new examples

### What to Document
- New classes and methods
- Configuration options
- Examples and use cases
- Breaking changes
- Migration guides

### Documentation Structure
```
docs/
├── getting-started/     # Installation and setup
├── user-guide/          # User documentation
├── api/                 # API reference
├── development/         # Developer documentation
├── examples/            # Code examples
└── architecture/        # System architecture
```

## Pull Request Process

### Before Submitting
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Examples work correctly
- [ ] No breaking changes (or clearly documented)

### Pull Request Template
```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass

## Documentation
- [ ] User documentation updated
- [ ] API documentation updated
- [ ] Examples updated

## Breaking Changes
- [ ] No breaking changes
- [ ] Breaking changes documented
- [ ] Migration guide provided

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code commented where needed
- [ ] Corresponding changes to documentation
```

### Code Review Process
1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Maintainer Review**: At least one maintainer reviews the code
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: Once approved, the PR can be merged

## Getting Help

### Resources
- [Development Guide](development.md)
- [Architecture Overview](architecture/overview.md)
- [API Reference](api.md)
- [Examples](examples/all-examples.md)

### Contact
- GitHub Issues: [Report bugs or request features](https://github.com/Liberos-Systems/mancer/issues)
- Email: kacperpaczos2024@proton.me
- GitHub Discussions: [Community discussions](https://github.com/Liberos-Systems/mancer/discussions)

### Common Issues
1. **Import errors**: Make sure you're in the virtual environment
2. **Test failures**: Check if all dependencies are installed
3. **Code formatting issues**: Run `black` and `isort` on your code
4. **Documentation build failures**: Check markdown syntax and links

## Recognition

Contributors are recognized in several ways:
- GitHub contributors list
- Release notes for significant contributions
- Special thanks in documentation
- Contributor badges and recognition

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:
- Be respectful and inclusive
- Focus on the code and technical issues
- Help others learn and grow
- Report any inappropriate behavior

Thank you for contributing to Mancer!
