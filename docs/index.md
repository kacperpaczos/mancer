# Mancer Framework

Professional command automation and orchestration for system and network environments.

---

## Install
```bash
# Using pip (recommended)
pip install mancer

# From source (development)
git clone https://github.com/your-org/mancer.git
cd mancer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Quickstart
```python
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type="bash")
cmd = runner.create_command("echo").text("hello mancer")
result = runner.execute(cmd)
print(result.raw_output)
```

---

## What is Mancer?
- Create and execute system commands and custom command chains
- Run locally (bash) or remotely (SSH)
- Manage contexts (env, working dir) and execution history
- Convert results to JSON / pandas DataFrame / NumPy ndarray
- Extend with your own commands and backends

---

## Quick Links
- [Getting Started](getting-started/installation.md)
- [Examples](user-guide/examples.md)
- [API Reference](api.md)
- [Architecture](architecture/overview.md)

---

## Community & Contact
Questions or want to contribute? [GitHub Repository](https://github.com/your-org/mancer)
