# Mancer

Programmable system automation engine for Linux: run commands locally (Bash) and remotely (SSH) with one Python API. Get structured results, compose commands, and keep execution history.

## Install
```bash
pip install -U mancer
```

## Quickstart
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
result = runner.execute(runner.create_command("echo").text("hello"))
print(result.raw_output)
```

### Remote over SSH
```python
from mancer.application.shell_runner import ShellRunner
from mancer.domain.model.command_context import CommandContext, RemoteHost

runner = ShellRunner(backend_type="bash")
context = CommandContext(remote_host=RemoteHost(host="1.2.3.4", user="ubuntu"))
result = runner.execute(runner.create_command("ls").long(), context=context)
```

## Why Mancer vs Fabric
- Local and remote in one model: Bash and SSH backends share one API
- Structured data: JSON / pandas DataFrame / NumPy ndarray adapters
- Version‑aware behavior: commands adapt parsing to detected tool versions
- Composable commands and chains with execution history

See Fabric: https://www.fabfile.org/

## Examples
- Basic: echo/ls/grep pipelines
- Remote: SSH with optional sudo
- Data: convert outputs to JSON/DataFrame/ndarray

## Contributing
```bash
pip install pre-commit
pre-commit install --install-hooks -t pre-commit -t pre-push
```

## License
MIT