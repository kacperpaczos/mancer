# Quickstart

This quickstart shows the simplest way to run a command using Mancer's high-level runner and how to chain commands. It also briefly covers remote execution.

## 1) Run your first command
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")

# Create a command (ls -la) and execute it
cmd = runner.create_command("ls").long().all()
result = runner.execute(cmd)

print("Success:", result.is_success())
print("Exit code:", result.exit_code)
print("Raw output:\n", result.raw_output[:200])
```

## 2) Build a small pipeline (chain)
```python
from mancer.application.shell_runner import ShellRunner
from mancer.infrastructure.command.system.ps_command import PsCommand
from mancer.infrastructure.command.system.grep_command import GrepCommand

runner = ShellRunner()

pipeline = PsCommand().with_option("-ef").pipe(GrepCommand("python"))
result = pipeline.execute(runner.context)

print("Matching processes:", len(result.get_structured()))
```

## 3) Remote execution (SSH)
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")

# Configure remote target (provide correct host/user and authentication)
runner.set_remote_execution(host="your-host", user="your-user")

# Execute a basic remote ls
cmd = runner.create_command("ls").long()
remote_result = runner.execute(cmd)
print("Remote output sample:\n", remote_result.raw_output.splitlines()[:5])
```

Next steps: see the [User Guide](../user-guide/commands.md) and the [Examples](../user-guide/examples.md) for full programs.
