# Mancer

Mancer — Multisystem Programmable Engine

Professional command automation and orchestration for system and network environments.


<div class="hero-buttons">
  <a class="md-button md-button--primary" href="getting-started/installation/">Get Started</a>
  <a class="md-button" href="user-guide/examples/">Tutorials</a>
  <a class="md-button" href="api/">API Reference</a>
  <a class="md-button" href="https://github.com/Liberos-Systems/mancer">GitHub</a>
</div>

---

## Get started

=== "Python"

    ```bash
    pip install mancer
    ```

=== "From source"

    ```bash
    git clone https://github.com/Liberos-Systems/mancer.git
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

---

## What does “Mancer” mean?

Mancer comes from the Greek “manteia” (divination). In modern fantasy/sci‑fi, a “‑mancer” is a specialist who masters a specific domain or force (e.g., Pyromancer, Geomancer, Technomancer). In our context, Mancer is a programmable engine for mastering systems: shells, processes, data, and remote execution.

- Necromancer — death/spirits
- Pyromancer — fire
- Geomancer — earth
- Hydromancer — water
- Aeromancer — air
- Technomancer — technology
- Chronomancer — time

Fun fact: “mancy” names come from real divination terms (oneiromancy, cartomancy, chiromancy). That’s why “Mancer” is memorable and extensible — you can imagine any specialized “mancer” archetype.

- [Contributing](https://github.com/Liberos-Systems/mancer)

---

## Watch & Learn
> Coming soon: Intro video to Mancer and live demos

---

## Community & Contact
Questions or want to contribute? [GitHub Repository](https://github.com/your-org/mancer)
