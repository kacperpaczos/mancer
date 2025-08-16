# Configuration

This page explains how to configure execution backends and runtime context in code. The primary entry point is ShellRunner and the CommandContext model.

## Backends: local vs SSH

- Local (default): backend_type="bash"
- Remote (SSH): still backend_type="bash", but you enable remote execution on the runner/context

```python
from mancer.application.shell_runner import ShellRunner

# Local runner (default)
runner = ShellRunner(backend_type="bash")

# Enable remote execution for subsequent commands
runner.set_remote_execution(host="your-host", user="your-user")
```

## Remote configuration options

Use ShellRunner.set_remote_execution(...) or CommandContext.set_remote_execution(...):

```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner()
runner.set_remote_execution(
    host="your-host",
    user="your-user",
    port=22,                    # default
    key_file="~/.ssh/id_rsa",  # or password="..."
    use_agent=True,             # use ssh-agent
    identity_only=False,        # IdentitiesOnly=yes
    use_sudo=False,             # run privileged commands
    sudo_password=None,         # if sudo requires password
    gssapi_auth=False,
    gssapi_keyex=False,
    gssapi_delegate_creds=False,
    ssh_options={"StrictHostKeyChecking": "no"},  # any additional SSH options
)
```

Equivalent via CommandContext (if building your own context):

```python
from mancer.domain.model.command_context import CommandContext

ctx = CommandContext()
ctx.set_remote_execution(
    host="your-host",
    user="your-user",
    key_file="~/.ssh/id_rsa",
    use_sudo=True,
)
```

## Working directory and environment variables

You can control current directory and environment variables via CommandContext:

```python
from mancer.domain.model.command_context import CommandContext
from mancer.infrastructure.command.system.echo_command import EchoCommand

ctx = CommandContext()
ctx.change_directory("/var/log")
ctx.environment_variables["LC_ALL"] = "C"

result = EchoCommand().with_arg("hello").execute(ctx)
```

If you use ShellRunner, it manages a reusable context internally. You can pass overrides per call:

```python
from mancer.application.shell_runner import ShellRunner
from mancer.infrastructure.command.system.df_command import DfCommand

runner = ShellRunner()
res = runner.execute(DfCommand(), context_params={
    "current_directory": "/",
    "environment_variables": {"LANG": "C"},
})
```

## Sudo and privileged commands

For commands that require elevated privileges:

- Set use_sudo=True in remote host configuration
- Provide sudo_password if your setup prompts for it

```python
runner.set_remote_execution(host="your-host", user="your-user", use_sudo=True, sudo_password="***")
```

## Using config files (optional pattern)

Mancer does not require a specific config file format. If you prefer files, load them yourself and apply values to ShellRunner/CommandContext:

```python
import json
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner()
conf = json.load(open("mancer.json"))
runner.set_remote_execution(**conf["remote"])  # e.g., {"host": ..., "user": ..., "key_file": ...}
```
