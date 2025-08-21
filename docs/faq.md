# FAQ

## General Questions

**Q: What is Mancer?**
A: Mancer is a domain-driven framework for programmable system automation. It provides a unified API for executing commands locally (bash) or remotely (SSH), with features like command chaining, structured results, execution history, and version-aware behavior.

**Q: What version is Mancer currently at?**
A: Mancer is currently at version 0.1, which is an early development version. The API may evolve between releases as we work toward a stable 1.0 release.

**Q: How do I install Mancer?**
A: See [Installation Guide](getting-started/installation.md) for detailed instructions. The quickest way is:
```bash
pip install -U mancer
```

**Q: How do I run a command?**
A: There are two main ways:
1. **ShellRunner** (recommended for most users):
   ```python
   from mancer.application.shell_runner import ShellRunner
   runner = ShellRunner(backend_type="bash")
   result = runner.execute(runner.create_command("ls").long())
   ```

2. **CommandManager** (for advanced use cases):
   ```python
   from mancer.application.command_manager import CommandManager
   manager = CommandManager()
   result = manager.execute_command("ls -la", context)
   ```

## Usage Questions

**Q: What's the difference between ShellRunner and CommandManager?**
A: **ShellRunner** is a high-level interface for quick command execution with automatic context management. **CommandManager** is a lower-level interface for advanced command orchestration with manual context control. See [Core Classes](development.md#core-classes-shellrunner-vs-commandmanager) for details.

**Q: How do I execute commands remotely over SSH?**
A: Use ShellRunner with remote execution:
```python
runner = ShellRunner(backend_type="bash")
runner.set_remote_execution(host="your-host", user="your-user")
result = runner.execute(runner.create_command("ls").long())
```

**Q: How do I chain commands together?**
A: Use the pipe method to create command chains:
```python
from mancer.infrastructure.command.system.ps_command import PsCommand
from mancer.infrastructure.command.system.grep_command import GrepCommand

pipeline = PsCommand().with_option("-ef").pipe(GrepCommand("python"))
result = pipeline.execute(context)
```

**Q: How do I convert command output to different formats?**
A: Use the `to_format` method:
```python
from mancer.domain.model.data_format import DataFormat

# Convert to JSON
json_result = result.to_format(DataFormat.JSON)

# Convert to pandas DataFrame
df_result = result.to_format(DataFormat.DATAFRAME)
```

## Development Questions

**Q: How do I contribute to Mancer?**
A: See our [Contributing Guide](development/contributing.md) for detailed instructions. The basic steps are:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

**Q: How do I run tests?**
A: Use pytest to run tests:
```bash
# All tests
pytest

# Only unit tests
pytest tests/unit/

# With coverage
pytest --cov=src/mancer --cov-report=html
```

**Q: How do I add a new command?**
A: See [Adding New Commands](development/contributing.md#adding-new-commands) in the Contributing Guide. You'll need to:
1. Create a class inheriting from `BaseCommand`
2. Implement required methods
3. Add tests
4. Create examples

**Q: How do I handle version-specific behavior in commands?**
A: Use version adapters. See [Version Adaptation](development/version-adaptation.md) for detailed examples:
```python
class MyCommand(BaseCommand):
    tool_name = "my_tool"
    version_adapters = {
        "1.x": "_parse_output_v1",
        "2.x": "_parse_output_v2"
    }
```

## Configuration Questions

**Q: How do I configure Mancer?**
A: Mancer uses YAML configuration files. See [Configuration](user-guide/configuration.md) for details. Configuration files are searched in:
1. Current directory
2. `~/.mancer/`
3. `/etc/mancer/`
4. Package directory

**Q: How do I manage tool versions?**
A: Use the tool version management system. See [Tool Versioning](user-guide/versioning-compatibility.md) for details:
```bash
./tools/shell/mancer_tools.sh --versions list
./tools/shell/mancer_tools.sh --versions detect --all
```

**Q: How do I enable logging?**
A: Use the logging system. See [Logging](user-guide/logging-and-errors.md) for details:
```python
from mancer.infrastructure.logging.mancer_logger import MancerLogger
logger = MancerLogger.get_instance()
logger.initialize(log_level="info", console_enabled=True)
```

## Troubleshooting

**Q: I'm getting import errors. What should I do?**
A: Make sure you're in the virtual environment and have installed Mancer correctly:
```bash
source .venv/bin/activate
pip install -e .
```

**Q: Commands are failing. How do I debug?**
A: Enable debug logging and check the execution history:
```python
# Enable debug logging
logger.initialize(log_level="debug")

# Check execution history
history = result.get_history()
print(f"Steps: {history.get_steps_count()}")
```

**Q: SSH connections are failing. What should I check?**
A: Verify your SSH configuration:
- Check host, user, and authentication
- Verify SSH key permissions
- Try with `ssh_options={"StrictHostKeyChecking": "no"}` for testing

**Q: How do I handle sudo commands?**
A: Set `use_sudo=True` in remote execution configuration:
```python
runner.set_remote_execution(
    host="your-host", 
    user="your-user", 
    use_sudo=True, 
    sudo_password="your-password"
)
```

## Performance Questions

**Q: How do I cache command results?**
A: Use the built-in caching system. See [Cache Usage](examples/cache_usage.py) for examples:
```python
# Caching is enabled by default
# Results are automatically cached based on command and context
```

**Q: How do I optimize command execution?**
A: Several strategies:
- Use command chaining instead of multiple separate executions
- Enable result caching for repeated commands
- Use appropriate data formats (avoid unnecessary conversions)
- Batch operations when possible

## Compatibility Questions

**Q: What Python versions are supported?**
A: Mancer requires Python 3.8 or higher.

**Q: What operating systems are supported?**
A: Mancer works on Linux, macOS, and Windows (with some limitations for PowerShell backend).

**Q: How do I handle different tool versions?**
A: Mancer automatically detects tool versions and adapts behavior. See [Version Adaptation](development/version-adaptation.md) for details.

## Getting Help

**Q: Where can I find more examples?**
A: Check the [Examples Directory](examples/all-examples.md) for comprehensive examples covering various use cases.

**Q: How do I report a bug?**
A: Use [GitHub Issues](https://github.com/Liberos-Systems/mancer/issues) to report bugs. Include:
- Description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details

**Q: How do I request a new feature?**
A: Use [GitHub Issues](https://github.com/Liberos-Systems/mancer/issues) to request features. Describe:
- What you want to achieve
- Why it's useful
- Any implementation ideas you have

**Q: How can I contact the maintainers?**
A: Several ways:
- [GitHub Issues](https://github.com/Liberos-Systems/mancer/issues)
- Email: kacperpaczos2024@proton.me
- [GitHub Discussions](https://github.com/Liberos-Systems/mancer/discussions)

## Advanced Questions

**Q: How do I create custom backends?**
A: See [Adding Backends](extending/backends.md) for details. You'll need to implement the `IExecutionBackend` interface.

**Q: How do I extend the data format system?**
A: Extend the `DataFormat` enum and implement conversion logic in `DataConverterService`. See [Data Formatting](user-guide/data-formatting.md) for details.

**Q: How do I implement custom logging backends?**
A: Implement the `LogBackendInterface` and register your backend. See the logging system documentation for details.

**Q: How do I profile command performance?**
A: Use the execution history and timing information:
```python
history = result.get_history()
for step in history.get_steps():
    print(f"Command: {step.command_string}")
    print(f"Duration: {step.execution_time}")
```
