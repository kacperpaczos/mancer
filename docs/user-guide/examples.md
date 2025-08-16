# Examples

## Basic Command (ls -la)
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
cmd = runner.create_command("ls").long().all()
result = runner.execute(cmd)
print(result.raw_output)
```

## Command Chain (ps | grep)
```python
from mancer.application.shell_runner import ShellRunner
from mancer.infrastructure.command.system.ps_command import PsCommand
from mancer.infrastructure.command.system.grep_command import GrepCommand

runner = ShellRunner()
pipeline = PsCommand().with_option("-ef").pipe(GrepCommand("python"))
result = pipeline.execute(runner.context)
print(len(result.get_structured()))
```

## Remote Execution (SSH)
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner()
runner.set_remote_execution(host="your-host", user="your-user")
cmd = runner.create_command("ls").long()
remote_result = runner.execute(cmd)
print("\n".join(remote_result.raw_output.splitlines()[:5]))
```

## Data conversion (to pandas DataFrame)
```python
from mancer.application.shell_runner import ShellRunner
from mancer.domain.model.data_format import DataFormat

runner = ShellRunner(backend_type="bash")
ps = runner.create_command("ps").with_option("-ef")
res = runner.execute(ps)

# Convert to DataFrame (requires pandas installed)
df_res = res.to_format(DataFormat.DATAFRAME)
df = df_res.get_structured()
print(df.head())
```

See the `examples/` directory in the repository for more.
