# Bash Wrapper Test Strategy

This document captures the agreed structure for testing the Bash wrapper that orchestrates Python scripts and GNU coreutils. It focuses on deterministic unit coverage, faithful integration checks inside Debian LXC containers, and optional end-to-end workflows that mirror real operator flows.

## Test Suite Layout

```
tests/
 ├─ unit/          # pytest + mocks, no external side effects
 ├─ integration/   # real Python/coreutils inside LXC
 └─ e2e/           # optional full workflows, heavily isolated
```

Recommended markers:

- `@pytest.mark.unit` (default; fast, isolated)
- `@pytest.mark.integration` + `@pytest.mark.lxc` (real tools/container)
- `@pytest.mark.e2e` (full workflows; run via `pytest -m e2e --run-e2e`)

## 1. Unit Test Baseline

**Scope**

- Argument parsing (flags, positional args, env propagation)
- Command string construction (python invocation, coreutils dispatch)
- stdout/stderr/codes handling, retry logic, logging hooks

**Technique**

- Use `unittest.mock.patch` to replace `subprocess.run/Popen`.
- Provide fixtures for fake stdout/stderr payloads.
- No LXC dependencies; run locally and in CI by default.

**Positive Scenarios**

1. Valid Python invocation returns stdout, exit code `0`.
2. Coreutils command with options is assembled exactly as expected.
3. Wrapper injects working directory/environment variables.

**Negative Scenarios**

1. Malformed arguments → wrapper raises `ValueError`.
2. Subprocess returns non-zero exit → wrapper surfaces error + stderr.
3. Unexpected stdout encoding → wrapper logs warning and returns fallback.

**Template Snippet**

```
@patch("mancer.infrastructure.backend.bash_backend.subprocess.run")
def test_python_invocation_success(mock_run, tmp_path):
    mock_run.return_value = SimpleNamespace(
        returncode=0, stdout="ok", stderr=""
    )
    wrapper = PythonWrapper()
    result = wrapper.run(["script.py", "--flag"], cwd=tmp_path)

    assert result.exit_code == 0
    mock_run.assert_called_once()
```

## 2. Integration Suite on LXC

**Environment**

- Debian LXC container with Python 3.10+, coreutils, sshd enabled.
- Helper script provisions users, mounts shared workspace, seeds fixtures.

**Fixtures**

- `lxc_session` fixture handles container lifecycle (start, snapshot, teardown).
- `@pytest.mark.integration`, `@pytest.mark.lxc`.

**Positive Scenarios**

1. Real Python script processes file in `/tmp/data.txt` and outputs JSON.
2. Wrapper chains `ls | grep` via coreutils and captures combined stdout.
3. Temporary files created and cleaned successfully.

**Negative Scenarios**

1. Missing Python dependency → wrapper surfaces stderr + specific error code.
2. Permission denied when touching `/root` → error path validated.
3. Container reboot mid-run → wrapper reconnect logic handles failure.

**Data handling**

- Keep fixtures small (<10 KB) and versioned under `tests/fixtures/`.
- Reset state between tests via LXC snapshot restores or cleanup scripts.

## 3. Optional End-to-End Flow

**When to run**

- Pre-release validation
- Reproducing customer workflows
- Benchmarking multi-step automation

**Scenarios**

| Scenario | Description | Expected Outcome |
| --- | --- | --- |
| Happy path automation | Run full wrapper script chaining Python + coreutils | Success, logs archived, exit 0 |
| Large batch ingestion | Process N inputs via loop | Bounded runtime, no leaks |
| Failure recovery | Introduce bad file mid-run | Graceful abort, clear error |

Enable with `pytest -m e2e --run-e2e --lxc-profile=debian12`.

## 4. Orchestration Guidance

1. **Default pipeline**: `pytest -m "unit and not slow"` runs locally on every commit.
2. **Integration gate**: run `pytest -m integration --lxc-config tests/lxc/config.yaml` when verifying real dependencies.
3. **E2E cadence**: nightly or pre-release due to runtime cost.
4. **Data hygiene**: maintain separate fixtures for positive vs negative cases; avoid reusing mutable paths.
5. **Logging**: capture wrapper stdout/stderr alongside container logs for diffing against “traditional” command runs.

## 5. Scenario Checklist

| Layer | Positive Cases | Negative Cases |
| --- | --- | --- |
| Unit | valid args, env injection, success exit | bad args, subprocess failure, encoding issues |
| Integration | file processing, command chaining, cleanup | missing deps, permission denied, container interruption |
| E2E | full workflow, batch processing, metrics capture | failure recovery, rollback validation |

## 6. Next Actions

1. Scaffold pytest modules under `tests/unit`, `tests/integration`, `tests/e2e`.
2. Implement LXC helper scripts + fixtures referenced above.
3. Wire markers into `pytest.ini` (`markers = integration, lxc, e2e`).
4. Update CI to run unit tests always; gate integration/e2e behind explicit jobs.

This document should be treated as the canonical reference before adding or extending wrapper tests.

