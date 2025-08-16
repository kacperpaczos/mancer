# All Examples

Below is a catalog of all runnable scripts under the examples/ directory.
Each entry includes a short description and how to run it locally.

Note: Some examples require extra setup (e.g., Docker or SSH).

- apt_example.py
  - Description: Demonstrates interacting with apt-related commands (package info/ops).
  - Run: `python examples/apt_example.py`

- basic_usage.py
  - Description: Minimal ShellRunner usage (local bash) and executing a simple command.
  - Run: `python examples/basic_usage.py`

- cache_usage.py
  - Description: Using command caching; demonstrates speed-up for repeated commands.
  - Run: `python examples/cache_usage.py`

- cache_visualization.py
  - Description: Visualize cache behavior or statistics (requires optional plotting libs if used).
  - Run: `python examples/cache_visualization.py`

- command_chains.py
  - Description: Building command chains/pipelines (e.g., ps | grep) and executing them.
  - Run: `python examples/command_chains.py`

- command_logging_example.py
  - Description: Configure and view command logging output (console/file).
  - Run: `python examples/command_logging_example.py`

- create_custom_command.py
  - Description: Walkthrough for creating a custom command class (extending BaseCommand).
  - Run: `python examples/create_custom_command.py`

- custom_commands.py
  - Description: Using one or more custom commands in practice.
  - Run: `python examples/custom_commands.py`

- data_formats_usage.py
  - Description: Converting CommandResult to JSON / pandas DataFrame / NumPy ndarray.
  - Run: `python examples/data_formats_usage.py`
  - Requires: `pip install pandas numpy`

- df_command_example.py
  - Description: Using the df command; parsing and presenting filesystem usage.
  - Run: `python examples/df_command_example.py`

- docker_testing_example.py
  - Description: Executing or validating framework behavior inside Docker containers.
  - Run: `python examples/docker_testing_example.py`
  - Requires: Docker/Compose installed and running.

- execution_history_analysis.py
  - Description: Working with ExecutionHistory and steps; analyzing results.
  - Run: `python examples/execution_history_analysis.py`

- new_logger_example.py
  - Description: Using the logging subsystem (mancer.infrastructure.logging.* backends).
  - Run: `python examples/new_logger_example.py`

- remote_sudo_usage.py
  - Description: Executing a remote command over SSH with sudo.
  - Run: `python examples/remote_sudo_usage.py`
  - Requires: SSH access and sudo configuration on the target host.

- remote_usage.py
  - Description: Basic remote execution (SSH) example.
  - Run: `python examples/remote_usage.py`
  - Requires: SSH access (key or password).

- ssh_auth_methods.py
  - Description: Demonstrates multiple SSH authentication methods (key, agent, password).
  - Run: `python examples/ssh_auth_methods.py`

- version_checking.py
  - Description: Checking tool versions and compatibility handling.
  - Run: `python examples/version_checking.py`

- version_info_example.py
  - Description: Using VersionInfo and registry with commands/services.
  - Run: `python examples/version_info_example.py`

Tip: From the project root, run an example with:
```bash
python -m examples.basic_usage
# or
python examples/basic_usage.py
```

