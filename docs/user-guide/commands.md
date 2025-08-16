# Commands

This guide explains how to create and execute commands, build chains, and run them locally or remotely.

## Running a Single Command
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
cmd = runner.create_command("ls").long().all()  # ls -la
result = runner.execute(cmd)

print("Success:", result.is_success())
print("Exit code:", result.exit_code)
print("First lines:\n", "\n".join(result.raw_output.splitlines()[:5]))
```

## Chaining Commands (Pipelines)
```python
from mancer.application.shell_runner import ShellRunner
from mancer.infrastructure.command.system.ps_command import PsCommand
from mancer.infrastructure.command.system.grep_command import GrepCommand

runner = ShellRunner()

pipeline = PsCommand().with_option("-ef").pipe(GrepCommand("python"))
result = pipeline.execute(runner.context)

print("Items found:", len(result.get_structured()))
```

## Remote Command Execution (SSH)
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
runner.set_remote_execution(host="your-host", user="your-user")

cmd = runner.create_command("ls").long()
remote_result = runner.execute(cmd)
print("Remote sample:\n", "\n".join(remote_result.raw_output.splitlines()[:5]))
```

See [Examples](examples.md) for more advanced scenarios.
