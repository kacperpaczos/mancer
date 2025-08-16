# Mancer Framework

Professional command automation and orchestration for system and network environments.

---

## Get started

=== "Python"

    ```bash
    pip install mancer
    ```

=== "From source"

    ```bash
    git clone https://github.com/your-org/mancer.git
    cd mancer
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    ```

---

## Quickstart

=== "Python"

    ```python
    from mancer.application.shell_runner import ShellRunner

    runner = ShellRunner(backend_type="bash")
    cmd = runner.create_command("echo").text("hello mancer")
    result = runner.execute(cmd)
    print(result.raw_output)
    ```

=== "CLI"

    ```bash
    mancer run "echo hello mancer"
    ```

---

## Learn more

- Flexible Orchestration — Define workflows with chains/pipelines or custom commands
- Local & Remote — Run locally (bash) or remotely (SSH) with unified API
- Rich Results — Convert to JSON / pandas DataFrame / NumPy ndarray
- Extensible — Add your own commands, backends, and logging

[Explore Examples](user-guide/examples.md) · [Read the User Guide](user-guide/commands.md)

---

## Quick Links
- [Get Started](getting-started/installation.md)
- [Tutorials](user-guide/examples.md)
- [Agents / Tools](/) <!-- Placeholder if we introduce higher-level concepts later -->
- [API Reference](api.md)
- [Contributing](https://github.com/your-org/mancer)

---

## Watch & Learn
> Coming soon: Intro video to Mancer and live demos

---

## Community & Contact
Questions or want to contribute? [GitHub Repository](https://github.com/your-org/mancer)
