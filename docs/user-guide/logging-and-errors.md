# Logging & Observability, Error Handling

This guide shows how to enable logging, inspect execution history, use live output, and handle errors properly.

## Enabling command logging
Use CommandLoggerService and/or ShellRunner options.

```python
from mancer.domain.service.command_logger_service import CommandLoggerService
from mancer.application.shell_runner import ShellRunner

# Initialize logging backend (console and file)
logger = CommandLoggerService.get_instance()
logger.initialize(
    log_level="info",
    log_dir="logs",
    log_file="mancer.log",
    console_enabled=True,
    file_enabled=True,
)

runner = ShellRunner(enable_command_logging=True, log_level="info", log_to_file=True)
```

## Execution history
Each CommandResult includes an ExecutionHistory with steps. You can inspect it:

```python
res = runner.execute(runner.create_command("ls").long())
history = res.get_history()
print("Steps:", history.get_steps_count())
last = history.get_last_step()
print("Last command:", last.command_string, "success:", last.success)
```

## Live output
To stream output while a command runs, enable live output:

```python
cmd = runner.create_command("tail").with_option("-f").add_arg("/var/log/syslog")
res = runner.execute(cmd, live_output=True)
```

Note: ShellRunner sets context parameters (live_output=True, interval=0.1) for the duration of the call.

## Accessing command history from logger
```python
from mancer.domain.service.command_logger_service import CommandLoggerService
cl = CommandLoggerService.get_instance()
entries = cl.get_command_history(limit=10)
for e in entries:
    print(e["command"]["command_name"], e.get("result", {}))
```

## Error handling patterns
- Check result.success or use res.is_success()
- Inspect result.exit_code and result.error_message
- For structured data, validate presence of expected keys before processing

```python
res = runner.execute(runner.create_command("cat").add_arg("/nonexistent"))
if not res.is_success():
    print("Error:", res.error_message)
    # Decide whether to retry or log and continue
```

## Troubleshooting tips
- Increase log verbosity: set log_level="debug" in CommandLoggerService/ShellRunner
- For SSH issues: verify host/user/key_file, and consider ssh_options={"StrictHostKeyChecking": "no"}
- For sudo: ensure use_sudo=True and provide sudo_password if needed
- Avoid logging very large outputs; by default, debug logging truncates long outputs

## Recommended practices
- Keep logging enabled in development (console) and optionally to file in CI
- Use ExecutionHistory to enrich diagnostics on failures
- Use live output selectively for long-running commands

