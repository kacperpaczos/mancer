# Mancer

Programmable system automation engine for Linux: run commands locally (Bash) and remotely (SSH) with one Python API. Get structured results, compose commands, and keep execution history.

> Status: pre‑1.0 (API may change). Linux only for now. SSH support is experimental.

## What is Mancer

Mancer is a programmable system automation engine for Linux. It lets you execute commands locally (Bash) and remotely (SSH) through a single Python API with structured results, caching, and execution history. Locally it is shell‑native (runs on your system’s Bash), in contrast to Fabric which is largely a wrapper over Paramiko and Invoke.

## Features

- Local & Remote: run locally (Bash) and remotely (SSH) via one API
- Shell‑native (local): executes on your system’s Bash — no Invoke/Paramiko layer
- Structured results: LIST / JSON / pandas.DataFrame / numpy.ndarray
- Caching & history: cache results and inspect execution history
- Live output: stream stdout/stderr in real time
- Extensible: add your own commands, backends, and logging

## Install
Requirements: Python 3.9+
```bash
pip install -U mancer
```

## Quickstart

### Local execution
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
cmd = runner.create_command("echo").text("hello mancer")
result = runner.execute(cmd)
print(result.raw_output)
```

### Remote over SSH (experimental)
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner()
runner.set_remote_execution(host="1.2.3.4", user="ubuntu", key_file="~/.ssh/id_rsa")
cmd = runner.create_bash_command("ls -la /var/log")
res = runner.execute(cmd)
print(res.raw_output)
```

### Bash pipelines
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner()
cmd = runner.create_bash_command("ls -la | grep py | wc -l")
res = runner.execute(cmd)
print(res.raw_output)
```

### Data conversion (pandas / numpy)
```python
from mancer.application.shell_runner import ShellRunner
from mancer.domain.service.data_converter_service import DataFormatConverter
from mancer.domain.model.data_format import DataFormat

runner = ShellRunner()
res = runner.execute(runner.create_bash_command("printf 'size\n42K\n1.5M\n'"))
records = res.structured_output  # list of dicts

df = DataFormatConverter.convert(records, DataFormat.LIST, DataFormat.DATAFRAME)
nd = DataFormatConverter.convert(records, DataFormat.LIST, DataFormat.NDARRAY)
```

## Alternatives & When to use

- **Fabric/Invoke**: Higher-level Python task runner; largely a wrapper over Paramiko and Invoke (per Fabric docs). Mancer executes locally on pure Bash (shell‑native) and focuses on a unified command API with structured results. Choose Fabric for Python task workflows and SSH-centric flows; choose Mancer when you prefer shell pipelines and want symmetrical local/remote execution with structured data.

- **Ansible**: Config management at scale; Mancer is a lightweight programmable engine, not inventory-driven CM.

- **Paramiko**: SSH library; Mancer provides a higher-level command model and data adapters.

- **plumbum / subprocess**: Great for raw shelling; Mancer adds structure, history, and remote symmetry.

See also: [Fabric](https://www.fabfile.org/)

## Security Notes

- Prefer SSH keys over passwords; manage permissions carefully.
- Use sudo only when required; avoid hardcoding secrets.
- Review command history/logs for sensitive output before sharing.

## Roadmap

- Stabilize SSH session handling and features
- Windows and macOS support
- Richer built-in commands and pipelines
- CLI improvements and docs

## Contributing
```bash
pip install pre-commit
pre-commit install --install-hooks -t pre-commit -t pre-push
```

## Links

- [Documentation](docs/)
- [GitHub](https://github.com/Liberos-Systems/mancer)

## License
MIT